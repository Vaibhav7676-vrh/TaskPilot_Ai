
from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DRAFTS_DIR = PROJECT_ROOT / "data" / "drafts"


def create_email_drafts(internships: list[dict]) -> list[dict]:
    """Create local email drafts for internship applications."""

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    created_drafts = []

    for internship in internships:
        company = internship.get("company", "Company")
        role = internship.get("role", "Internship")
        safe_name = "".join(
            char if char.isalnum() else "_"
            for char in company
        ).strip("_")

        draft = {
            "company": company,
            "role": role,
            "subject": f"Application for {role}",
            "body": (
                f"Dear {company} Hiring Team,\n\n"
                f"I am writing to express my interest in the "
                f"{role} opportunity at {company}.\n\n"
                "I am a student interested in software development "
                "and would appreciate the opportunity to be considered. "
                "I can share my resume and relevant project details "
                "for your review.\n\n"
                "Thank you for your time and consideration.\n\n"
                "Best regards,\n"
                "[Your Name]"
            ),
        }

        file_path = DRAFTS_DIR / f"{safe_name or 'company'}_draft.json"
        file_path.write_text(
            json.dumps(draft, indent=2),
            encoding="utf-8",
        )

        created_drafts.append({
            **draft,
            "file": str(file_path),
        })

    return created_drafts


if __name__ == "__main__":
    sample = [{
        "company": "Demo Technologies",
        "role": "Software Engineering Intern",
    }]

    for draft in create_email_drafts(sample):
        print(f"Created draft: {draft['file']}")
