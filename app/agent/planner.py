
from typing import Any


def create_plan(goal: str) -> list[dict[str, Any]]:
    """Convert a user goal into an executable task plan."""

    goal = goal.strip()

    if not goal:
        raise ValueError("Goal cannot be empty.")

    goal_lower = goal.lower()
    steps = []

    # Internship research workflow
    if "internship" in goal_lower:
        steps.append({
            "step_id": "search",
            "tool": "internship_search",
            "description": "Find relevant internship opportunities",
            "status": "pending",
        })

        steps.append({
            "step_id": "save",
            "tool": "spreadsheet",
            "description": "Save internship results to Excel",
            "status": "pending",
        })

        if "email" in goal_lower or "draft" in goal_lower:
            steps.append({
                "step_id": "draft_emails",
                "tool": "email_drafts",
                "description": "Prepare email drafts for review",
                "status": "pending",
            })

        steps.append({
            "step_id": "verify",
            "tool": "verification",
            "description": "Verify that the requested results exist",
            "status": "pending",
        })

    else:
        steps.append({
            "step_id": "general",
            "tool": "general",
            "description": "Analyze the user's goal",
            "status": "pending",
        })

    return steps


if __name__ == "__main__":
    example_goal = (
        "Find internships, save them to Excel, "
        "and prepare email drafts"
    )

    for step in create_plan(example_goal):
        print(step)
