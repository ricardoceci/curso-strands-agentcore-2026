"""
Employee travel policy tool.

Returns the travel policy for a given employee ID so the agent can decide
whether a booking is allowed before proceeding.
"""

from strands import tool

# Hardcoded policy table. Replace with a database call in production.
_POLICIES: dict[str, dict] = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "Ana García",
        "budget_per_booking": 1500.00,
        "budget_per_month": 4000.00,
        "allowed_cabin_classes": ["economy", "premium_economy"],
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Carlos López",
        "budget_per_booking": 3000.00,
        "budget_per_month": 8000.00,
        "allowed_cabin_classes": ["economy", "premium_economy", "business"],
    },
    "EMP003": {
        "employee_id": "EMP003",
        "name": "María Fernández",
        "budget_per_booking": 800.00,
        "budget_per_month": 2000.00,
        "allowed_cabin_classes": ["economy"],
    },
    "EMP004": {
        "employee_id": "EMP004",
        "name": "Roberto Silva",
        "budget_per_booking": 5000.00,
        "budget_per_month": 15000.00,
        "allowed_cabin_classes": ["economy", "premium_economy", "business"],
    },
}

# Use this tool before booking any flight to verify whether the employee is
#    allowed to travel in the requested cabin class and whether the fare is
 #   within their budget limits. The agent should check the policy first and
  #  only proceed with a booking if the offer satisfies all constraints.

@tool
def get_employee_policy(employee_id: str) -> dict:
    """Retrieve the travel policy for a given employee.

   

    Args:
        employee_id: The unique employee identifier (e.g. "EMP001").

    Returns:
        A dict with the employee's travel policy:
        - ``employee_id``: the requested ID.
        - ``name``: employee's full name.
        - ``budget_per_booking``: maximum amount (USD) allowed per single booking.
        - ``budget_per_month``: maximum total amount (USD) allowed in a calendar month.
        - ``allowed_cabin_classes``: list of cabin classes the employee may book.
          Possible values: "economy", "premium_economy", "business".
        - ``error``: present only when the employee ID is not found.
    """
    policy = _POLICIES.get(employee_id.upper())
    if policy is None:
        return {
            "error": "employee_not_found",
            "employee_id": employee_id,
            "message": f"No policy found for employee '{employee_id}'. Verify the ID and try again.",
        }
    return policy
