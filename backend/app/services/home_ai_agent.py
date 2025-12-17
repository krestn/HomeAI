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
    is_document_question,
)
from app.services.weather import get_chicago_weather_summary
from app.services.agent_memory import memory as agent_memory
from app.services.document_tools import (
    DOCUMENT_FUNCTION_DEFINITIONS,
    list_documents_for_agent,
    search_documents_for_agent,
    summarize_document_for_agent,
)


PENDING_PROPERTY_REQUESTS: dict[int, str] = {}
LAST_AGENT_REPLY: dict[int, str] = {}
PENDING_TASK_CONFIRMATIONS: dict[int, str] = {}

COMPLETION_KEYWORDS = [
    "complete",
    "completed",
    "finish",
    "finished",
    "done",
    "called",
    "emailed",
    "texted",
    "spoke",
    "talked",
    "reached out",
    "scheduled",
    "booked",
]

POSITIVE_CONFIRMATIONS = {
    "yes",
    "y",
    "yep",
    "yeah",
    "sure",
    "please do",
    "do it",
    "sounds good",
    "go ahead",
    "please",
}

TASK_STOPWORDS = {
    "call",
    "remind",
    "reminder",
    "email",
    "text",
    "follow",
    "task",
    "todo",
    "please",
    "need",
    "contact",
    "reach",
    "talk",
    "speak",
    "tomorrow",
    "today",
    "soon",
    "check",
    "look",
}

NEGATIVE_CONFIRMATIONS = {
    "no",
    "n",
    "not yet",
    "keep it",
    "leave it",
    "later",
    "still pending",
}

TASK_FUNCTION_DEFINITIONS = [
    {
        "name": "remember_user_task",
        "description": "Store a short follow-up task or reminder for the assistant.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "A concise summary of the follow-up action.",
                },
            },
            "required": ["description"],
        },
    },
    {
        "name": "complete_user_task",
        "description": "Mark a stored follow-up task as completed.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Specific task to remove. If omitted, clears all tasks.",
                }
            },
            "required": [],
        },
    },
]


# ----------------------------
# Tool functions
# ----------------------------


def get_home_value(address: str) -> str:
    property_details = get_property_details_by_address(address)
    return get_zestimate_from_data(property_details)


def get_local_services(service: str, city_state: str) -> list[dict]:
    return find_local_services(service, city_state)


def remember_user_task(*, user_id: int, description: str) -> dict:
    agent_memory.add_task(user_id, description)
    return {"status": "stored", "tasks": agent_memory.get_tasks(user_id)}


def complete_user_task(*, user_id: int, description: str | None = None) -> dict:
    agent_memory.complete_task(user_id, description)
    return {"status": "completed", "tasks": agent_memory.get_tasks(user_id)}


def execute_tool(func_name: str, args: dict, *, user_id: int) -> dict:
    if func_name == "get_home_value":
        return get_home_value(args["address"])
    if func_name == "get_local_services":
        return get_local_services(args["service"], args["city_state"])
    if func_name == "remember_user_task":
        return remember_user_task(user_id=user_id, description=args["description"])
    if func_name == "complete_user_task":
        return complete_user_task(user_id=user_id, description=args.get("description"))
    if func_name == "list_user_documents":
        return list_documents_for_agent(user_id)
    if func_name == "summarize_user_document":
        return summarize_document_for_agent(user_id, args["document_id"])
    if func_name == "search_user_documents":
        return search_documents_for_agent(user_id, args["query"])
    raise ValueError(f"Unsupported function {func_name}")


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
    tasks: list[dict] | None = None,
) -> dict:
    return {
        "reply": reply,
        "active_property": active_property,
        "available_properties": all_properties,
        "requires_property_selection": requires_property_selection,
        "tasks": tasks or [],
    }


def remember_agent_reply(user_id: int, reply: str) -> None:
    LAST_AGENT_REPLY[user_id] = reply


