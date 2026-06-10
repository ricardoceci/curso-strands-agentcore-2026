"""
Flight search tool backed by the Duffel sandbox API.

The Duffel flow is two-step: we create an offer request, and the response
already includes the cheapest offers. We expose a single `search_flights`
function so the agent doesn't need to know the underlying flow.

Docs: https://duffel.com/docs/guides/getting-started-with-flights
"""

import os
from typing import Optional
from dotenv import load_dotenv

import requests
from strands import tool

load_dotenv()

DUFFEL_API_BASE_URL = "https://api.duffel.com"
DUFFEL_API_VERSION = "v2"


def _duffel_headers() -> dict:
    """Build the headers required by every Duffel request."""
    api_key = os.environ.get("DUFFEL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DUFFEL_API_KEY is not set. Add it to your .env file."
        )
    return {
        "Authorization": f"Bearer {api_key}",
        "Duffel-Version": DUFFEL_API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


@tool
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    cabin_class: str = "economy",
    adults: int = 1,
    max_results: int = 5,
) -> dict:
    """Search for one-way flights using the Duffel sandbox API.

    Use this tool whenever the user asks to find, search, or compare flights.
    The tool returns the cheapest offers ordered by total price.

    Args:
        origin: Origin airport IATA code (3 letters, e.g. "EZE", "JFK").
        destination: Destination airport IATA code (3 letters, e.g. "MIA").
        departure_date: Departure date in YYYY-MM-DD format.
        cabin_class: One of "economy", "premium_economy", "business", "first".
        adults: Number of adult passengers (default 1).
        max_results: Maximum number of offers to return (default 5).

    Returns:
        A dict with `offers`: a list of flight options, each containing
        `offer_id`, `total_amount`, `currency`, `airline`, `departure_time`,
        `arrival_time` and `duration`.
    """
    payload = {
        "data": {
            "slices": [
                {
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_date": departure_date,
                }
            ],
            "passengers": [{"type": "adult"} for _ in range(adults)],
            "cabin_class": cabin_class,
        }
    }

    # `return_offers=true` makes Duffel include offers in the response,
    # avoiding a second round-trip call.
    response = requests.post(
        f"{DUFFEL_API_BASE_URL}/air/offer_requests",
        headers=_duffel_headers(),
        params={"return_offers": "true"},
        json=payload,
        timeout=30,
    )

    if response.status_code >= 400:
        return {
            "error": "duffel_request_failed",
            "status_code": response.status_code,
            "details": response.text[:500],
        }

    data = response.json().get("data", {})
    offers = data.get("offers", [])

    # Sort by total amount ascending and trim
    offers_sorted = sorted(offers, key=lambda o: float(o.get("total_amount", 1e9)))
    trimmed = offers_sorted[:max_results]

    # Map Duffel's verbose schema into a model-friendly shape
    return {
        "offer_request_id": data.get("id"),
        "offers": [_simplify_offer(o) for o in trimmed],
    }


def _simplify_offer(offer: dict) -> dict:
    """Reduce a Duffel offer to the minimum fields the agent needs."""
    first_slice = offer.get("slices", [{}])[0]
    segments = first_slice.get("segments", [])
    first_segment: Optional[dict] = segments[0] if segments else None
    last_segment: Optional[dict] = segments[-1] if segments else None

    return {
        "offer_id": offer.get("id"),
        "total_amount": offer.get("total_amount"),
        "currency": offer.get("total_currency"),
        "airline": offer.get("owner", {}).get("name"),
        "departure_time": first_segment.get("departing_at") if first_segment else None,
        "arrival_time": last_segment.get("arriving_at") if last_segment else None,
        "duration": first_slice.get("duration"),
        "stops": max(0, len(segments) - 1),
    }
