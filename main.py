from fastmcp import FastMCP
from tools.doctors import resolve_doctor_id
from dependencies import dbops

mcp = FastMCP("CareBot-Operations")

@mcp.tool()
async def book_appointment(doctor_name: str, patient_name: str, date: str):
    """Books an appointment using human names instead of IDs."""
    # 1. Translate Name to ID (Context Enrichment)
    doc_id = await resolve_doctor_id(doctor_name)
    
    if not doc_id:
        return f"Could not find doctor: {doctor_name}"

    # 2. Call DBOps (Execution)
    # Note: You'll need a similar resolve_patient_id function
    payload = {"doctor_id": doc_id, "appointment_date": date} 
    await dbops.post("/appointments", payload)
    
    return f"Successfully scheduled {patient_name} with {doctor_name}."

if __name__ == "__main__":
    mcp.run()