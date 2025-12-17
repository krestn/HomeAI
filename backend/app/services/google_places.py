import os
from urllib.parse import urlparse

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


def _format_website(url: str | None) -> str:
    if not url:
        return "N/A"

    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.rstrip("/")

    if not host:
        return "N/A"

    if not host.startswith("www.") and "." in host:
        return f"www.{host}"

    return host


def find_local_services(service: str, city_state: str) -> list[str]:
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

    results: list[str] = []

    for place in data.get("results", [])[:5]:
        details = get_place_details(place["place_id"])

        name = place.get("name") or "Unknown business"
        address = place.get("formatted_address") or "Address unavailable"
        rating = place.get("rating") or "N/A"
        phone = details.get("formatted_phone_number") or "N/A"
        website = _format_website(details.get("website"))

        results.append(
            f"{name}\n"
            f"  - Address: {address}\n"
            f"  - Phone: {phone}\n"
            f"  - Website: {website}\n"
            f"  - Rating: {rating}"
        )

    return results
