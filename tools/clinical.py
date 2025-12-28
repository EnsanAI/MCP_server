from fastmcp import Context
from dependencies import dbops
from tools.patients import resolve_patient_id
from tools.models import SoapNoteCreate, SoapNoteUpdate, TreatmentPlanCreate
from typing import List, Optional, Dict, Any
import logging
import mcp
import datetime

logger = logging.getLogger("dbops-mcp.clinical")

# --- Helpers ---

async def resolve_last_appointment_id(patient_name: str) -> Optional[str]:
    """
    Context Enrichment: Finds the most recent appointment UUID for a patient.
    Essential for 'Add note to John's appointment' commands.
    """
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return None
    
    # Fetch all appointments and sort by date/time
    # Assuming the API returns them sorted or we sort manually
    apps = await dbops.get(f"/patients/{patient_id}/appointments")
    if not apps: return None
    
    # Sort descending (newest first) - assuming ISO strings
    apps.sort(key=lambda x: x['appointment_date'] + x['start_time'], reverse=True)
    return apps[0]['id']

# ==========================================
# Family 1: SOAP Notes (6 Endpoints)
# ==========================================

# --- Resources ---

@mcp.resource("clinical://soap/all/{appointment_id}")
async def get_appointment_soap_notes(appointment_id: str) -> str:
    """Resource: Get all SOAP notes linked to a specific appointment ID."""
    notes = await dbops.get(f"/appointments/{appointment_id}/soap-notes")
    return f"SOAP Notes for Appt {appointment_id}:\n{notes}"

@mcp.resource("clinical://soap/latest/{patient_name}")
async def get_latest_soap_note(patient_name: str) -> str:
    """Resource: Get the most recent SOAP note for a patient's last visit."""
    # Enrichment: Find the appointment first
    appt_id = await resolve_last_appointment_id(patient_name)
    if not appt_id: return f"Error: No recent appointment found for {patient_name}."

    try:
        note = await dbops.get(f"/appointments/{appt_id}/soap-notes/latest")
        return (f"Latest SOAP Note for {patient_name}:\n"
                f"S: {note.get('subjective')}\n"
                f"O: {note.get('objective')}\n"
                f"A: {note.get('assessment')}\n"
                f"P: {note.get('plan')}")
    except Exception:
        return "No SOAP notes found for the last appointment."

@mcp.resource("clinical://soap/history/{appointment_id}")
async def get_soap_note_history(appointment_id: str) -> str:
    """Resource: Get version history of SOAP notes for an appointment."""
    history = await dbops.get(f"/appointments/{appointment_id}/soap-notes/history")
    return f"Version History:\n{history}"

# --- Tools ---

@mcp.tool()
async def create_soap_note(
    patient_name: str,
    subjective: str,
    objective: str,
    assessment: str,
    plan: str,
    bp: str = None,
    hr: int = None,
    temp: float = None
) -> str:
    """
    Tool: Creates a new SOAP note. 
    automatically attaches it to the patient's most recent appointment.
    """
    appt_id = await resolve_last_appointment_id(patient_name)
    if not appt_id: return f"Error: Could not find a recent appointment for {patient_name} to attach this note to."

    payload = {
        "subjective": subjective,
        "objective": objective,
        "assessment": assessment,
        "plan": plan,
        "vitalSigns": {}
    }
    # Add vitals if provided
    if bp: payload["vitalSigns"]["bloodPressure"] = bp
    if hr: payload["vitalSigns"]["heartRate"] = hr
    if temp: payload["vitalSigns"]["temperature"] = temp

    try:
        await dbops.post(f"/appointments/{appt_id}/soap-notes", data=payload)
        return f"✅ SOAP Note created for {patient_name} (Appt: {appt_id})."
    except Exception as e:
        return f"❌ Failed to create note: {str(e)}"

@mcp.tool()
async def update_soap_note(
    appointment_id: str,
    note_id: str,
    subjective: Optional[str] = None,
    objective: Optional[str] = None
) -> str:
    """Tool: Updates fields in an existing SOAP note."""
    payload = {}
    if subjective: payload["subjective"] = subjective
    if objective: payload["objective"] = objective
    
    try:
        await dbops.put(f"/appointments/{appointment_id}/soap-notes/{note_id}", data=payload)
        return f"✅ SOAP Note {note_id} updated."
    except Exception as e:
        return f"❌ Update failed: {str(e)}"

