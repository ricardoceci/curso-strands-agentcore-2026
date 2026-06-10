"""
Flight booking simulation tool.

Simulates confirming a flight offer previously returned by `search_flights`.
No real charge is made; the booking is recorded in memory and a fake
confirmation number is returned so the agent can report back to the user.
"""

import random
import string
from datetime import datetime, timezone

from strands import tool

# In-memory store of simulated bookings (keyed by confirmation number).
_BOOKINGS: dict[str, dict] = {}


def _generate_confirmation() -> str:
    """Return a random 8-character alphanumeric confirmation code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=8))


# 2. ``get_employee_policy`` has confirmed that the cabin class and amount
     #  are within the employee's allowed limits.
@tool
def book_flight(
    offer_id: str,
    employee_id: str,

    total_amount: float,
    currency: str,
    cabin_class: str,
) -> dict:
    """Booking a flight offer on behalf of an employee.

    Call this tool ONLY after:
    1. ``search_flights`` has returned the offer the user wants to book.
   

    A confirmation number is returned that the agent can present to the user.

    Args:
        offer_id: The ``offer_id`` returned by ``search_flights``.
        employee_id: The employee ID who is making the booking (e.g. "EMP001").
        total_amount: Total fare amount to be charged (used for audit trail).
        currency: Currency code of the fare (e.g. "USD", "ARS").
        cabin_class: Cabin class being booked (e.g. "economy", "business").

    Returns:
        A dict with:
        - ``confirmation_number``: unique booking reference.
        - ``status``: "confirmed" on success.
        - ``offer_id``: echoed back for traceability.
        - ``employee_id``: echoed back.
        - ``total_amount``: echoed back.
        - ``currency``: echoed back.
        - ``cabin_class``: echoed back.
        - ``booked_at``: ISO-8601 UTC timestamp of the simulated booking.
        - ``error``: present only if the booking could not be completed.
    """
    if not offer_id or not employee_id:
        return {
            "error": "missing_required_fields",
            "message": "offer_id, employee_id",
        }

    confirmation = _generate_confirmation()
    booked_at = datetime.now(timezone.utc).isoformat()

    record = {
        "confirmation_number": confirmation,
        "status": "confirmed",
        "offer_id": offer_id,
        "employee_id": employee_id,
       
        "total_amount": total_amount,
        "currency": currency,
        "cabin_class": cabin_class,
        "booked_at": booked_at,
    }

    _BOOKINGS[confirmation] = record
    return record
