from fastmcp import Context
from cachetools import TTLCache, cached
from dependencies import dbops
from tools.models import Clinic
from typing import List, Optional
import logging
import asyncio
from server import mcp

logger = logging.getLogger("dbops-mcp.clinics")

# Cache clinic info for 24 hours (very static data)
clinic_cache = TTLCache(maxsize=10, ttl=86400)

@mcp.resource("clinics://all")
@cached(clinic_cache)
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