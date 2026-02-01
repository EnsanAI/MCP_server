from fastmcp import Context
from cachetools import TTLCache, cached
from dependencies import dbops
from tools.models import PatientBase, PatientCreate
import logging
from server import mcp
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json


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
@mcp.resource("patients://appointments/{name}")
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

@mcp.resource("patients://appointments/{name}")
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

# --- NEW PATIENT MANAGEMENT TOOLS ---

@mcp.resource("patients://info/{patient_name}")
async def get_patient_info(patient_name: str) -> str:
    """Returns complete patient information including contact details and demographics."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    patient = await dbops.get(f"/patients/{patient_id}")

    return (
        f"=== PATIENT INFORMATION ===\n"
        f"Name: {patient['first_name']} {patient['last_name']}\n"
        f"DOB: {patient['date_of_birth']}\n"
        f"Gender: {patient.get('gender', 'N/A')}\n"
        f"\n=== CONTACT INFO ===\n"
        f"Phone: {patient['user']['phoneNumber']}\n"
        f"Email: {patient['user']['email']}\n"
        f"Emergency Contact: {patient.get('emergency_contact', 'N/A')}\n"
        f"Emergency Phone: {patient.get('emergency_phone', 'N/A')}\n"
        f"\n=== PATIENT STATUS ===\n"
        f"Reliability Score: {patient.get('reliability_score', 100)}/100\n"
        f"No-Shows: {patient.get('no_show_count', 0)}\n"
        f"Insurance: {patient.get('insurance_provider', 'N/A')}"
    )

@mcp.resource("patients://appointments/upcoming/{patient_name}")
async def get_patient_upcoming_appointments(patient_name: str) -> str:
    """Returns all upcoming appointments for a patient."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    all_appointments = await dbops.get(f"/appointments/patient/{patient_id}")

    # Filter for future appointments
    today = date.today()

    upcoming = [
        apt for apt in all_appointments
        if apt['status'] in ['scheduled', 'confirmed'] and
           datetime.fromisoformat(apt['appointment_date']).date() >= today
    ]

    if not upcoming:
        return f"No upcoming appointments for {patient_name}"

    result = f"=== UPCOMING APPOINTMENTS FOR {patient_name.upper()} ===\n\n"
    for apt in upcoming:
        result += (
            f"Date: {apt['appointment_date']} at {apt['start_time']}\n"
            f"Doctor: Dr. {apt['doctor']['first_name']} {apt['doctor']['last_name']}\n"
            f"Type: {apt['appointmentType']['name']}\n"
            f"Status: {apt['status']}\n"
            f"Notes: {apt.get('notes', 'None')}\n"
            f"---\n"
        )

    return result

@mcp.resource("patients://appointments/history/{patient_name}")
async def get_patient_appointment_history(
    patient_name: str,
    start_date: str = None,  # Optional: YYYY-MM-DD
    end_date: str = None     # Optional: YYYY-MM-DD
) -> str:
    """Returns appointment history for a patient, optionally filtered by date range.

    Args:
        patient_name: Patient's full name or partial name
        start_date: Optional start date (YYYY-MM-DD). Defaults to all history.
        end_date: Optional end date (YYYY-MM-DD). Defaults to today.
    """
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    all_appointments = await dbops.get(f"/appointments/patient/{patient_id}")

    # Filter appointments
    # Default: all past appointments
    if not start_date:
        start_date = "1900-01-01"
    if not end_date:
        end_date = date.today().isoformat()

    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except ValueError:
        return "Error: Invalid date format. Use YYYY-MM-DD."

    history = [
        apt for apt in all_appointments
        if start <= datetime.fromisoformat(apt['appointment_date']).date() <= end
    ]

    if not history:
        return f"No appointments found for {patient_name} between {start_date} and {end_date}"

    result = f"=== APPOINTMENT HISTORY FOR {patient_name.upper()} ===\n"
    result += f"Period: {start_date} to {end_date}\n"
    result += f"Total: {len(history)} appointments\n\n"

    for apt in history:
        result += (
            f"• {apt['appointment_date']} at {apt['start_time']} - "
            f"Dr. {apt['doctor']['last_name']} ({apt['appointmentType']['name']}) - "
            f"{apt['status']}\n"
        )

    return result

