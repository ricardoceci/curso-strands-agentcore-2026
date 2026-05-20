"""
Local logging tool. Writes a structured record per search to a JSONL file.

Used in Class 1 to demonstrate a tool that performs a side effect (writes
to disk) instead of just returning data. From Class 4 onwards we replace
this with DynamoDB persistence.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from strands import tool

LOG_FILE_PATH = Path(__file__).parent.parent / "search_log.jsonl"


@tool
def save_search_log(query: str, result_summary: str) -> dict:
    """Append a search record to the local search log file.

    Use this tool every time you perform a flight search, to keep an audit
    trail of what was searched and what was returned. The log is one JSON
    object per line.

    Args:
        query: The original natural-language query from the user.
        result_summary: A short description of what was found (e.g.
            "Found 3 offers, cheapest USD 412 with American Airlines").

    Returns:
        A dict with `status` and `log_path`.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "result_summary": result_summary,
    }
    with LOG_FILE_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"status": "logged", "log_path": str(LOG_FILE_PATH)}
