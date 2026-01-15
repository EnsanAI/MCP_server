from fastmcp import Context
from cachetools import TTLCache, cached
from dependencies import dbops
from tools.models import Clinic
from typing import List, Optional, Dict, Any
import logging
import asyncio
from server import mcp

logger = logging.getLogger("dbops-mcp.clinics")

# Cache clinic info for 24 hours (very static data)
clinic_cache = TTLCache(maxsize=10, ttl=86400)

@mcp.resource("clinics://all")
async def get_all_clinics_resource() -> str:
    """Resource: List all clinics in the network."""
    data = await dbops.get("/clinics")
    
    lines = [f"• {c['name']} ({c['city']}) - {c['phone']}" for c in data]
    return "Available Clinics:\n" + "\n".join(lines)

@mcp.resource("clinics://details/{clinic_id}")
async def get_clinic_details(clinic_id: str) -> str:
    """Resource: Get specific details for a clinic ID."""
    c = await dbops.get(f"/clinics/{clinic_id}")
    return (f"Clinic: {c['name']}\n"
            f"Address: {c['address']}, {c['city']}\n"
            f"Contact: {c['phone']} | {c['email']}")

# --- Tools ---

@mcp.tool()
async def get_clinic_info(clinic_id: Optional[str] = None) -> str:
    """
    Tool: Retrieves information about clinics. 
    If clinic_id is provided, returns details for that clinic.
    If not, returns the first clinic's info (default).
    """
    logger.info(f"Fetching clinic info. Clinic ID: {clinic_id if clinic_id else 'default'}")
    try:
        if clinic_id:
            data = await dbops.get(f"/clinics/{clinic_id}")
            return str(data)
        else:
            # If no clinic_id is provided, fetch the first clinic's info
            clinics = await dbops.get("/clinics")
            if clinics and isinstance(clinics, list) and len(clinics) > 0:
                return str(clinics[0])
            else:
                logger.warning("No clinics found when trying to get default clinic info.")
                return "No clinics found."
    except Exception as e:
        return f"Error fetching clinic info: {str(e)}"

@mcp.tool()
async def get_payment_methods() -> str:
    """Tool: Returns accepted payment methods from the clinic."""
    try:
        data = await dbops.get("/clinics/payment/methods")
        return str(data)
    except Exception as e:
        return f"Error fetching payment methods: {str(e)}"

@mcp.tool()
async def get_visit_type_fees() -> str:
    """Tool: Get visit type fees from the clinic."""
    try:
        data = await dbops.get("/clinics/visit-fees")
        return str(data)
    except Exception as e:
        return f"Error fetching visit fees: {str(e)}"