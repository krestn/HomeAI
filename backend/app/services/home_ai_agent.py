from app.services.openai_client import client
from app.services.home_ai_agent_prompt import HOME_AGENT_SYSTEM_PROMPT
from app.services.openwebninja_zillow_api import (
    get_property_details_by_address,
    get_zestimate_from_data,
)
from app.services.google_places import find_local_services
import json

CURRENT_PROPERTY_ADDRESSES = (
    [
        "1600 Zenobia Street, Denver, CO 80204",
        "3545 Lincoln Place Dr, Des Moines, IA 50312",
        "129 Vernon Dr. Bolingbrook, IL",
    ],
)


def get_home_value(address: str) -> str:
    try:
        property_details = get_property_details_by_address(address)
        return get_zestimate_from_data(property_details)
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }


def get_local_services(service: str, city_state: str) -> list[dict]:
    try:
        return find_local_services(service, city_state)
    except Exception as e:
        return {"error": str(e)}


FUNCTION_REGISTRY = {
    "get_home_value": lambda args: get_home_value(args["address"]),
    "get_local_services": lambda args: get_local_services(
        args["service"], args["city_state"]
    ),
}


def run_home_agent(message: str) -> str:
    """
    Sends a user message to OpenAI and optionally calls the get_home_value function
    if the model determines it should.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": HOME_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        functions=[
            {
                "name": "get_home_value",
                "description": "Get an estimated home value for a specific property address.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Full street address of the home",
                        }
                    },
                    "required": ["address"],
                },
            },
            {
                "name": "get_local_services",
                "description": "Find local services near a city and state.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "Liscenced service, e.g. 'Plumber', 'Electrician', 'Roofer', 'Appraiser'",
                        },
                        "city_state": {
                            "type": "string",
                            "description": "City and state, e.g. 'Austin, TX'",
                        },
                    },
                    "required": ["service", "city_state"],
                },
            },
        ],
        function_call="auto",
    )

    message_data = response.choices[0].message

    if message_data.function_call:
        func_name = message_data.function_call.name
        arguments = json.loads(message_data.function_call.arguments)

        handler = FUNCTION_REGISTRY.get(func_name)
        if not handler:
            result = {"error": f"Unknown function {func_name}"}
        else:
            result = handler(arguments)

        follow_up = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": HOME_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
                {
                    "role": "function",
                    "name": func_name,
                    "content": json.dumps(result),
                },
            ],
        )

        return follow_up.choices[0].message.content

    return message_data.content
