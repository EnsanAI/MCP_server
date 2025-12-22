from fastmcp import FastMCP
from tools.doctors import (
    list_all_doctors_resource, 
    get_doctor_availability_resource,
    add_availability_tool,
    resolve_doctor_id
)

mcp = FastMCP("CareBot-DBOps-MCP")

# --- Doctors Family Registration ---
mcp.resource("doctors://list", list_all_doctors_resource)
mcp.resource("doctors://availability/{doctor_name}/{date}", get_doctor_availability_resource)
mcp.tool()(add_availability_tool)

# --- JARVIS Pattern: Capability Search ---
@mcp.tool()
async def search_staff_tools(query: str) -> str:
    """Dynamically identifies relevant staff/doctor tools based on intent."""
    catalog = {
        "check availability": "doctors://availability/{name}/{date}",
        "list staff": "doctors://list",
        "update schedule": "add_availability_tool"
    }
    # Simple semantic match logic
    results = [f"Match: {k} -> Use {v}" for k, v in catalog.items() if query.lower() in k]
    return "\n".join(results) if results else "No specific staff tool matched. Try 'list staff'."

if __name__ == "__main__":
    mcp.run()

if __name__ == "__main__":
    mcp.run()