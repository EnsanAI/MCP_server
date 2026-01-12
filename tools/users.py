from server import mcp
from dependencies import dbops

@mcp.tool()
async def register_user(email: str, full_name: str, phone: str) -> str:
    """Tool: Registers a new user account."""
    # Simple username logic from client
    username = email.split('@')[0] if '@' in email else full_name.replace(" ", "_").lower()
    
    payload = {
        "email": email,
        "fullName": full_name,
        "phoneNumber": phone,
        "roleId": "patient",
        "username": username,
        "languagePreference": "en"
    }
    try:
        res = await dbops.post("/auth/register", data=payload)
        return f"✅ User Registered. ID: {res.get('id')}"
    except Exception as e:
        return f"Registration failed: {e}"