@mcp.resource("patients://medical-profile/{patient_name}")
async def get_patient_medical_profile(patient_name: str) -> str:
    """Returns patient's medical profile: allergies, medications, medical history, insurance."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    patient = await dbops.get(f"/patients/{patient_id}")

    result = f"=== MEDICAL PROFILE: {patient['first_name']} {patient['last_name']} ===\n\n"

    # Allergies
    allergies = patient.get('allergies', [])
    result += "ALLERGIES:\n"
    if allergies:
        for allergy in allergies:
            result += f"  • {allergy}\n"
    else:
        result += "  • No known allergies\n"

    # Current Medications
    medications = patient.get('medications', [])
    result += "\nCURRENT MEDICATIONS:\n"
    if medications:
        for med in medications:
            result += f"  • {med}\n"
    else:
        result += "  • No current medications\n"

    # Medical History
    medical_history = patient.get('medical_history', {})
    result += "\nMEDICAL HISTORY:\n"
    if medical_history:
        result += f"{json.dumps(medical_history, indent=2)}\n"
    else:
        result += "  • No medical history recorded\n"

    # Insurance
    result += "\nINSURANCE:\n"
    result += f"  Provider: {patient.get('insurance_provider', 'N/A')}\n"
    result += f"  Policy Number: {patient.get('insurance_policy_number', 'N/A')}\n"

    return result

@mcp.tool()
async def update_patient_profile(
    patient_name: str,
    first_name: str = None,
    last_name: str = None,
    date_of_birth: str = None,  # YYYY-MM-DD
    gender: str = None,
    emergency_contact: str = None,
    emergency_phone: str = None,
    insurance_provider: str = None,
    insurance_policy_number: str = None
) -> str:
    """Updates patient profile information. Only provided fields will be updated.

    Args:
        patient_name: Current patient name for identification
        first_name: Optional - New first name
        last_name: Optional - New last name
        date_of_birth: Optional - New DOB (YYYY-MM-DD)
        gender: Optional - New gender
        emergency_contact: Optional - Emergency contact name
        emergency_phone: Optional - Emergency contact phone
        insurance_provider: Optional - Insurance provider name
        insurance_policy_number: Optional - Insurance policy number
    """
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    # Build update payload with only provided fields
    update_data = {}
    if first_name:
        update_data['first_name'] = first_name
    if last_name:
        update_data['last_name'] = last_name
    if date_of_birth:
        update_data['date_of_birth'] = date_of_birth
    if gender:
        update_data['gender'] = gender
    if emergency_contact:
        update_data['emergency_contact'] = emergency_contact
    if emergency_phone:
        update_data['emergency_phone'] = emergency_phone
    if insurance_provider:
        update_data['insurance_provider'] = insurance_provider
    if insurance_policy_number:
        update_data['insurance_policy_number'] = insurance_policy_number

    if not update_data:
        return "Error: No fields provided to update."

    try:
        updated_patient = await dbops.patch(f"/patients/{patient_id}", data=update_data)
        patient_cache.clear()  # Invalidate cache

        updated_fields = ", ".join(update_data.keys())
        return f"✅ Successfully updated patient profile for {patient_name}. Updated fields: {updated_fields}"
    except Exception as e:
        return f"❌ Failed to update patient profile: {str(e)}"

@mcp.tool()
async def update_patient_medical_profile(
    patient_name: str,
    allergies: list[str] = None,
    medications: list[str] = None,
    medical_history: dict = None
) -> str:
    """Updates patient's medical profile (allergies, medications, medical history).

    Args:
        patient_name: Patient's full name or partial name
        allergies: Optional - List of allergies (replaces existing)
        medications: Optional - List of current medications (replaces existing)
        medical_history: Optional - Medical history object (merges with existing)
    """
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    # Build update payload
    update_data = {}
    if allergies is not None:
        update_data['allergies'] = allergies
    if medications is not None:
        update_data['medications'] = medications
    if medical_history is not None:
        update_data['medical_history'] = medical_history

    if not update_data:
        return "Error: No medical fields provided to update."

    try:
        updated_patient = await dbops.patch(f"/patients/{patient_id}", data=update_data)
        patient_cache.clear()  # Invalidate cache

        updated_fields = ", ".join(update_data.keys())
        return f"✅ Successfully updated medical profile for {patient_name}. Updated: {updated_fields}"
    except Exception as e:
        return f"❌ Failed to update medical profile: {str(e)}"