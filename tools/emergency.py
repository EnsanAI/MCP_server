from server import mcp
from dependencies import dbops

@mcp.tool()
async def report_emergency(
    clinic_id: str, 
    patient_id: str, 
    description: str, 
    priority: str = "routine"
) -> str:
    """
    Tool: Reports a medical emergency to the dashboard.
    Priority options: 'routine', 'urgent', 'critical'.
    """
    payload = {
        "clinicId": clinic_id,
        "patientId": patient_id,
        "description": description,
        "priority": priority,
        "status": "reported"
    }
    try:
        res = await dbops.post("/emergencies", data=payload)
        return f"🚨 Emergency Reported! ID: {res.get('id')}"
    except Exception as e:
        return f"Failed to report emergency: {e}"

@mcp.resource("emergency://all")
async def get_all_emergencies() -> str:
    """Resource: Lists all active emergencies."""
    data = await dbops.get("/emergencies")
    return str(data)

@mcp.tool()
async def update_emergency_status(emergency_id: str, status: str, notes: str = "") -> str:
    """Tool: Updates emergency status (e.g., 'resolved')."""
    payload = {"status": status}
    if notes: payload["notes"] = notes
    try:
        await dbops.put(f"/emergencies/{emergency_id}/status", data=payload)
        return f"Status updated to {status}."
    except Exception as e:
        return f"Update failed: {e}"