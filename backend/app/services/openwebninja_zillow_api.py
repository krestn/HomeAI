import os
from dotenv import load_dotenv
import requests

load_dotenv()

OPENWEBNINJA_API_KEY = os.getenv("OPENWEBNINJA_API_KEY")
OPENWEBNINJA_ENDPOINT = (
    "https://api.openwebninja.com/realtime-zillow-data/property-details-address"
)


def get_property_details_by_address(address: str) -> str:

    headers = {"x-api-key": OPENWEBNINJA_API_KEY, "Accept": "application/json"}
    params = {"address": address}

    response = requests.get(OPENWEBNINJA_ENDPOINT, params=params, headers=headers)
    response.raise_for_status()
    data = response.json().get("data", {})

    # Return the full JSON if the API returns details
    if data:
        return data
    else:
        raise ValueError("No property details found for this address")


def get_zestimate_from_data(property_data: dict) -> str:
    """
    Extract the Zestimate (estimated home value) from the full property details.
    """
    zestimate = property_data.get("zestimate")

    return str(zestimate) if zestimate else "Zestimate not found"
