import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ==================================================
# PROJECT CONFIGURATION
# ==================================================

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.executor import execute_goal
from app.storage.task_store import load_task

EXCEL_FILE = ROOT / "data" / "internships.xlsx"
DRAFTS_DIR = ROOT / "data" / "drafts"

st.set_page_config(
    page_title="TaskPilot AI",
    page_icon="🤖",
    layout="wide",
)

# ==================================================
# CUSTOM CSS - CREAM AND OLIVE THEME
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #F8F6F0;
        color: #26352B;
    }

    [data-testid="stHeader"] {
        background: rgba(248, 246, 240, 0.96);
    }

    .block-container {
        max-width: 1680px;
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }

    h1, h2, h3, h4 {
        color: #26352B !important;
        letter-spacing: -0.025em;
    }

    p, label, [data-testid="stMarkdownContainer"] {
        color: #465047;
    }

    .tp-brand {
        font-size: 31px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #26352B;
    }

    .tp-eye {
        color: #718064;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.7px;
        margin-bottom: 7px;
    }

    .tp-muted {
        color: #777C71;
        font-size: 13px;
        line-height: 1.55;
    }

    .stTextArea textarea {
        background: #FFFDF8 !important;
        color: #26352B !important;
        border: 1px solid #DDD8CC !important;
        border-radius: 12px !important;
        padding: 13px !important;
    }

    .stTextArea textarea:focus {
        border-color: #718064 !important;
        box-shadow: 0 0 0 1px #718064 !important;
    }

    .stButton > button[kind="primary"] {
        background: #354A3A !important;
        color: white !important;
        border: 1px solid #354A3A !important;
    }

    
