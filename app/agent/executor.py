
import uuid
from datetime import datetime, timezone

from app.agent.llm import generate_plan
from app.storage.task_store import save_task, load_task
from app.tools.internship_search import search_internships
from app.tools.spreadsheet import save_internships
from app.tools.email_drafts import create_email_drafts
from app.services.verification import verify_results


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_task(task: dict) -> dict:
    """Execute a saved task, skipping steps already completed."""

    task_id = task["task_id"]
    goal = task["goal"]
    plan = task["plan"]
    context = task.setdefault(
        "context", {"internships": [], "drafts": []}
    )
    results = task.setdefault("results", [])

    task["status"] = "running"
    task.pop("error", None)
    save_task(task_id, task)

    for step in plan:
        # Don't repeat successfully completed steps.
        if step.get("status") == "completed":
            continue

        tool_name = step["tool"]

        # A previously running step may have performed a side effect
        # before a crash. Do not blindly retry it.
        if step.get("status") == "running":
            task["status"] = "interrupted"
            task["error"] = (
                f"Step {step.get('step_id')} ({tool_name}) was running "
                "when execution stopped. Check its side effects before retrying."
            )
            save_task(task_id, task)
            return {"success": False, **task}

        step["status"] = "running"
        save_task(task_id, task)

        try:
            if tool_name == "internship_search":
                output = search_internships(goal)
                context["internships"] = output

            elif tool_name == "spreadsheet":
                output = save_internships(context["internships"])
                if not output.get("success", False):
                    raise RuntimeError("Spreadsheet operation failed")

            elif tool_name == "email_drafts":
                output = create_email_drafts(context["internships"])
                context["drafts"] = output

            elif tool_name == "verification":
                output = verify_results(context)
                if not output.get("verified", False):
                    raise RuntimeError(f"Verification failed: {output}")

            else:
                raise ValueError(f"Unsupported tool: {tool_name}")

            step["status"] = "completed"
            results.append({
                "step_id": step["step_id"],
                "tool": tool_name,
                "status": "completed",
                "output": output,
            })
            save_task(task_id, task)

        except Exception as exc:
            step["status"] = "failed"
            task["status"] = "failed"
            task["error"] = str(exc)
            results.append({
                "step_id": step["step_id"],
                "tool": tool_name,
                "status": "failed",
                "error": str(exc),
            })
            save_task(task_id, task)
            return {"success": False, **task}

    task["status"] = "completed"
    task["completed_at"] = now_utc()
    save_task(task_id, task)
    return {"success": True, **task}


def execute_goal(goal: str) -> dict:
    """Create a new task using Gemini, then execute it."""

    plan = generate_plan(goal)
    task = {
        "task_id": str(uuid.uuid4()),
        "goal": goal,
        "status": "pending",
        "created_at": now_utc(),
        "plan": plan,
        "results": [],
        "context": {"internships": [], "drafts": []},
    }
    save_task(task["task_id"], task)
    return run_task(task)


def resume_task(task_id: str) -> dict:
    """Load and resume a previously saved task."""

    task = load_task(task_id)
    if task is None:
        raise ValueError(f"Task not found: {task_id}")

    if task.get("status") == "completed":
        return {"success": True, **task}

    return run_task(task)


if __name__ == "__main__":
    import json

    result = execute_goal(
        "Find internships, save them to Excel, and prepare email drafts"
    )
    print(json.dumps(result, indent=2, default=str))
