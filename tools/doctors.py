from fastmcp import Context
from cachetools import TTLCache, cached
from dependencies import dbops
from tools.models import DoctorBase, Availability
from typing import List, Optional, Dict, Any
import logging
from server import mcp

logger = logging.getLogger("dbops-mcp.doctors")

# 2-hour cache for the full staff registry
doctors_cache = TTLCache(maxsize=1, ttl=7200)

async def _fetch_raw_doctors() -> List[dict]:
    """Internal: Raw API call to get all doctors."""
    return await dbops.get("/doctors")

async def resolve_doctor_id(name: str) -> Optional[str]:
    """
    CONTEXT ENRICHMENT: Translates 'Dr. Smith' -> UUID.
    Searches the cached registry to find a name match.
    """
    raw_data = await _fetch_raw_doctors()
    search_name = name.lower().replace("dr.", "").strip()
    
    for doc in raw_data:
        full_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".lower()
        if search_name in full_name:
            return doc['id']
    return None

# --- MCP Resources (GET) ---
async def _get_doctors_list_logic() -> str:
    """Internal logic helper to avoid calling decorated objects."""
    data = await _fetch_raw_doctors()
    doctors = [DoctorBase(**d) for d in data]
    
    lines = [f"- {d.first_name} {d.last_name} ({d.title}) | Languages: {', '.join(d.languages_spoken)}" for d in doctors]
    return "Clinic Staff Registry:\n" + "\n".join(lines)

@mcp.resource("doctors://list")
async def list_all_doctors_resource() -> str:
    """Resource: Returns a human-friendly list of all doctors and their titles."""
    return await _get_doctors_list_logic()

@mcp.resource("doctors://availability/{doctor_name}/{date}")
async def get_doctor_availability_resource(doctor_name: str, date: str) -> str:
    """Resource: Returns availability for a doctor on a specific date."""
    doc_id = await resolve_doctor_id(doctor_name)
    if not doc_id:
        return f"Could not find doctor matching '{doctor_name}'"

    raw_avail = await dbops.get(f"/doctors/{doc_id}/availability", params={"date": date})
    slots = [Availability(**a) for a in raw_avail]
    
    if not slots:
        return f"No specific availability slots found for {doctor_name} on {date}."
    
    avail_str = "\n".join([f"• {s.start_time} - {s.end_time}: {'Available' if s.is_available else 'Booked'}" for s in slots])
    return f"Availability for {doctor_name} on {date}:\n{avail_str}"

# --- MCP Tools (GET) ---
@mcp.tool()
async def get_doctors() -> str:
    """Tool: Lists all doctors. Alias for doctors://list resource."""
    return await _get_doctors_list_logic()

# --- MCP Tools (POST/PATCH) ---
@mcp.tool()
async def add_availability_tool(
    doctor_name: str, 
    day_of_week: str, 
    start_time: str, 
    end_time: str
) -> str:
    """Tool: Sets a doctor's availability using their name."""
    doc_id = await resolve_doctor_id(doctor_name)
    if not doc_id:
        return f"Error: Doctor '{doctor_name}' not found."

    payload = {
        "doctor_id": doc_id,
        "day_of_week": day_of_week.lower(),
        "start_time": start_time,
        "end_time": end_time,
        "is_available": True
    }

    try:
        # Per documentation: POST /doctors/availability
        await dbops.post("/doctors/availability", data=payload)
        return f"Successfully added {day_of_week} availability for {doctor_name} ({start_time}-{end_time})."
    except Exception as e:
        return f"API Error while updating availability: {str(e)}"