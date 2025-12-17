from app.services.openai_client import client
from app.services.home_ai_agent_prompt import (
    HOME_AGENT_SYSTEM_PROMPT,
    GENERAL_AGENT_SYSTEM_PROMPT,
)

import re
from app.services.openwebninja_zillow_api import (
    get_property_details_by_address,
    get_zestimate_from_data,
)
from app.services.google_places import find_local_services
from app.services.property_context import get_user_properties, serialize_property
from sqlalchemy.orm import Session
import json
from app.services.non_property_intent import (
    is_non_property_question,
    is_weather_question,
)
from app.services.weather import get_chicago_weather_summary


PENDING_PROPERTY_REQUESTS: dict[int, str] = {}


# ----------------------------
# Tool functions
# ----------------------------


def get_home_value(address: str) -> str:
    property_details = get_property_details_by_address(address)
    return get_zestimate_from_data(property_details)


def get_local_services(service: str, city_state: str) -> list[dict]:
    return find_local_services(service, city_state)


FUNCTION_REGISTRY = {
    "get_home_value": lambda args: get_home_value(args["address"]),
    "get_local_services": lambda args: get_local_services(
        args["service"], args["city_state"]
    ),
}


def format_property_summary(properties: list[dict]) -> str:
    return "\n".join(f"{p['address']} - {p['city_state']}" for p in properties)


def resolve_property_from_message(message: str, properties: list[dict]) -> dict | None:
    """
    Attempt to infer which property the user referenced in free-form text.
    Supports matching by property ID (number) or address/city strings.
    """
    text = message.lower()
    tokens = re.findall(r"[a-z0-9]+", text)

    # Look for explicit numeric IDs in the message
    id_tokens = re.findall(r"\d+", message)
    for token in id_tokens:
        for property_obj in properties:
            if str(property_obj["id"]) == token:
                return property_obj

    # Fall back to address/city substring matching
    for property_obj in properties:
        address_text = property_obj["address"].lower()
        city_state_text = property_obj["city_state"].lower()

        if address_text in text or text in address_text:
            return property_obj
        if city_state_text in text or text in city_state_text:
            return property_obj

        for token in tokens:
            if len(token) < 3:
                continue
            if token in address_text or token in city_state_text:
                return property_obj

    return None


def build_agent_response(
    *,
    reply: str,
    active_property: dict | None,
    all_properties: list[dict],
    requires_property_selection: bool = False,
) -> dict:
    return {
        "reply": reply,
        "active_property": active_property,
        "available_properties": all_properties,
        "requires_property_selection": requires_property_selection,
    }


MULTI_PROPERTY_PROMPT = """
You are HomeAI, an empathetic homeowner assistant.
The user is asking something that requires knowing which of their properties is affected.
Respond in 2 short sentences.
- Acknowledge the user's situation using a warm, professional tone.
- Offer help relevant to the user's message.
- Remind them they have multiple properties and ask which one applies, but do not list the properties.
"""


def build_multi_property_reply(message: str, property_options: list[dict]) -> str:
    property_list = "\n".join(
        f"- {p['address']}, {p['city_state']}" for p in property_options
    )
    if not property_list:
        property_list = "- No properties available."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": MULTI_PROPERTY_PROMPT.strip()},
                {"role": "user", "content": message},
            ],
            max_tokens=120,
        )
        intro = response.choices[0].message.content.strip()
    except Exception:
        intro = (
            "I'm here to help and want to make sure I'm looking at the right home."
            " Which property should we focus on?"
        )

    return f"{intro}\n\nHere are the homes I have on file:\n{property_list}"


# ----------------------------
# Property context resolution
# ----------------------------


def resolve_property_context(db: Session, user_id: int) -> dict:
    """
    Always returns one of:
    - { "error": str }
    - { "resolved": True, "property": {...} }
    - { "resolved": False, "options": [...] }
    """
    properties = get_user_properties(db, user_id)

    if not properties:
        return {
            "error": "No property found for your account. Please add a property first."
        }

    serialized_properties = [serialize_property(p) for p in properties]

    if len(serialized_properties) == 1:
        return {
            "resolved": True,
            "property": serialized_properties[0],
            "all_properties": serialized_properties,
        }

    return {
        "resolved": False,
        "options": serialized_properties,
        "all_properties": serialized_properties,
    }


# ----------------------------
# Main agent runner
# ----------------------------


