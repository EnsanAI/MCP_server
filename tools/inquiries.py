from server import mcp
from dependencies import dbops

@mcp.tool()
async def create_medical_inquiry(patient_id: str, subject: str, message: str, type: str = "medical") -> str:
    """Tool: Creates a support ticket/inquiry for a patient."""
    payload = {
        "patientId": patient_id, 
        "subject": subject, 
        "message": message, 
        "type": type
    }
    try:
        res = await dbops.post("/inquiries", data=payload)
        return f"✅ Inquiry Created. ID: {res.get('id')}"
    except Exception as e:
        return f"Creation failed: {e}"

@mcp.tool()
async def mark_inquiry_answered(inquiry_id: str, answer_text: str, user_id: str) -> str:
    """Tool: Marks an inquiry as answered."""
    payload = {"answerText": answer_text, "answeredByUserId": user_id}
    try:
        await dbops.patch(f"/inquiries/{inquiry_id}/answer", data=payload)
        return "✅ Inquiry marked as answered."
    except Exception as e:
        return f"Update failed: {e}"

@mcp.resource("inquiries://list")
async def get_inquiries() -> str:
    """Resource: List all inquiries."""
    data = await dbops.get("/inquiries")
    return str(data)