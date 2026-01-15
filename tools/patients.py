from fastmcp import Context
from cachetools import TTLCache, cached
from dependencies import dbops
from tools.models import PatientBase, PatientCreate
import logging
from server import mcp
from typing import List, Optional, Dict, Any


logger = logging.getLogger("dbops-mcp.patients")

# 10-minute cache for patient registry to ensure quick lookups
patient_cache = TTLCache(maxsize=100, ttl=600)
@cached(patient_cache)
async def _fetch_raw_patients() -> List[dict]:
    """Internal: Fetches all patients from DBOps."""
    return await dbops.get("/patients")

async def _resolve_patient_logic(phone_number: str) -> str:
    """Internal logic helper for patient lookup."""
    # 1. Clean & Generate Variations (Ported from Client)
    clean = ''.join(filter(str.isdigit, phone_number))
    variations = [phone_number, clean, f"+{clean}"]
    
    if clean.startswith('0'): 
        variations.append(clean[1:]) # Remove leading 0
    if not clean.startswith('971') and len(clean) >= 9:
        variations.append(f"971{clean}") # Add UAE code

    # 2. Try Lookup
    for var in variations:
        try:
            res = await dbops.get(f"/patients/by-phone/{var}")
            if res and res.get('id'):
                return f"Found: {res.get('first_name')} (ID: {res.get('id')})"
        except:
            continue
            
    return f"Patient not found for number: {phone_number}"

@mcp.tool()
async def resolve_patient_by_phone(phone_number: str) -> str:
    """
    Tool: Smart Patient Lookup. Finds a patient ID using a phone number. 
    Automatically tries variations (e.g. +971, missing 0) to handle formatting issues.
    """
    return await _resolve_patient_logic(phone_number)

# --- MCP Resources (GET) ---
@mcp.resource("patients://appointments/{name}")
async def get_patient_summary_resource(name: str) -> str:
    """Resource: Returns a patient's medical and reliability summary."""
    res_text = await _resolve_patient_logic(name)
    if "Found:" not in res_text:
        return f"Error: Patient '{name}' not found."
    
    patient_id = res_text.split("ID: ")[1].rstrip(")")
    p = await dbops.get(f"/patients/{patient_id}")
    
    return (f"Patient: {p.get('first_name')} {p.get('last_name')}\n"
            f"Reliability Score: {p.get('reliability_score', 'N/A')}\n"
            f"Medical History: {p.get('medical_history', 'No records')}\n"
            f"Allergies: {', '.join(p.get('allergies', [])) or 'None'}")

@mcp.resource("patients://appointments/{name}")
async def get_patient_appointments_resource(name: str) -> str:
    """Resource: Fetches all past and upcoming appointments for a patient."""
    res_text = await _resolve_patient_logic(name)
    if "Found:" not in res_text:
        return f"Error: Patient '{name}' not found."
    
    patient_id = res_text.split("ID: ")[1].rstrip(")")
    appointments = await dbops.get(f"/patients/{patient_id}/appointments")
    
    if not appointments:
        return f"No appointments found for {name}."

    lines = [f"• {a['appointment_date']} at {a['start_time']} - Status: {a['status']}" for a in appointments]
    return f"Appointment History for {name}:\n" + "\n".join(lines)

# --- MCP Tools (POST) ---

@mcp.tool()
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