from fastmcp import Context
from dependencies import dbops
from tools.models import PreVisitResponseCreate
import logging
from server import mcp
from typing import List, Optional, Dict, Any


logger = logging.getLogger("dbops-mcp.previsit")

# --- Resources ---

@mcp.resource("previsit://all")
async def get_all_previsit_responses() -> str:
    """resoucre: List all submitted pre-visit questionnaires."""
    data = await dbops.get("/previsit-responses")
    return f"Total Responses: {len(data)}\n{data}"

@mcp.resource("previsit://date-range/{start_date}/{end_date}")
async def get_previsit_by_date(start_date: str, end_date: str) -> str:
    """resoucre: Get questionnaires submitted within a date range."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/previsit-responses/date-range", params=params)
    return f"Responses ({start_date} to {end_date}):\n{data}"

# --- Tools ---

@mcp.tool()
async def submit_previsit_response(
    patient_name: str,
    responses: Dict[str, str],
    notes: str = ""
) -> str:
    """
    Tool: Submits a pre-visit questionnaire for a patient's latest appointment.
    """
    # Move this INSIDE the function to prevent the "partially initialized" error
    from tools.appointments import resolve_last_appointment_id
    # Context Enrichment: Auto-link to the last appointment
    appt_id = await resolve_last_appointment_id(patient_name)
    if not appt_id: 
        return f"Error: No recent appointment found for {patient_name} to attach responses to."

    payload = {
        "appointment_id": appt_id,
        "responses": responses,
        "notes": notes,
        "is_complete": True
    }

    try:
        await dbops.post("/previsit-responses", data=payload)
        return f" Pre-visit forms submitted for {patient_name}."
    except Exception as e:
        return f" Submission failed: {str(e)}"