"""Agent loop: model -> tool -> model."""
import json
import time

from openai import OpenAI

from agent.config import Config
from agent.logger import RunLogger
from agent.tools import TOOLS, get_calendar_day, get_weather, get_train_connections, get_context

SYSTEM_PROMPT = (
    "You are an assistant for calendar, weather and train connections. Get every fact from the "
    "tools; never use your own knowledge for appointments, weather, trains, times or prices. "
    "If a tool returns found=false, there is no data for exactly that request (day, place or "
    "route): say so for that part and do not estimate or guess. If a tool returns an error, "
    "say that the lookup failed technically. If you can only answer part of a question, answer "
    "that part and say what is missing. If the user names no starting point, use the home city "
    "from get_context. For a trip on the current day, ignore connections that have already "
    "departed (compare with now from get_context). State rain probability as a percentage and "
    "give a short recommendation. If the calendar returns an empty list of events, say there "
    "are no appointments that day. Answer in the language of the question, as plain text "
    "without Markdown."
)

# Safety limit: normally one tool round is enough (model -> tool -> model).
MAX_ROUNDS = 10

HANDLERS = {
    "get_calendar_day": get_calendar_day,
    "get_weather": get_weather,
    "get_train_connections": get_train_connections,
    "get_context": get_context,
}


def _elapsed_ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


def _parse_arguments(raw: str) -> dict:
    """The model sends arguments as a JSON string: parse it, never crash."""
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return args if isinstance(args, dict) else {}


def _execute_tool(cfg: Config, name: str, args: dict) -> dict:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return handler(cfg.data_base_url, **args)
    except TypeError as exc:  # model sent missing or unexpected arguments
        return {"error": f"invalid arguments: {exc}"}

MAX_MODEL_RETRIES = 3

def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (OpenAI.RateLimitError, OpenAI.APITimeoutError, OpenAI.APIConnectionError)):
        return True
    if isinstance(exc, OpenAI.BadRequestError):
        text = str(exc)
        return "tool_use_failed" in text or "Parsing failed" in text
    return False


def _call_model(client, cfg, messages, logger, step):
    for attempt in range(1, MAX_MODEL_RETRIES + 1):
        start = time.perf_counter()
        try:
            return client.chat.completions.create(
                model=cfg.model, messages=messages,
                tools=TOOLS, tool_choice="auto",
            )
        except Exception as exc:
            retryable = _is_retryable(exc)
            logger.log(
                "error", ok=False, duration_ms=_elapsed_ms(start),
                step=step, attempt=attempt, retryable=retryable,
                error=f"{type(exc).__name__}: {str(exc)[:500]}",
            )
            if not retryable or attempt == MAX_MODEL_RETRIES:
                raise
            time.sleep(2 * attempt)  # 2 s, 4 s, ...

def run_agent(cfg: Config, logger: RunLogger, task: str) -> str:
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for step in range(1, MAX_ROUNDS+1):
        start = time.perf_counter()
        # response = client.chat.completions.create(
        #    model=cfg.model,
        #    messages=messages,
        #    tools=TOOLS,
        #    tool_choice="auto",
        #)

        response = _call_model(client, cfg, messages, logger, step)

        model_ms = _elapsed_ms(start)
        message = response.choices[0].message

        # No tool requested: this is the final answer.
        if not message.tool_calls:
            logger.log("final", duration_ms=model_ms, content=message.content)
            return message.content or ""

        # Echo the assistant message (with its tool calls) back to the model.
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            }
        )

        # The model may request several calls at once: handle every one.
        for call in message.tool_calls:
            name = call.function.name
            args = _parse_arguments(call.function.arguments)
            # duration_ms here is the model call that produced this request.
            logger.log("tool_call", tool=name, args=args, duration_ms=model_ms, step=step)

            tool_start = time.perf_counter()
            result = _execute_tool(cfg, name, args)
            # 404 ("no data") is a valid result; only technical errors have an "error" key.
            logger.log(
                "tool_result",
                tool=name,
                args=args,
                ok="error" not in result,
                duration_ms=_elapsed_ms(tool_start),
                result=result,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,  # must match the id of the request
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError(f"No final answer after {MAX_ROUNDS} rounds")