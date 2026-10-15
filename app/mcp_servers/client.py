
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_servers.server"],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()

            print("Connected to TaskPilot MCP server.")
            print("\nAvailable tools:")

            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description}")

            result = await session.call_tool(
                "internship_search",
                {
                    "goal": (
                        "Find software engineering internships "
                        "and prepare a list"
                    )
                },
            )

            print("\nTool result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
