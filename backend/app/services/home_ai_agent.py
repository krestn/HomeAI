from app.services.openai_client import client
from app.services.home_ai_agent_prompt import HOME_AGENT_SYSTEM_PROMPT
from app.services.openwebninja_zillow_api import (
    get_property_details_by_address,
    get_zestimate_from_data,
)
from app.services.google_places import find_local_services
from app.services.property_context import get_user_properties
from sqlalchemy.orm import Session
import json


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

    if len(properties) == 1:
        p = properties[0]
        return {
            "resolved": True,
            "property": {
                "id": p.id,
                "address": p.formatted_address,
                "city_state": f"{p.city}, {p.state}",
            },
        }

    return {
        "resolved": False,
        "options": [
            {
                "id": p.id,
                "address": p.formatted_address,
                "city_state": f"{p.city}, {p.state}",
            }
            for p in properties
        ],
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
) -> str:
    """
    User-aware Home AI Agent
    """

    context = resolve_property_context(db, user_id)

    # ---- Hard error
    if "error" in context:
        return context["error"]

    # ---- Multiple properties
    if not context["resolved"]:
        if not property_id:
            addresses = "\n".join(
                f"- ({p['id']}) {p['address']}" for p in context["options"]
            )
            return (
                "You have multiple properties. Which one are you referring to?\n\n"
                f"{addresses}"
            )

        selected = next(
            (p for p in context["options"] if p["id"] == property_id),
            None,
        )

        if not selected:
            return "Invalid property selection."

        property_address = selected["address"]
        city_state = selected["city_state"]

    # ---- Single property
    else:
        property_address = context["property"]["address"]
        city_state = context["property"]["city_state"]

    # ----------------------------
    # Inject property context
    # ----------------------------

    system_prompt = (
        HOME_AGENT_SYSTEM_PROMPT
        + "\n\nThe user is referring to this property:\n"
        + f"Address: {property_address}\n"
        + f"City/State: {city_state}\n"
        + "Do not ask for the address unless the user explicitly changes properties."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
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

        follow_up = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
                {
                    "role": "function",
                    "name": func_name,
                    "content": json.dumps(result),
                },
            ],
        )

        return follow_up.choices[0].message.content

    return msg.content
