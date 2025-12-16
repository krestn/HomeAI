import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def get_place_details(place_id: str) -> dict:
    """
    Fetch phone number and website for a place using Place Details API.
    """
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,website",
        "key": GOOGLE_API_KEY,
    }

    res = requests.get(PLACE_DETAILS_URL, params=params, timeout=10)
    res.raise_for_status()
    return res.json().get("result", {})


def find_local_services(service: str, city_state: str) -> list[dict]:
    """
    Find licensed home services near a given city/state.
    """
    params = {
        "query": f"{service} near {city_state}",
        "key": GOOGLE_API_KEY,
    }

    res = requests.get(TEXT_SEARCH_URL, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()

    results = []

    for place in data.get("results", [])[:5]:
        details = get_place_details(place["place_id"])

        results.append(
            {
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "rating": place.get("rating"),
                "phone": details.get("formatted_phone_number"),
                "website": details.get("website"),
            }
        )

    return results
