from server import mcp
from dependencies import dbops

@mcp.tool()
async def join_waitlist(clinic_id: str, patient_id: str, preferred_date: str, notes: str = "") -> str:
    """Tool: Adds a patient to the appointment waitlist."""
    payload = {
        "clinic_id": clinic_id,
        "patient_id": patient_id,
        "preferred_date": preferred_date,
        "notes": notes,
        "status": "active"
    }
    try:
        res = await dbops.post("/db/waitlist/add", data=payload)
        return f" Added to waitlist. ID: {res.get('id')}"
    except Exception as e:
        return f"Failed to join waitlist: {e}"

@mcp.resource("waitlist://all")
async def get_waitlist() -> str:
    """Resource: View the active waitlist."""
    data = await dbops.get("/db/waitlist")
    return str(data)