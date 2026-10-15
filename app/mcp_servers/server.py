
from mcp.server.fastmcp import FastMCP

from app.tools.internship_search import search_internships

mcp = FastMCP("taskpilot-internships")


@mcp.tool()
def internship_search(goal: str) -> list[dict]:
    """Search for internships matching a user's goal.

    Currently uses local demo records. Live source integrations
    will be added separately.
    """
    if not goal or not goal.strip():
        raise ValueError("Please provide an internship search goal.")

    return search_internships(goal.strip())


if __name__ == "__main__":
    mcp.run(transport="stdio")