/* Primary Run TaskPilot button */
.stButton > button[kind="primary"] {
    background-color: #354A3A !important;
    color: #FFFFFF !important;
    border: 1px solid #354A3A !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}

.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #FFFFFF !important;
    opacity: 1 !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #465D49 !important;
    color: #FFFFFF !important;
}


    .stDownloadButton > button {
        background: #FFFDF8 !important;
        color: #354A3A !important;
        border: 1px solid #DADFD2 !important;
    }

    [data-testid="stMetric"] {
        background: #FFFDF8;
        border: 1px solid #E8E3D8;
        border-radius: 12px;
        padding: 10px;
    }

    [data-testid="stMetricLabel"] {
        color: #777C71 !important;
    }

    [data-testid="stMetricValue"] {
        color: #26352B !important;
    }

    [data-testid="stExpander"] {
        background: #FFFDF8;
        border: 1px solid #E8E3D8;
        border-radius: 11px;
    }

    [data-testid="stAlert"] {
        border-radius: 11px;
    }

    hr {
        border-color: #E6E1D6;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E5E0D5;
        border-radius: 12px;
        overflow: hidden;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================================================
# SESSION STATE
# ==================================================

if "last_task_id" not in st.session_state:
    st.session_state["last_task_id"] = None

if "last_error" not in st.session_state:
    st.session_state["last_error"] = None

# ==================================================
# HEADER
# ==================================================

h1, h2 = st.columns([4, 1])

with h1:
    st.markdown(
        '<div class="tp-brand">🤖 TaskPilot AI</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "AUTONOMOUS WORKSPACE  ·  PLAN  ·  EXECUTE  ·  VERIFY"
    )

with h2:
    st.markdown(
        "<div style='height:10px'></div>**● Workspace ready**",
        unsafe_allow_html=True,
    )

st.divider()

# ==================================================
# LOAD TASK DATA
# ==================================================

task_id = st.session_state.get("last_task_id")
task = load_task(task_id) if task_id else None

plan = (task or {}).get("plan", [])
results = (task or {}).get("results", [])
status = (task or {}).get("status", "ready")

verification = next(
    (
        result.get("output", {})
        for result in results
        if result.get("tool") == "verification"
    ),
    None,
)

# ==================================================
# TOP ROW: TASK, AGENT ACTIVITY, VERIFICATION
# ==================================================

task_col, activity_col, verify_col = st.columns(
    [1.12, 1.42, 1.0],
    gap="large",
)

# ==================================================
# TASK INPUT
# ==================================================

with task_col:
    st.markdown(
        '<div class="tp-eye">01 / YOUR TASK</div>',
        unsafe_allow_html=True,
    )

    st.subheader("What should I do?")

    st.markdown(
        '<div class="tp-muted">'
        "Describe your goal. TaskPilot executes the workflow "
        "and checks its outputs."
        "</div>",
        unsafe_allow_html=True,
    )

    goal = st.text_area(
        "Task goal",
        value="",
        height=132,
        placeholder=(
            "Find AI and machine learning internships, "
            "save them to Excel, and prepare email drafts."
        ),
        label_visibility="collapsed",
        key="task_goal",
    )

    if st.button(
        "▶  Run TaskPilot",
        type="primary",
        use_container_width=True,
    ):
        if not goal.strip():
            st.warning("Please enter a task first.")

        else:
            st.session_state["last_error"] = None

            try:
                with st.spinner(
                    "Planning and executing your task..."
                ):
                    execution_result = execute_goal(goal.strip())

                st.session_state["last_task_id"] = (
                    execution_result.get("task_id")
                )

                if not execution_result.get("success", False):
                    st.session_state["last_error"] = (
                        execution_result.get(
                            "error",
                            "Task did not complete.",
                        )
                    )

                st.rerun()

            except Exception as exc:
                st.session_state["last_error"] = str(exc)

    # QUICK ACTIONS
    st.markdown(
        '<div class="tp-eye" style="margin-top:20px">'
        "QUICK ACTIONS</div>",
        unsafe_allow_html=True,
    )

    qa, qb = st.columns(2)

    with qa:
        if EXCEL_FILE.exists():
            st.download_button(
                "↓ Excel file",
                EXCEL_FILE.read_bytes(),
                "internships.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )
        else:
            st.button(
                "↓ Excel file",
                disabled=True,
                use_container_width=True,
            )

    with qb:
        drafts_n = (
            len(list(DRAFTS_DIR.glob("*.json")))
            if DRAFTS_DIR.exists()
            else 0
        )

        st.button(
            f"✉ Drafts · {drafts_n}",
            disabled=True,
            use_container_width=True,
        )

    st.caption(
        "Drafts are saved for review. "
        "Emails are not sent automatically."
    )

# ==================================================
# AGENT ACTIVITY
# ==================================================

with activity_col:
    st.markdown(
        '<div class="tp-eye">02 / LIVE EXECUTION</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Agent activity")

    if task:
        done = sum(
            step.get("status") == "completed"
            for step in plan
        )

        m1, m2 = st.columns(2)

        m1.metric("Task status", status.title())
        m2.metric("Steps", f"{done}/{len(plan)}")

        st.caption(f"Task ID: {task_id}")

        if status == "completed":
            st.success("Workflow completed.")

        elif status in ("failed", "interrupted"):
            st.error(
                task.get("error", "Task needs attention.")
            )

        for i, step in enumerate(plan, 1):
            step_status = step.get("status", "pending")

            if step_status == "completed":
                mark = "✅"
            elif step_status == "failed":
                mark = "❌"
            else:
                mark = "⏳"

            name = (
                step.get("tool", "step")
                .replace("_", " ")
                .title()
            )

            with st.expander(
                f"{mark} {i}. {name} · {step_status.title()}",
                expanded=step_status == "failed",
            ):
                if step.get("description"):
                    st.write(step["description"])

                step_result = next(
                    (
                        result
                        for result in results
                        if result.get("step_id")
                        == step.get("step_id")
                    ),
                    None,
                )

                if step_result:
                    if step_result.get("status") == "failed":
                        st.error(
                            step_result.get(
                                "error",
                                "Step failed.",
                            )
                        )

                    else:
                        output = step_result.get("output", {})

                        if isinstance(output, dict):
                            for key, value in output.items():
                                label = key.replace(
                                    "_", " "
                                ).title()

                                if isinstance(value, list):
                                    st.write(
                                        f"**{label}:** "
                                        f"{len(value)} item(s)"
                                    )

                                elif isinstance(
                                    value,
                                    (str, int, float, bool),
                                ) or value is None:
                                    st.write(
                                        f"**{label}:** {value}"
                                    )

                        elif isinstance(output, list):
                            st.write(
                                f"Returned **{len(output)}** "
                                "item(s)."
                            )

    else:
        st.info("Run a task to see the execution steps.")

        for item in [
            "Internship search",
            "Spreadsheet update",
            "Email drafts",
            "Verification",
        ]:
            st.markdown(f"○  {item}")

# ==================================================
# VERIFICATION PANEL
# ==================================================

with verify_col:
    st.markdown(
        '<div class="tp-eye">03 / QUALITY CHECK</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Verification")

    if verification is not None:
        if verification.get("verified"):
            st.success("All checks passed.")
        else:
            st.warning("Some checks need attention.")

        st.metric(
            "Internships found",
            verification.get("internships_found", 0),
        )

        st.metric(
            "Drafts created",
            verification.get("drafts_created", 0),
        )

        st.metric(
            "Spreadsheet rows",
            verification.get("spreadsheet_rows", 0),
        )

        st.write(
            "Spreadsheet exists:",
            (
                "Yes"
                if verification.get("spreadsheet_exists")
                else "No"
            ),
        )

        missing_internships = verification.get(
            "internships_missing_from_sheet"
        )

        if missing_internships:
            st.warning(
                f"{len(missing_internships)} internships "
                "missing from Excel."
            )

        missing_drafts = verification.get("missing_drafts")

        if missing_drafts:
            st.warning(
                f"{len(missing_drafts)} draft files missing."
            )

        if verification.get("spreadsheet_error"):
            st.error(verification["spreadsheet_error"])

    elif task:
        st.info("Verification output was not recorded.")

    else:
        st.info("Verification appears here after a task runs.")

    if st.session_state.get("last_error"):
        st.error(st.session_state["last_error"])

# ==================================================
# FULL-WIDTH INTERNSHIP SPREADSHEET
# ==================================================

st.divider()

st.markdown(
    '<div class="tp-eye">04 / SAVED DATA</div>',
    unsafe_allow_html=True,
)

st.title("Internship spreadsheet")

st.markdown(
    '<div class="tp-muted">'
    "Full-width Excel preview. Scroll horizontally "
    "to inspect every column."
    "</div>",
    unsafe_allow_html=True,
)

if EXCEL_FILE.exists():
    try:
        df = pd.read_excel(EXCEL_FILE)

        if df.empty:
            st.info(
                "The workbook exists but contains no internship rows."
            )

        else:
            fcol, count_col = st.columns([1, 3])

            with fcol:
                query = st.text_input(
                    "Filter rows",
                    placeholder="Company or role…",
                    key="sheet_filter",
                )

            with count_col:
                st.caption(
                    f"{len(df)} rows · {len(df.columns)} columns"
                )

            if query.strip():
                searchable = df.fillna("").astype(str)

                mask = searchable.apply(
                    lambda col: col.str.contains(
                        query,
                        case=False,
                        regex=False,
                    )
                ).any(axis=1)

                view = df.loc[mask]

            else:
                view = df

            st.dataframe(
                view,
                use_container_width=True,
                hide_index=True,
                height=430,
            )

            st.download_button(
                "Download current Excel workbook",
                EXCEL_FILE.read_bytes(),
                "internships.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )

    except Exception as exc:
        st.error(f"Could not read spreadsheet: {exc}")

else:
    st.info(
        "The spreadsheet will appear here after "
        "the first successful task."
    )

# ==================================================
# EMAIL DRAFTS
# ==================================================

st.divider()

st.markdown(
    '<div class="tp-eye">05 / READY FOR REVIEW</div>',
    unsafe_allow_html=True,
)

st.title("Email drafts")

draft_files = (
    sorted(DRAFTS_DIR.glob("*.json"))
    if DRAFTS_DIR.exists()
    else []
)

if not draft_files:
    st.info("No email drafts generated yet.")

else:
    st.caption(
        f"{len(draft_files)} draft files saved locally. "
        "Nothing is sent automatically."
    )

    for path in draft_files:
        try:
            draft = json.loads(
                path.read_text(encoding="utf-8")
            )

        except (json.JSONDecodeError, OSError) as exc:
            st.warning(
                f"Could not read {path.name}: {exc}"
            )
            continue

        # Support JSON files containing a single draft.
        if not isinstance(draft, dict):
            st.warning(
                f"{path.name} does not contain a single draft object."
            )
            continue

        with st.expander(
            f"✉ {draft.get('company', path.stem)} "
            f"· {draft.get('role', '')}"
        ):
            st.write(
                f"**Subject:** {draft.get('subject', '')}"
            )

            st.write(draft.get("body", ""))

            st.download_button(
                "Download draft",
                json.dumps(
                    draft,
                    indent=2,
                    ensure_ascii=False,
                ),
                path.name,
                mime="application/json",
                key=f"download_{path.name}",
            )

# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "TaskPilot AI · Hackathon prototype · "
    "Review opportunities and drafts before taking action."
)