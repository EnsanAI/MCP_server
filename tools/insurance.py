from server import mcp
from dependencies import dbops

async def _get_insurance_providers_logic() -> str:
    """Internal logic to fetch insurance providers."""
    data = await dbops.get("/clinics/insurance/providers")
    return str(data)

@mcp.resource("insurance://providers")
async def get_insurance_providers_resource() -> str:
    """Resource: Lists all accepted insurance providers."""
    return await _get_insurance_providers_logic()

@mcp.tool()
async def get_insurance_providers() -> str:
    """Tool: Lists all accepted insurance providers. Alias for resource."""
    return await _get_insurance_providers_logic()

@mcp.tool()
async def check_procedure_coverage(procedure_id: str, insurance_id: str) -> str:
    """Tool: Checks insurance coverage for a specific procedure."""
    params = {"procedureId": procedure_id, "insuranceId": insurance_id}
    try:
        data = await dbops.get("/clinics/procedures/insurance-coverage", params=params)
        return f"Coverage Details: {data}"
    except Exception as e:
        return f"Check failed: {e}"