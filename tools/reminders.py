from fastmcp import Context
from dependencies import dbops
from tools.patients import resolve_patient_by_phone
from tools.models import ReminderBase, MedicationReminderCreate
from typing import List, Optional, Dict, Any
import logging
from server import mcp


logger = logging.getLogger("dbops-mcp.reminders")

# --- MCP resources (GET) ---

@mcp.resource("reminders://medication/pending/{patient_name}")
async def get_pending_med_reminders(patient_name: str) -> str:
    """resource: Returns pending medication reminders for a patient."""
    patient_id = await resolve_patient_by_phone(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    # Per docs: GET /db/reminders/medication/{userId}
    reminders = await dbops.get(f"/db/reminders/medication/{patient_id}")
    
    if not reminders:
        return f"No pending medication reminders for {patient_name}."

    lines = [f"• {r['message']} | Scheduled: {r['send_at']}" for r in reminders]
    return f"Pending Medication for {patient_name}:\n" + "\n".join(lines)

@mcp.resource("reminders://adherence/{patient_name}")
async def get_adherence_stats(patient_name: str) -> str:
    """resource: Returns adherence rate and missed dose statistics."""
    patient_id = await resolve_patient_by_phone(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    stats = await dbops.get(f"/db/reminders/adherence/{patient_id}")
    return (f"Adherence Report for {patient_name}:\n"
            f"Rate: {stats['adherence_rate']}%\n"
            f"Taken: {stats['taken']} | Missed: {stats['missed']}\n"
            f"Total Reminders: {stats['total_reminders']}")

# --- MCP Tools (Actions) ---

@mcp.tool()
async def create_medication_reminder(
    patient_name: str,
    medication: str,
    dosage: str,
    frequency: str,
    times: List[str],
    end_date: str
) -> str:
    """
    Tool: Sets up a recurring medication schedule.
    Example: 'Remind John Doe to take Metformin 500mg twice daily until 2026-01-01'
    """
    patient_id = await resolve_patient_by_phone(patient_name)
    if not patient_id:
        return f"Error: Patient '{patient_name}' not found."

    payload = {
        "userId": patient_id,
        "medicationName": medication,
        "dosage": dosage,
        "frequency": frequency,
        "timingContext": "standard",
        "scheduledTimes": times,
        "endDate": end_date
    }

    try:
        # Per docs: POST /db/reminders/medication
        res = await dbops.post("/db/reminders/medication", data=payload)
        return f" {res['message']} created for {patient_name}."
    except Exception as e:
        return f" Failed to create medication schedule: {str(e)}"

@mcp.tool()
async def log_medication_taken(reminder_id: str, notes: str = "") -> str:
    """Tool: Records that a patient successfully took their dose."""
    try:
        # Per docs: PATCH /db/reminders/adherence/{id}
        await dbops.patch(f"/db/reminders/adherence/{reminder_id}", data={"taken": True, "notes": notes})
        return f" Dose logged for reminder {reminder_id}."
    except Exception as e:
        return f" Logging failed: {str(e)}"