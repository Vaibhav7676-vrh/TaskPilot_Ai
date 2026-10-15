
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_FILE = PROJECT_ROOT / "data" / "seed_internships.json"

AICTE_API = (
    "https://internship.aicte-india.org/api/v1/catalogue/internships"
)
AICTE_LISTING_PAGE = "https://internship.aicte-india.org/internships"
TIMEOUT = 15


def _clean_search_query(goal: str) -> str:
    """Extract search keywords from a complete task instruction."""
    query = goal.strip()

    # Keep the search part before task-execution instructions.
    query = re.split(
        r",|;|\bthen\s+(?:save|store|prepare|create|draft|export)\b"
        r"|\band\s+(?:save|store|prepare|create|draft|export)\b",
        query,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Remove leading task verbs.
    query = re.sub(
        r"^\s*(?:please\s+)?"
        r"(?:find|search\s+for|search|look\s+for|show\s+me|get|list)"
        r"\s+",
        "",
        query,
        flags=re.IGNORECASE,
    )

    query = query.strip(" .,!?:;")
    query = re.sub(
    r"\binternships\b",
    "internship",
    query,
    flags=re.IGNORECASE,
)
    return query 


def _load_demo_listings() -> list[dict]:
    """Load clearly labelled demo records only when the API fails."""
    if not SEED_FILE.exists():
        return []

    with SEED_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Seed dataset must contain a JSON list.")

    return [
        item
        for item in records
        if isinstance(item, dict)
        and item.get("company")
        and item.get("role")
        and item.get("application_url")
    ]


def _build_application_url(item: dict) -> str:
    """Build the AICTE internship detail-page URL."""
    listing_id = item.get("id")

    if not listing_id:
        return AICTE_LISTING_PAGE

    return f"{AICTE_LISTING_PAGE}/{listing_id}"


def _normalise_aicte_item(item: dict) -> dict:
    """Convert an AICTE API record into TaskPilot's format."""
    eligibility = item.get("eligibility") or []

    if isinstance(eligibility, list):
        eligibility_text = (
            "; ".join(str(value) for value in eligibility)
            if eligibility
            else "Check the official listing"
        )
    else:
        eligibility_text = str(eligibility)

    return {
        "company": item.get("organization") or "Unknown organization",
        "role": item.get("title") or "Untitled internship",
        "eligibility": eligibility_text,
        "deadline": item.get("deadline") or "Not specified",
        "application_url": _build_application_url(item),
        "source": "AICTE National Internship Portal",
        "source_listing_id": item.get("id") or item.get("uid"),
        "location": item.get("location") or "Not specified",
        "mode": item.get("mode") or "Not specified",
        "duration": item.get("duration") or "Not specified",
        "stipend": item.get("stipendDisplay") or "Not specified",
        "skills": item.get("skills") or [],
        "posted_date": item.get("postedDate"),
        "is_open": item.get("isOpen"),
        "verified": item.get("verified"),
        "data_origin": "live_aicte_api",
    }


def _fetch_aicte_page(
    query: str,
    page: int = 1,
    page_size: int = 12,
) -> dict:
    """Fetch one page from the AICTE internship catalogue."""
    params = {
        "sort": "best",
        "page": page,
        "pageSize": page_size,
    }

    if query.strip():
        params["q"] = query.strip()

    url = f"{AICTE_API}?{urlencode(params)}"

    request = Request(
        url,
        headers={
            "User-Agent": "TaskPilotAI/1.0",
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("items"), list)
    ):
        raise ValueError("Unexpected AICTE catalogue response.")

    return payload


def search_internships(
    goal: str,
    max_pages: int = 2,
    page_size: int = 12,
) -> list[dict]:
    """Search live AICTE listings using cleaned task keywords."""
    if not goal or not goal.strip():
        raise ValueError("Please provide an internship search goal.")

    query = _clean_search_query(goal) or goal.strip()
    print(f"AICTE search query: {query}")

    
    try:
        # Try the original query first, then simpler alternatives.
        query_variants = [query]

        lowered = query.lower()

        if "machine learning" in lowered and "ai" in lowered:
            query_variants.extend([
                "AI internship",
                "machine learning internship",
            ])
        elif "machine learning" in lowered:
            query_variants.append("AI internship")
        elif "ai" in lowered:
            query_variants.append("machine learning internship")

        all_items = []
        seen_ids = set()

        for search_query in dict.fromkeys(query_variants):
            print(f"Trying AICTE query: {search_query}")

            first_page = _fetch_aicte_page(
                search_query,
                page=1,
                page_size=page_size,
            )

            items = list(first_page["items"])
            total_pages = min(
                int(first_page.get("totalPages") or 1),
                max(1, max_pages),
            )

            for page in range(2, total_pages + 1):
                page_data = _fetch_aicte_page(
                    search_query,
                    page=page,
                    page_size=page_size,
                )
                items.extend(page_data["items"])

            for item in items:
                if not isinstance(item, dict):
                    continue

                listing_id = item.get("id") or item.get("uid")

                if listing_id:
                    if listing_id in seen_ids:
                        continue
                    seen_ids.add(listing_id)

                all_items.append(item)

        results = [
            _normalise_aicte_item(item)
            for item in all_items
        ]

        print(f"AICTE listings returned: {len(results)}")
        return results

    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(
            f"AICTE API unavailable ({exc}). "
            "Trying clearly labelled local demo records."
        )
        return _load_demo_listings()



if __name__ == "__main__":
    internships = search_internships(
        "Find software engineering internships, "
        "save them to Excel, and prepare email drafts"
    )

    print(f"\nFound {len(internships)} internships\n")

    for index, internship in enumerate(internships, start=1):
        print(f"{index}. {internship['role']}")
        print(f"   Company: {internship['company']}")
        print(f"   Deadline: {internship['deadline']}")
        print(f"   URL: {internship['application_url']}")
        print(f"   Source: {internship['source']}")
        print()
