from app.services.openai_client import client
from app.services.home_ai_agent_prompt import HOME_AGENT_SYSTEM_PROMPT
from app.services.openwebninja_zillow_api import (
    get_property_details_by_address,
    get_zestimate_from_data,
)
import json


def get_home_value(address: str) -> str:
    try:
        property_details = get_property_details_by_address(address)
        return get_zestimate_from_data(property_details)
    except Exception as e:
        return f"Error fetching value: {str(e)}"


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
                "description": "Get the estimated value of a home based on its address using OpenWeb Ninja API",
                "parameters": {
                    "type": "object",
                    "properties": {"address": {"type": "string"}},
                    "required": ["address"],
                },
            }
        ],
        function_call="auto",
    )

    message_data = response.choices[0].message

    # Check if the model decided to call a function
    if message_data.function_call is not None:
        func_name = message_data.function_call.name
        arguments = json.loads(message_data.function_call.arguments)

        if func_name == "get_home_value":
            home_value = get_home_value(arguments["address"])

            # Feed the function result back to the model for a friendly response
            follow_up = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": HOME_AGENT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                    {
                        "role": "function",
                        "name": func_name,
                        "content": json.dumps({"value": home_value}),
                    },
                ],
            )
            return follow_up.choices[0].message.content

    # Otherwise return the model's normal response
    return message_data.content
