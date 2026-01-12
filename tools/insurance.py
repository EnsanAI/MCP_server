from server import mcp
from dependencies import dbops

@mcp.resource("insurance://providers")
async def get_insurance_providers() -> str:
    """Resource: Lists all accepted insurance providers."""
    data = await dbops.get("/clinics/insurance/providers")
    return str(data)

@mcp.tool()
async def check_procedure_coverage(procedure_id: str, insurance_id: str) -> str:
    """Tool: Checks insurance coverage for a specific procedure."""
    params = {"procedureId": procedure_id, "insuranceId": insurance_id}
    try:
        data = await dbops.get("/clinics/procedures/insurance-coverage", params=params)
        return f"Coverage Details: {data}"
    except Exception as e:
        return f"Check failed: {e}"