def find_task_match(message: str, tasks: list[dict]) -> str | None:
    text = (message or "").lower()
    if not text or not any(keyword in text for keyword in COMPLETION_KEYWORDS):
        return None

    best_task = None
    best_score = 0

    for task in tasks:
        if task.get("completed"):
            continue
        desc = (task.get("description") or "").strip()
        if not desc:
            continue
        desc_lower = desc.lower()
        if desc_lower and desc_lower in text:
            return desc

        tokens = [
            t
            for t in re.findall(r"[a-z0-9]+", desc_lower)
            if len(t) >= 3 and t not in TASK_STOPWORDS
        ]
        if not tokens:
            tokens = [desc_lower]

        matches = sum(1 for token in tokens if token and token in text)
        if matches > best_score:
            best_score = matches
            best_task = desc if matches > 0 else best_task

    return best_task if best_score > 0 else None


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
    message_text = (message or "").strip()
    message_lower = message_text.lower()

    # ----------------------------
    # Non-property questions path
    # ----------------------------
    current_tasks = agent_memory.get_tasks(user_id)

    pending_completion = PENDING_TASK_CONFIRMATIONS.get(user_id)
    if pending_completion and message_lower in POSITIVE_CONFIRMATIONS:
        complete_user_task(user_id=user_id, description=pending_completion)
        PENDING_TASK_CONFIRMATIONS.pop(user_id, None)
        reply_text = f"Got it. I've marked '{pending_completion}' as completed."
        remember_agent_reply(user_id, reply_text)
        return build_agent_response(
            reply=reply_text,
            active_property=None,
            all_properties=[],
            requires_property_selection=False,
            tasks=agent_memory.get_tasks(user_id),
        )

    if pending_completion and message_lower in NEGATIVE_CONFIRMATIONS:
        PENDING_TASK_CONFIRMATIONS.pop(user_id, None)
        reply_text = (
            "No problem. I'll keep that reminder active—let me know when it's done."
        )
        remember_agent_reply(user_id, reply_text)
        return build_agent_response(
            reply=reply_text,
            active_property=None,
            all_properties=[],
            requires_property_selection=False,
            tasks=agent_memory.get_tasks(user_id),
        )

    if not pending_completion:
        matched_task = find_task_match(message_text, current_tasks)
        if matched_task:
            PENDING_TASK_CONFIRMATIONS[user_id] = matched_task
            reply_text = (
                f"Great! Should I mark \"{matched_task}\" as completed?"
            )
            remember_agent_reply(user_id, reply_text)
            return build_agent_response(
                reply=reply_text,
                active_property=None,
                all_properties=[],
                requires_property_selection=False,
                tasks=current_tasks,
            )

    # ----------------------------
    # Non-property questions path
    # ----------------------------
    general_request = is_document_question(message_text) or (
        is_non_property_question(message_text) and not current_tasks
    )

    if general_request:
        PENDING_PROPERTY_REQUESTS.pop(user_id, None)
        if is_weather_question(message):
            reply_text = get_chicago_weather_summary()
            remember_agent_reply(user_id, reply_text)
            return build_agent_response(
                reply=reply_text,
                active_property=None,
                all_properties=[],
                requires_property_selection=False,
                tasks=agent_memory.get_tasks(user_id),
            )

        general_messages = [
            {"role": "system", "content": GENERAL_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": message_text},
        ]
        general_functions = TASK_FUNCTION_DEFINITIONS + DOCUMENT_FUNCTION_DEFINITIONS

        while True:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=general_messages,
                functions=general_functions,
                function_call="auto",
            )

            msg = response.choices[0].message
            if msg.function_call:
                func_name = msg.function_call.name
                args = json.loads(msg.function_call.arguments or "{}")
                result = execute_tool(func_name, args, user_id=user_id)
                general_messages.append(
                    {
                        "role": "function",
                        "name": func_name,
                        "content": json.dumps(result),
                    }
                )
                continue

            reply_text = msg.content or ""
            remember_agent_reply(user_id, reply_text)
            return build_agent_response(
                reply=reply_text,
                active_property=None,
                all_properties=[],
                requires_property_selection=False,
                tasks=agent_memory.get_tasks(user_id),
            )

    context = resolve_property_context(db, user_id)

    # ---- Hard error
    if "error" in context:
        reply_text = context["error"]
        remember_agent_reply(user_id, reply_text)
        return build_agent_response(
            reply=reply_text,
            active_property=None,
            all_properties=context.get("all_properties", []),
            requires_property_selection=False,
            tasks=agent_memory.get_tasks(user_id),
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
                reply_text = "Invalid property selection."
                remember_agent_reply(user_id, reply_text)
                return build_agent_response(
                    reply=reply_text,
                    active_property=None,
                    all_properties=all_properties,
                    requires_property_selection=True,
                    tasks=agent_memory.get_tasks(user_id),
                )

            active_property = selected

        inferred_property = resolve_property_from_message(message, context["options"])
        if inferred_property:
            active_property = inferred_property

        if not active_property:
            reply_text = build_multi_property_reply(message, context["options"])
            PENDING_PROPERTY_REQUESTS[user_id] = message
            remember_agent_reply(user_id, reply_text)
            return build_agent_response(
                reply=reply_text,
                active_property=None,
                all_properties=all_properties,
                requires_property_selection=True,
                tasks=agent_memory.get_tasks(user_id),
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

    active_tasks = agent_memory.get_tasks(user_id)
    if active_tasks:
        tasks_summary = "\n".join(
            f"- [{'x' if task.get('completed') else ' '}] {task.get('description')}"
            for task in active_tasks
        )
    else:
        tasks_summary = "- None."

    system_prompt = (
        HOME_AGENT_SYSTEM_PROMPT
        + "\n\nUser properties on file:\n"
        + properties_summary
        + "\n\nThe user is referring to this property:\n"
        + f"Property ID: {active_property['id']}\n"
        + f"Address: {property_address}\n"
        + f"City/State: {city_state}\n"
        + "Do not ask for the address unless the user explicitly changes properties."
        + "\n\nActive follow-up tasks:\n"
        + tasks_summary
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

    last_agent_note = LAST_AGENT_REPLY.get(user_id)
    if last_agent_note:
        agent_message = (
            "Previous assistant reply:\n"
            f"{last_agent_note}\n\n"
            "Latest user message:\n"
            f"{agent_message}"
        )

    base_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": agent_message},
    ]

    functions_payload = [
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
    ] + TASK_FUNCTION_DEFINITIONS + DOCUMENT_FUNCTION_DEFINITIONS

    MAX_TOOL_CALLS = 2
    tool_calls = 0
    messages = list(base_messages)

    while True:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=functions_payload,
            function_call="auto",
        )

        msg = response.choices[0].message

        if msg.function_call:
            if tool_calls >= MAX_TOOL_CALLS:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Please answer the user now using the information you already have. "
                            "Do not call another tool."
                        ),
                    }
                )
                continue

            func_name = msg.function_call.name
            args = json.loads(msg.function_call.arguments)

            if func_name == "get_home_value":
                args["address"] = property_address

            if func_name == "get_local_services":
                args["city_state"] = city_state

            result = execute_tool(func_name, args, user_id=user_id)

            messages.append(
                {
                    "role": "function",
                    "name": func_name,
                    "content": json.dumps(result),
                }
            )

            if func_name == "get_local_services":
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Use the service entries exactly as provided. "
                            "Do not add numbering or bullets—keep each entry separated by blank lines."
                        ),
                    }
                )

            tool_calls += 1

            if tool_calls < MAX_TOOL_CALLS:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "If another tool call would help answer the user, call it now. "
                            "Otherwise, respond directly."
                        ),
                    }
                )

            continue

        reply_text = msg.content or ""
        remember_agent_reply(user_id, reply_text)
        return build_agent_response(
            reply=reply_text,
            active_property=active_property,
            all_properties=all_properties,
            tasks=agent_memory.get_tasks(user_id),
        )
