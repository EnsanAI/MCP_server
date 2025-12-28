from fastmcp import Context
from cachetools import TTLCache, cached
from dependencies import dbops
from tools.models import PatientBase, PatientCreate
import logging
import mcp
from typing import List, Optional, Dict, Any


logger = logging.getLogger("dbops-mcp.patients")

# 10-minute cache for patient registry to ensure quick lookups
patient_cache = TTLCache(maxsize=100, ttl=600)

@cached(patient_cache)
async def _fetch_raw_patients() -> List[dict]:
    """Internal: Fetches all patients from DBOps."""
    return await dbops.get("/patients")

async def resolve_patient_id(name: str) -> Optional[str]:
    """
    CONTEXT ENRICHMENT: Translates 'John Doe' -> UUID.
    """
    raw_data = await _fetch_raw_patients()
    search_name = name.lower().strip()
    
    for p in raw_data:
        full_name = f"{p.get('first_name', p.get('firstName', ''))} {p.get('last_name', p.get('lastName', ''))}".lower()
        if search_name in full_name:
            return p['id']
    return None

# --- MCP Resources (GET) ---

async def get_patient_summary_resource(name: str) -> str:
    """Resource: Returns a patient's medical and reliability summary."""
    patient_id = await resolve_patient_id(name)
    if not patient_id:
        return f"Error: Patient '{name}' not found."

    p = await dbops.get(f"/patients/{patient_id}")
    
    return (f"Patient: {p.get('first_name')} {p.get('last_name')}\n"
            f"Reliability Score: {p.get('reliability_score', 'N/A')}\n"
            f"Medical History: {p.get('medical_history', 'No records')}\n"
            f"Allergies: {', '.join(p.get('allergies', [])) or 'None'}")

async def get_patient_appointments_resource(name: str) -> str:
    """Resource: Fetches all past and upcoming appointments for a patient."""
    patient_id = await resolve_patient_id(name)
    if not patient_id:
        return f"Error: Patient '{name}' not found."

    # Per docs: GET /patients/{id}/appointments
    appointments = await dbops.get(f"/patients/{patient_id}/appointments")
    
    if not appointments:
        return f"No appointments found for {name}."

    lines = [f"• {a['appointment_date']} at {a['start_time']} - Status: {a['status']}" for a in appointments]
    return f"Appointment History for {name}:\n" + "\n".join(lines)

# --- MCP Tools (POST) ---

async def create_patient_tool(
    first_name: str, 
    last_name: str, 
    email: str, 
    phone: str, 
    dob: str
) -> str:
    """Tool: Registers a new patient in the system."""
    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "phoneNumber": phone,
        "dateOfBirth": dob
    }

    try:
        # Per docs: POST /patients
        response = await dbops.post("/patients", data=payload)
        # Clear cache so the new patient can be resolved immediately
        patient_cache.clear()
        return f"Successfully registered new patient: {first_name} {last_name} (ID: {response['id']})"
    except Exception as e:
        return f"Failed to create patient record: {str(e)}"