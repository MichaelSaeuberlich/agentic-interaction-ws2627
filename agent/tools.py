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


def get_calendar_day(data_base_url: str, date: str) -> dict:
    """Fetch the appointments of one day. Always returns a dict and never raises."""
    # Strict check: fromisoformat alone also accepts forms like 20261029.
    try:
        parsed = datetime.date.fromisoformat(date)
    except (TypeError, ValueError):
        return {"date": date, "error": "invalid date, expected format YYYY-MM-DD"}
    if parsed.isoformat() != date:
        return {"date": date, "error": "invalid date, expected format YYYY-MM-DD"}

    url = f"{data_base_url}/calendar/{date}.json"
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        return {"date": date, "error": f"request failed: {exc}"}

    # 404 means "no data for this day": a normal result, not an error.
    if response.status_code == 404:
        return {"date": date, "found": False, "message": "No data for this day"}
    if response.status_code != 200:
        return {"date": date, "error": f"unexpected HTTP status {response.status_code}"}

    try:
        return response.json()
    except ValueError:
        return {"date": date, "error": "response is not valid JSON"}