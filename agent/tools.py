"""Calendar tool: the function the model can call, plus its description for the model."""
import datetime

import requests

TIMEOUT_SECONDS = 10

# This description is the only thing the model sees of the tool.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_day",
            "description": (
                "Returns all calendar appointments of one single day "
                "(title, start time, end time, location, all-day flag). "
                "Use it whenever the user asks what is scheduled on a specific date. "
                "Call it once per day; if the user asks about several days, call it for each day."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": (
                            "The day in the format YYYY-MM-DD, e.g. 2026-10-29. "
                            "Convert other formats such as 29.10.2026 yourself."
                        ),
                    }
                },
                "required": ["date"],
            },
        },
    }
]

# helper function
def _valid_date(date) -> bool:
    # Strict check: fromisoformat alone also accepts forms like 20261029.
    try:
        return datetime.date.fromisoformat(date).isoformat() == date
    except (TypeError, ValueError):
        return False


def _fetch_json(url: str, meta: dict) -> dict:
    """GET a JSON file. Always returns a dict, never raises. 404 = no data."""
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        return {**meta, "error": f"request failed: {exc}"}
    if response.status_code == 404:
        return {**meta, "found": False,
                "message": "No data for this request. Do not estimate or guess values."}
    if response.status_code != 200:
        return {**meta, "error": f"unexpected HTTP status {response.status_code}"}
    try:
        return response.json()
    except ValueError:
        return {**meta, "error": "response is not valid JSON"}

# tool call functions
def get_calendar_day(data_base_url: str, date: str) -> dict:
    """Fetch the appointments of one day. Always returns a dict and never raises."""
    meta = {"date": date}
    if not _valid_date(date):
        return {**meta, "error": "invalid date, expected format YYYY-MM-DD"}
    url = f"{data_base_url}/calendar/{date}.json"
    return _fetch_json(url, meta)