def run_home_agent(
    *,
    db: Session,
    user_id: int,
    message: str,
    property_id: int | None = None,
) -> dict:
    """
    User-aware Home AI Agent
    """

    # ----------------------------
    # Non-property questions path
    # ----------------------------
    if is_non_property_question(message):
        PENDING_PROPERTY_REQUESTS.pop(user_id, None)
        if is_weather_question(message):
            return build_agent_response(
                reply=get_chicago_weather_summary(),
                active_property=None,
                all_properties=[],
                requires_property_selection=False,
            )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": GENERAL_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            # No property tools for general questions
        )

        reply_text = response.choices[0].message.content
        return build_agent_response(
            reply=reply_text,
            active_property=None,
            all_properties=[],
            requires_property_selection=False,
        )

    context = resolve_property_context(db, user_id)

    # ---- Hard error
    if "error" in context:
        return build_agent_response(
            reply=context["error"],
            active_property=None,
            all_properties=context.get("all_properties", []),
            requires_property_selection=False,
        )

    all_properties = context.get("all_properties", [])
    active_property: dict | None = None

    # ---- Multiple properties
    if not context["resolved"]:
        if property_id is not None:
            selected = next(
                (p for p in context["options"] if p["id"] == property_id),
                None,
            )

            if not selected:
                return build_agent_response(
                    reply="Invalid property selection.",
                    active_property=None,
                    all_properties=all_properties,
                    requires_property_selection=True,
                )

            active_property = selected

        inferred_property = resolve_property_from_message(message, context["options"])
        if inferred_property:
            active_property = inferred_property

        if not active_property:
            reply_text = build_multi_property_reply(message, context["options"])
            PENDING_PROPERTY_REQUESTS[user_id] = message
            return build_agent_response(
                reply=reply_text,
                active_property=None,
                all_properties=all_properties,
                requires_property_selection=True,
            )

    # ---- Single property
    else:
        active_property = context["property"]

    pending_property_message = PENDING_PROPERTY_REQUESTS.pop(user_id, None)

    property_address = active_property["address"]
    city_state = active_property["city_state"]

    # ----------------------------
    # Inject property context
    # ----------------------------

    properties_summary = format_property_summary(all_properties)
    if not properties_summary:
        properties_summary = "- No properties available."

    system_prompt = (
        HOME_AGENT_SYSTEM_PROMPT
        + "\n\nUser properties on file:\n"
        + properties_summary
        + "\n\nThe user is referring to this property:\n"
        + f"Property ID: {active_property['id']}\n"
        + f"Address: {property_address}\n"
        + f"City/State: {city_state}\n"
        + "Do not ask for the address unless the user explicitly changes properties."
    )

    agent_message = message
    if pending_property_message:
        selection_note = (
            "The user clarified the affected property is "
            f"{property_address}, {city_state}."
        )
        extra = message.strip()
        if extra:
            agent_message = (
                f"{pending_property_message}\n\n{selection_note}\n\n"
                f"User follow-up: {extra}"
            )
        else:
            agent_message = f"{pending_property_message}\n\n{selection_note}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": agent_message},
        ],
        functions=[
            {
                "name": "get_home_value",
                "description": "Get an estimated home value for the user's current property.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string"},
                    },
                    "required": ["address"],
                },
            },
            {
                "name": "get_local_services",
                "description": "Find local services near the user's property.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "city_state": {"type": "string"},
                    },
                    "required": ["service", "city_state"],
                },
            },
        ],
        function_call="auto",
    )

    msg = response.choices[0].message

    # ----------------------------
    # Tool execution
    # ----------------------------

    if msg.function_call:
        func_name = msg.function_call.name
        args = json.loads(msg.function_call.arguments)

        # Enforce resolved property context
        if func_name == "get_home_value":
            args["address"] = property_address

        if func_name == "get_local_services":
            args["city_state"] = city_state

        result = FUNCTION_REGISTRY[func_name](args)

        follow_up_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": agent_message},
            {
                "role": "function",
                "name": func_name,
                "content": json.dumps(result),
            },
        ]

        if func_name == "get_local_services":
            follow_up_messages.append(
                {
                    "role": "user",
                    "content": (
                        "Use the service entries exactly as provided. "
                        "Do not add numbering or bullets—keep each entry separated by blank lines."
                    ),
                }
            )

        follow_up = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=follow_up_messages,
        )

        reply_text = follow_up.choices[0].message.content
        return build_agent_response(
            reply=reply_text,
            active_property=active_property,
            all_properties=all_properties,
        )

    reply_text = msg.content
    return build_agent_response(
        reply=reply_text,
        active_property=active_property,
        all_properties=all_properties,
    )
