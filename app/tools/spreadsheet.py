
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
EXCEL_FILE = DATA_DIR / "internships.xlsx"

HEADERS = [
    "Company",
    "Role",
    "Eligibility",
    "Deadline",
    "Application URL",
    "Status",
    "Source Listing ID",
]


def save_internships(internships: list[dict]) -> dict:
    """Save internships using unique listing IDs where available."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if EXCEL_FILE.exists():
        workbook = load_workbook(EXCEL_FILE)
        sheet = (
            workbook["Internships"]
            if "Internships" in workbook.sheetnames
            else workbook.create_sheet("Internships")
        )

        if sheet["A1"].value is None:
            sheet.append(HEADERS[:])
        else:
            current_headers = [
                sheet.cell(1, col).value for col in range(1, 7)
            ]

            if current_headers != HEADERS[:6]:
                workbook.close()
                raise ValueError("Unexpected spreadsheet headers.")

            # Add the new column without deleting existing records.
            if sheet.cell(1, 7).value is None:
                sheet.cell(1, 7, "Source Listing ID")
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Internships"
        sheet.append(HEADERS)

    existing_ids = set()
    existing_urls = set()
    existing_company_roles = set()

    for row in range(2, sheet.max_row + 1):
        listing_id = sheet.cell(row, 7).value
        url = sheet.cell(row, 5).value
        company = sheet.cell(row, 1).value
        role = sheet.cell(row, 2).value

        if listing_id:
            existing_ids.add(str(listing_id).strip())

        if url:
            existing_urls.add(str(url).strip().rstrip("/"))

        if company and role:
            existing_company_roles.add(
                (str(company).strip().lower(),
                 str(role).strip().lower())
            )

    added = 0
    skipped = 0

    try:
        for item in internships:
            url = str(item.get("application_url", "")).strip()
            listing_id = str(
                item.get("source_listing_id") or ""
            ).strip()
            company = str(item.get("company", "")).strip()
            role = str(item.get("role", "")).strip()

            if not url.startswith(("https://", "http://")):
                skipped += 1
                continue

            company_role = (company.lower(), role.lower())

            if listing_id:
                # Live listings are identified by their unique IDs.
                if (
                    listing_id in existing_ids
                    or company_role in existing_company_roles
                ):
                    skipped += 1
                    continue
            elif url.rstrip("/") in existing_urls:
                # Keep URL-based deduplication for records without IDs.
                skipped += 1
                continue

            sheet.append([
                company,
                role,
                item.get("eligibility", ""),
                item.get("deadline", ""),
                url,
                "Pending review",
                listing_id,
            ])

            if listing_id:
                existing_ids.add(listing_id)

            existing_urls.add(url.rstrip("/"))
            existing_company_roles.add(company_role)
            added += 1

        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                fill_type="solid", fgColor="243B64"
            )
            cell.alignment = Alignment(horizontal="center")

        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

        for column, width in {
            "A": 32,
            "B": 42,
            "C": 35,
            "D": 22,
            "E": 55,
            "F": 20,
            "G": 42,
        }.items():
            sheet.column_dimensions[column].width = width

        workbook.save(EXCEL_FILE)
    finally:
        workbook.close()

    return {
        "success": True,
        "added": added,
        "skipped": skipped,
        "file": str(EXCEL_FILE),
    }
