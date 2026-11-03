"""Agent loop: model -> tool -> model."""
import json
import time

from openai import OpenAI

from agent.config import Config
from agent.logger import RunLogger
from agent.tools import TOOLS, get_calendar_day

SYSTEM_PROMPT = (
    "You are a calendar assistant. To answer questions about appointments, "
    "call the calendar tool for each requested date. Never invent appointments, "
    "times or locations. "
    "If the tool reports found=false (no data for this day), say that the calendar "
    "has no data for that day; do not claim there are no appointments. "
    "If the tool returns an empty list of events, say there are no appointments that day. "
    "Answer in the language of the user's question, as plain text without Markdown."
)

# Safety limit: normally one tool round is enough (model -> tool -> model).
MAX_ROUNDS = 5


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
    if name == "get_calendar_day":
        return get_calendar_day(cfg.data_base_url, args.get("date"))
    return {"error": f"unknown tool: {name}"}


def run_agent(cfg: Config, logger: RunLogger, task: str) -> str:
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(MAX_ROUNDS):
        start = time.perf_counter()
        response = client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
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
            logger.log("tool_call", tool=name, args=args, duration_ms=model_ms)

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