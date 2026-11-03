"""Run log: one JSONL file per run, written to logs/ in the repository root."""
import json
import uuid
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


class RunLogger:
    def __init__(self, model: str) -> None:
        self.run_id = str(uuid.uuid4())
        self.model = model
        LOG_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # Timestamp plus the start of the run_id: unique file name per run.
        self.path = LOG_DIR / f"{stamp}_{self.run_id[:8]}.jsonl"

    def log(self, event: str, *, tool=None, args=None, ok=True, duration_ms=None, **extra) -> None:
        """Append one JSON object (one line) with all required fields."""
        record = {
            "ts": datetime.now().astimezone().isoformat(),  # ISO 8601 with time zone
            "run_id": self.run_id,
            "event": event,  # user_task | tool_call | tool_result | final | error
            "tool": tool,
            "args": args,
            "ok": ok,
            "model": self.model,
            "duration_ms": duration_ms,
        }
        record.update(extra)  # optional extras such as content, result, error
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")