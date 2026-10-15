
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
TIMEOUT_MS = 30000

ALLOWED_TOOLS = {
    "internship_search",
    "spreadsheet",
    "email_drafts",
    "verification",
}


def _rule_based_plan(goal: str) -> list:
    """Create a safe plan using only supported tools."""
    from app.agent.planner import create_plan

    plan = create_plan(goal)

    # Convert unsupported planner tool names to supported tools.
    normalized = []
    for step in plan:
        tool = step.get("tool")

        if tool == "general":
            description = str(step.get("description", "")).lower()
            goal_lower = goal.lower()

            if any(word in goal_lower for word in (
                "internship", "internships", "job", "jobs", "career"
            )):
                tool = "internship_search"
            elif any(word in description for word in (
                "verify", "verification"
            )):
                tool = "verification"
            else:
                tool = "internship_search"

        if tool not in ALLOWED_TOOLS:
            raise ValueError(f"Unsupported fallback tool: {tool}")

        step["tool"] = tool
        step["status"] = "pending"
        normalized.append(step)

    # Build a reliable sequence for internship workflows.
    goal_lower = goal.lower()
    plan = [
        {
            "step_id": 1,
            "tool": "internship_search",
            "description": "Search for matching internship listings",
            "status": "pending",
        },
        {
            "step_id": 2,
            "tool": "spreadsheet",
            "description": "Save internship results to Excel",
            "status": "pending",
        },
    ]

    wants_drafts = any(
        word in goal_lower
        for word in ("email", "draft", "drafts")
    )

    if wants_drafts:
        plan.append({
            "step_id": len(plan) + 1,
            "tool": "email_drafts",
            "description": "Prepare email drafts for review",
            "status": "pending",
        })

    plan.append({
        "step_id": len(plan) + 1,
        "tool": "verification",
        "description": "Verify generated files and results",
        "status": "pending",
    })

    return plan


def _validate_plan(plan: list) -> list:
    """Validate tool names and step ordering."""
    if not isinstance(plan, list) or not plan:
        raise ValueError("The planner returned an empty or invalid plan.")

    seen_tools = set()

    for index, step in enumerate(plan, start=1):
        if not isinstance(step, dict):
            raise ValueError("Every plan step must be an object.")

        tool = step.get("tool")
        if tool not in ALLOWED_TOOLS:
            raise ValueError(f"Unsupported tool in plan: {tool}")

        if tool in seen_tools:
            raise ValueError(f"Duplicate tool in plan: {tool}")

        if not step.get("description"):
            raise ValueError(f"Step {index} is missing a description.")

        seen_tools.add(tool)
        step["step_id"] = index
        step["status"] = "pending"

    if plan[0]["tool"] != "internship_search":
        raise ValueError("Plan must start with internship_search.")

    if plan[-1]["tool"] != "verification":
        raise ValueError("Plan must end with verification.")

    if "spreadsheet" in seen_tools:
        search_index = next(
            i for i, step in enumerate(plan)
            if step["tool"] == "internship_search"
        )
        sheet_index = next(
            i for i, step in enumerate(plan)
            if step["tool"] == "spreadsheet"
        )
        if sheet_index < search_index:
            raise ValueError("Spreadsheet must follow internship search.")

    if "email_drafts" in seen_tools:
        if "spreadsheet" not in seen_tools:
            raise ValueError("Email drafts require a spreadsheet step.")

        sheet_index = next(
            i for i, step in enumerate(plan)
            if step["tool"] == "spreadsheet"
        )
        drafts_index = next(
            i for i, step in enumerate(plan)
            if step["tool"] == "email_drafts"
        )
        if drafts_index < sheet_index:
            raise ValueError("Email drafts must follow spreadsheet.")

    return plan


def generate_plan(goal: str) -> list:
    """Use Gemini to plan a task, falling back to supported tools."""
    if not goal or not goal.strip():
        raise ValueError("The task goal cannot be empty.")

    prompt = f"""
You are the planning component of TaskPilot AI.

User goal:
{goal}

Return a JSON array of steps using only these tool names:
- internship_search
- spreadsheet
- email_drafts
- verification

Rules:
- Search before saving.
- Save before preparing email drafts.
- Include email_drafts only if requested.
- Never send emails.
- Always finish with verification.
- Every step must contain step_id, tool, description, and status.
- Use status "pending".
- Return JSON only, without Markdown fences.
"""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("GEMINI_API_KEY missing; using rule-based planner.")
        return _validate_plan(_rule_based_plan(goal))

    client = None

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=TIMEOUT_MS),
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        plan = json.loads(response.text)
        return _validate_plan(plan)

    except Exception as exc:
        print(
            f"Gemini planning failed ({exc}). "
            "Using the rule-based planner as a fallback."
        )
        return _validate_plan(_rule_based_plan(goal))

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    goal = (
        "Find software engineering internships, save them to Excel, "
        "and prepare email drafts"
    )

    for step in generate_plan(goal):
        print(step)
