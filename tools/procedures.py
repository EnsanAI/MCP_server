from server import mcp
from dependencies import dbops
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("dbops-mcp.procedures")

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

@mcp.tool()
async def list_procedures() -> str:
    """Tool: Lists all available medical procedures."""
    try:
        data = await dbops.get("/procedures")
        if isinstance(data, list):
             lines = [f"• {p.get('name', 'Unknown')} (ID: {p.get('id', 'N/A')})" for p in data]
             return "Available Procedures:\n" + "\n".join(lines)
        return str(data)
    except Exception as e:
        return f"Failed to list procedures: {e}"

@mcp.tool()
async def get_all_dental_procedures() -> str:
    """Gets a list of all available dental procedures with pricing information."""
    logger.info("Fetching all dental procedures.")
    try:
        data = await dbops.get("/procedures")
        return str(data)
    except Exception as e:
        return f"Failed to fetch dental procedures: {str(e)}"