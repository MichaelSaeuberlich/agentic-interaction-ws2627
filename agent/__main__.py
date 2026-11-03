"""Entry point: python -m agent "your question"."""
import sys

from agent.config import load_config
from agent.logger import RunLogger
from agent.loop import run_agent


def main() -> int:
    task = " ".join(sys.argv[1:]).strip()
    if not task:
        print('Usage: python -m agent "your question"', file=sys.stderr)
        return 2

    cfg = load_config()
    logger = RunLogger(cfg.model)
    logger.log("user_task", content=task)
    try:
        answer = run_agent(cfg, logger, task)
    except Exception as exc:
        logger.log("error", ok=False, error=f"{type(exc).__name__}: {exc}")
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())