@mcp.tool()
async def version_soap_note(
    appointment_id: str,
    note_id: str,
    subjective: str,
    objective: str
) -> str:
    """Tool: Creates a new version of a SOAP note (preserves history)."""
    payload = {
        "subjective": subjective,
        "objective": objective
    }
    try:
        await dbops.post(f"/appointments/{appointment_id}/soap-notes/{note_id}/new-version", data=payload)
        return f"✅ New version created for note {note_id}."
    except Exception as e:
        return f"❌ Versioning failed: {str(e)}"

# ==========================================
# Family 2: Treatment Plans (6 Endpoints)
# ==========================================

# --- Resources ---

@mcp.resource("clinical://plans/active/{patient_name}")
async def get_active_treatment_plans(patient_name: str) -> str:
    """Resource: Get all ACTIVE treatment plans for a patient."""
    pat_id = await resolve_patient_id(patient_name)
    if not pat_id: return f"Error: Patient '{patient_name}' not found."

    plans = await dbops.get(f"/treatment-plans/patient/{pat_id}", params={"status": "active"})
    if not plans: return f"No active treatment plans for {patient_name}."
    
    return f"Active Plans for {patient_name}:\n{plans}"

@mcp.resource("clinical://plans/history/{patient_name}")
async def get_treatment_plan_history(patient_name: str) -> str:
    """Resource: Get full history of treatment plans."""
    pat_id = await resolve_patient_id(patient_name)
    if not pat_id: return f"Error: Patient '{patient_name}' not found."

    return await dbops.get(f"/treatment-plans/patient/{pat_id}/history")

@mcp.resource("clinical://plans/appointment/{appointment_id}")
async def get_plan_by_appointment(appointment_id: str) -> str:
    """Resource: Get the treatment plan associated with a specific appointment."""
    return await dbops.get(f"/treatment-plans/appointment/{appointment_id}")

# --- Tools ---

@mcp.tool()
async def create_treatment_plan(
    patient_name: str,
    diagnosis: str,
    medication_intervention: str,
    lifestyle_intervention: str
) -> str:
    """
    Tool: Creates a new treatment plan with initial interventions.
    Automatically links to patient's last appointment.
    """
    pat_id = await resolve_patient_id(patient_name)
    appt_id = await resolve_last_appointment_id(patient_name)
    
    if not pat_id or not appt_id:
        return "Error: Could not resolve Patient ID or recent Appointment."

    payload = {
        "patientId": pat_id,
        "appointmentId": appt_id,
        "diagnosis": diagnosis,
        "status": "active",
        "interventions": [
            {"type": "medication", "description": medication_intervention, "priority": "high"},
            {"type": "lifestyle", "description": lifestyle_intervention, "priority": "medium"}
        ]
    }

    try:
        await dbops.post("/treatment-plans", data=payload)
        return f"✅ Treatment Plan created for {diagnosis}."
    except Exception as e:
        return f"❌ Creation failed: {str(e)}"

@mcp.tool()
async def update_treatment_plan(
    plan_id: str,
    status: str,
    notes: str
) -> str:
    """Tool: Updates status (e.g. 'completed') of a treatment plan."""
    payload = {"status": status, "notes": notes}
    try:
        await dbops.put(f"/treatment-plans/{plan_id}", data=payload)
        return f"✅ Plan {plan_id} updated to {status}."
    except Exception as e:
        return f"❌ Update failed: {str(e)}"

@mcp.tool()
async def discontinue_treatment_plan(plan_id: str, reason: str) -> str:
    """Tool: Discontinues a plan (e.g., patient recovered)."""
    try:
        await dbops.post(f"/treatment-plans/{plan_id}/discontinue", data={"reason": reason})
        return f"✅ Plan {plan_id} discontinued."
    except Exception as e:
        return f"❌ Discontinue failed: {str(e)}"