from fastmcp import Context
import mcp
from dependencies import dbops
from tools.patients import resolve_patient_id
from tools.models import MedicationCreate, MedicationUpdate, MedicationRefill
from typing import Optional
import logging

logger = logging.getLogger("dbops-mcp.medications")

# --- Helpers ---

async def resolve_medication_id(patient_id: str, med_name: str) -> Optional[str]:
    """
    Context Enrichment: Finds a specific medication UUID for a patient by name.
    Useful for 'Refill Metformin' commands where the Agent doesn't know the ID.
    """
    # Fetch active medications first
    meds = await dbops.get(f"/patients/{patient_id}/medications")
    search_name = med_name.lower().strip()
    
    for m in meds:
        if search_name in m['medicationName'].lower():
            return m['id']
    return None

# --- MCP Resources (GET) ---

@mcp.resource("medications://all/{patient_name}")
async def get_all_medications(patient_name: str) -> str:
    """Resource: Returns ALL medications (active and past) for a patient."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    # Endpoint: GET /patients/{patientId}/medications
    meds = await dbops.get(f"/patients/{patient_id}/medications")
    if not meds: return f"No medication records found for {patient_name}."

    lines = [f"• {m['medicationName']} ({m['status']}) - {m['dosage']}" for m in meds]
    return f"Full Medication List for {patient_name}:\n" + "\n".join(lines)

@mcp.resource("medications://active/{patient_name}")
async def get_active_medications(patient_name: str) -> str:
    """Resource: Returns ONLY active medications."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    # Endpoint: GET /patients/{patientId}/medications/active
    meds = await dbops.get(f"/patients/{patient_id}/medications/active")
    if not meds: return f"{patient_name} has no active medications."

    lines = [f"• {m['medicationName']} - {m['dosage']} ({m['frequency']})" for m in meds]
    return f"Active Prescriptions for {patient_name}:\n" + "\n".join(lines)

@mcp.resource("medications://history/{patient_name}/{start_date}/{end_date}")
async def get_medication_history(patient_name: str, start_date: str, end_date: str) -> str:
    """Resource: Returns medication history within a specific date range."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    # Endpoint: GET /patients/{patientId}/medications/history
    params = {"startDate": start_date, "endDate": end_date}
    meds = await dbops.get(f"/patients/{patient_id}/medications/history", params=params)
    
    return f"Medication History ({start_date} to {end_date}):\n{meds}"

@mcp.resource("medications://statistics/{patient_name}")
async def get_medication_statistics(patient_name: str) -> str:
    """Resource: Returns adherence and prescription statistics."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    # Endpoint: GET /patients/{patientId}/medications/statistics
    stats = await dbops.get(f"/patients/{patient_id}/medications/statistics")
    return f"Medication Stats for {patient_name}:\n{stats}"

# --- MCP Tools (POST/PUT/PATCH) ---

@mcp.tool()
async def prescribe_medication(
    patient_name: str, 
    medication_name: str, 
    dosage: str, 
    frequency: str, 
    start_date: str, 
    instructions: str
) -> str:
    """Tool: Prescribes a NEW medication to a patient."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    payload = {
        "medicationName": medication_name,
        "dosage": dosage,
        "frequency": frequency,
        "startDate": start_date,
        "instructions": instructions
    }

    try:
        # Endpoint: POST /patients/{patientId}/medications
        await dbops.post(f"/patients/{patient_id}/medications", data=payload)
        return f"✅ Prescribed {medication_name} to {patient_name}."
    except Exception as e:
        return f"❌ Failed to prescribe: {str(e)}"

@mcp.tool()
async def update_prescription(
    patient_name: str,
    medication_name: str,
    new_dosage: Optional[str] = None,
    new_frequency: Optional[str] = None
) -> str:
    """Tool: Updates dosage or frequency for an existing medication."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."
    
    med_id = await resolve_medication_id(patient_id, medication_name)
    if not med_id: return f"Error: Active medication '{medication_name}' not found for this patient."

    payload = {}
    if new_dosage: payload["dosage"] = new_dosage
    if new_frequency: payload["frequency"] = new_frequency

    try:
        # Endpoint: PUT /patients/{patientId}/medications/{medicationId}
        await dbops.put(f"/patients/{patient_id}/medications/{med_id}", data=payload)
        return f" Updated {medication_name} prescription details."
    except Exception as e:
        return f" Update failed: {str(e)}"

@mcp.tool()
async def discontinue_medication(
    patient_name: str,
    medication_name: str,
    reason: str
) -> str:
    """Tool: Stops a medication (Discontinue)."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    med_id = await resolve_medication_id(patient_id, medication_name)
    if not med_id: return f"Error: Medication '{medication_name}' not found."

    try:
        # Endpoint: POST /patients/{patientId}/medications/{medicationId}/discontinue
        await dbops.post(f"/patients/{patient_id}/medications/{med_id}/discontinue", data={"reason": reason})
        return f" Discontinued {medication_name}. Reason: {reason}"
    except Exception as e:
        return f" Failed to discontinue: {str(e)}"

@mcp.tool()
async def add_medication_refill(
    patient_name: str,
    medication_name: str,
    refill_date: str,
    quantity: int,
    pharmacy: str
) -> str:
    """Tool: Logs a refill for a specific medication."""
    patient_id = await resolve_patient_id(patient_name)
    if not patient_id: return f"Error: Patient '{patient_name}' not found."

    med_id = await resolve_medication_id(patient_id, medication_name)
    if not med_id: return f"Error: Medication '{medication_name}' not found."

    payload = {
        "refillDate": refill_date,
        "quantity": quantity,
        "pharmacy": pharmacy
    }

    try:
        # Endpoint: POST /patients/{patientId}/medications/{medicationId}/refill
        await dbops.post(f"/patients/{patient_id}/medications/{med_id}/refill", data=payload)
        return f" Refill added for {medication_name} at {pharmacy}."
    except Exception as e:
        return f" Failed to add refill: {str(e)}"