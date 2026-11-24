"""toolbox: the functions the model can call, plus their descriptions for the model."""
import datetime
from urllib.parse import quote
import requests

TIMEOUT_SECONDS = 10
_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})

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
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Returns the weather forecast for one city on one day: "
                "temperature in °C, condition, rain probability as a fraction between 0 and 1 (0.2 = 20 %), "
                "wind in km/h. Use it for questions about weather, rain or umbrellas. "
                "Data exists only for some days and cities; found=false means there is no data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "City key, lowercase with umlauts written out, "
                            "e.g. 'ulm' or 'muenchen' (for München/Munich)."
                        ),
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "The day in the format YYYY-MM-DD, e.g. 2026-10-29. "
                            "Convert other formats such as 29.10.2026 yourself."
                        ),
                    }
                },
                "required": ["city", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_train_connections",
            "description": (
                "Returns the train connections between two cities on one day: "
                "departure, arrival, changes, train name, price in EUR. "
                "Use it for questions about getting from one city to another. "
                "origin is where the trip starts. Data exists only for some routes and days; "
                "found=false means there is no data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "City key, lowercase with umlauts written out, "
                            "e.g. 'ulm' or 'muenchen' (for München/Munich)."
                        ),
                    },
                    "destination": {
                        "type": "string",
                        "description": (
                            "City key, lowercase with umlauts written out, "
                            "e.g. 'ulm' or 'muenchen' (for München/Munich)."
                        ),
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "The day in the format YYYY-MM-DD, e.g. 2026-10-29. "
                            "Convert other formats such as 29.10.2026 yourself."
                        ),
                    }
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_context",
            "description": (
                "Returns the user's current date and time (now), their home city (home), "
                "quiet hours and hints. Call it when you need the user's starting point "
                "(e.g. 'How do I get to Munich?' without a start city) or the current time "
                "(e.g. 'today', 'next train')."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
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


def _city_key(city) -> str:
    # "München" -> "muenchen"; the model may send any spelling.
    return str(city).strip().lower().translate(_UMLAUTS)


# tool call functions
def get_calendar_day(data_base_url: str, date: str) -> dict:
    """Fetch the appointments of one day. Always returns a dict and never raises."""
    meta = {"date": date}
    if not _valid_date(date):
        return {**meta, "error": "invalid date, expected format YYYY-MM-DD"}
    url = f"{data_base_url}/calendar/{date}.json"
    return _fetch_json(url, meta)


def get_weather(data_base_url: str, city: str, date: str) -> dict:
    meta = {"city": city, "date": date}
    if not _valid_date(date):
        return {**meta, "error": "invalid date, expected format YYYY-MM-DD"}
    url = f"{data_base_url}/weather/{quote(_city_key(city), safe='')}/{date}.json"
    return _fetch_json(url, meta)


def get_train_connections(data_base_url: str, origin: str, destination: str, date: str) -> dict:
    meta = {"origin": origin, "destination": destination, "date": date}
    if not _valid_date(date):
        return {**meta, "error": "invalid date, expected format YYYY-MM-DD"}
    o, d = quote(_city_key(origin), safe=""), quote(_city_key(destination), safe="")
    return _fetch_json(f"{data_base_url}/transit/{o}/{d}/{date}.json", meta)


def get_context(data_base_url: str) -> dict:
    return _fetch_json(f"{data_base_url}/context.json", {})