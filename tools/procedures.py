from server import mcp
from dependencies import dbops

@mcp.tool()
async def get_procedure_guidelines(procedure_name: str) -> str:
    """Tool: Gets Pre/Post-visit guidelines for a procedure by name."""
    try:
        data = await dbops.get(f"/procedure-guidelines/procedure/{procedure_name}")
        return f"📋 Guidelines for {procedure_name}:\n{data}"
    except Exception as e:
        return f"No guidelines found for '{procedure_name}'."

@mcp.tool()
async def search_procedures(name: str) -> str:
    """Tool: Search for a procedure ID by name."""
    try:
        data = await dbops.get(f"/procedures/name/{name}")
        return str(data)
    except Exception as e:
        return f"Search failed: {e}"