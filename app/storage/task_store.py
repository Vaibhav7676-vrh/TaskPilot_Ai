
import json
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = PROJECT_ROOT / "data" / "tasks"


def save_task(task_id: str, task: dict) -> str:
    """Save task state to a JSON file."""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    task_path = TASKS_DIR / f"{task_id}.json"
    temp_path = task_path.with_suffix(".tmp")

    temp_path.write_text(
        json.dumps(task, indent=2, default=str),
        encoding="utf-8",
    )

    # Replace the destination only after the temporary file is written.
    temp_path.replace(task_path)

    return str(task_path)


def load_task(task_id: str) -> Optional[dict]:
    """Load saved task state, or return None if it doesn't exist."""
    task_path = TASKS_DIR / f"{task_id}.json"

    if not task_path.exists():
        return None

    return json.loads(
        task_path.read_text(encoding="utf-8")
    )
