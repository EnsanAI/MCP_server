from fastmcp import Context
from dependencies import dbops
from tools.doctors import resolve_doctor_id
from tools.patients import _resolve_patient_logic
from tools.models import AppointmentBase
import logging
from server import mcp
from typing import List, Optional, Dict, Any


logger = logging.getLogger("dbops-mcp.appointments")


# --- Helpers ---

async def _get_default_clinic_id():
    """Helper: Fetches the first available clinic ID if not provided."""
    clinics = await dbops.get("/clinics")
    return clinics[0]['id'] if clinics else None

async def resolve_last_appointment_id(patient_id: str) -> Optional[str]:
    """
    CONTEXT ENRICHMENT: Finds the most recent appointment ID for a patient.
    Used by pre-visit and clinical tools to link data to the correct visit.
    """
    try:
        # Fetch appointments for this specific patient
        appointments = await dbops.get(f"/patients/{patient_id}/appointments")
        if not appointments:
            return None
        
        # Sort by date/time descending to get the latest one
        # Assuming format is YYYY-MM-DD and HH:MM
        sorted_appts = sorted(
            appointments, 
            key=lambda x: (x['appointment_date'], x['start_time']), 
            reverse=True
        )
        return sorted_appts[0]['id']
    except Exception as e:
        logger.error(f"Error resolving last appointment: {e}")
        return None
# --- MCP Resources (GET) ---

@mcp.resource("appointments://doctor/{doctor_name}")
async def get_doctor_appointments(doctor_name: str) -> str:
    """Resource: Lists all appointments for a specific doctor by name."""
    doc_id = await resolve_doctor_id(doctor_name)
    if not doc_id:
        return f"Error: Doctor '{doctor_name}' not found."

    appointments = await dbops.get("/appointments")
    # Filter locally as the primary GET /appointments returns all
    doc_apps = [a for a in appointments if a['doctor_id'] == doc_id]
    
    if not doc_apps:
        return f"No appointments found for {doctor_name}."

    lines = [f"• {a['appointment_date']} at {a['start_time']} (Status: {a['status']})" for a in doc_apps]
    return f"Schedule for {doctor_name}:\n" + "\n".join(lines)

# --- MCP Tools (Actions) ---

@mcp.tool()
async def book_appointment(
    patient_name: str,
    doctor_name: str,
    date: str,
    start_time: str,
    end_time: str,
    notes: str = ""
) -> str:
    """
    Tool: Books a new appointment using human names.
    Example: 'Book John Doe with Dr. Smith on 2025-12-25 at 10:00'
    """
    # 1. Context Enrichment: Resolve both IDs in parallel
    doc_id = await resolve_doctor_id(doctor_name)
    
    pat_res = await _resolve_patient_logic(patient_name)
    pat_id = None
    if "Found:" in pat_res:
        pat_id = pat_res.split("ID: ")[1].rstrip(")")
        
    clinic_id = await _get_default_clinic_id()

    if not doc_id or not pat_id:
        return f"Error: Could not resolve IDs for {doctor_name} or {patient_name}."

    payload = {
        "clinic_id": clinic_id,
        "patient_id": pat_id,
        "doctor_id": doc_id,
        "appointment_date": date,
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
        "notes": notes
    }

    try:
        res = await dbops.post("/appointments", data=payload)
        return f" Appointment confirmed for {patient_name} with {doctor_name} on {date} at {start_time}."
    except Exception as e:
        return f" Failed to book appointment: {str(e)}"

@mcp.tool()
async def cancel_appointment(appointment_id: str, reason: str) -> str:
    """Tool: Cancels an existing appointment using the appointment ID."""
    try:
        # Per docs: PATCH /appointments/{id}/cancel
        await dbops.patch(f"/appointments/{appointment_id}/cancel", data={"cancellation_reason": reason})
        return f" Appointment {appointment_id} has been cancelled."
    except Exception as e:
        return f" Cancellation failed: {str(e)}"