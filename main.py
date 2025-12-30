import logging
from server import mcp  # Import the configured FastMCP instance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-server")

# --- Import Capabilities ---
# The act of importing these modules triggers the @mcp.tool and @mcp.resource 
# decorators inside them, automatically registering them with the server.
# This keeps main.py clean and acts as a "Plugin Loader".

import tools.doctors
import tools.patients
import tools.appointments
import tools.medication_management
import tools.reminders
import tools.revenue
import tools.clinical
import tools.previsit
import tools.clinic_management

# --- System & Diagnostics (New) ---

@mcp.tool()
async def check_system_health() -> str:
    """
    Diagnostic: Checks connection to DBOps and reports system status.
    Useful for orchestrators (PatientAI) to verify readiness.
    """
    from dependencies import dbops
    try:
        # fast ping to see if we can reach the DBOps container
        # We try to fetch something lightweight, like clinic list or just root
        await dbops.get("/clinics") 
        return " System Status: ONLINE. DBOps connection established."
    except Exception as e:
        logger.error(f"Health Check Failed: {e}")
        return f" System Status: OFFLINE. Error connecting to DBOps: {str(e)}"

# --- JARVIS Pattern: Capability Search ---

@mcp.tool()
async def search_staff_tools(query: str) -> str:
    """
    Meta-Tool: Dynamically identifies relevant tools based on user intent.
    Helps the LLM navigate the large catalog of tools.
    """
    # Simple semantic catalog - scalable to a vector search later if needed
    catalog = {
        "check availability": "doctors://availability/{name}/{date}",
        "list staff": "doctors://list",
        "update schedule": "add_availability_tool",
        "book appointment": "book_appointment",
        "prescribe": "prescribe_medication",
        "revenue": "analytics://revenue/comprehensive/..."
    }
    
    query_lower = query.lower()
    results = [f"Match: '{k}' -> Use Tool/Resource: {v}" for k, v in catalog.items() if k in query_lower]
    
    if not results:
        return "No direct match found. Try listing tools via the standard menu."
    
    return "\n".join(results)

# --- Entry Point ---

if __name__ == "__main__":
    logger.info(" Starting CareBot MCP Server...")
    # This runs the FastMCP server (default port 8000 if not specified)
    mcp.run()