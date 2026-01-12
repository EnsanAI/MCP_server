import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client

# Configuration
MCP_URL = "http://localhost:8000/sse"

async def run_tests():
    print(f"🔌 Connecting to CareBot MCP at {MCP_URL}...")
    
    try:
        async with sse_client(MCP_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # --- 1. Registry Scan ---
                print("\n📋 Scanning Tool Registry...")
                tools_response = await session.list_tools()
                tool_names = [t.name for t in tools_response.tools]
                
                # The Critical List (New + Core)
                checklist = {
                    "Emergency": "report_emergency",
                    "Insurance": "check_procedure_coverage",
                    "Inquiries": "create_medical_inquiry",
                    "Waitlist": "join_waitlist",
                    "Communication": "log_communication",
                    "Smart Patient": "resolve_patient_by_phone",
                    "Procedures": "get_procedure_guidelines"
                }
                
                passed = 0
                for category, tool in checklist.items():
                    if tool in tool_names:
                        print(f"   ✅ {category}: Found '{tool}'")
                        passed += 1
                    else:
                        print(f"   ❌ {category}: MISSING '{tool}'")
                
                if passed < len(checklist):
                    print(f"\n⚠️ Missing {len(checklist) - passed} tools. Check your imports in main.py!")
                    return

                # --- 2. Functional Logic Tests ---
                print("\n🚀 Running Logic Tests...")

                # TEST A: Smart Patient Lookup (Logic Check)
                # We expect this to fail gracefully (because 050... isn't in DB) 
                # but verify the server *tried* the variations.
                print("   [1/3] Testing Smart Phone Logic (+971)...")
                try:
                    res = await session.call_tool("resolve_patient_by_phone", {"phone_number": "0509998888"})
                    print(f"      Result: {res.content[0].text}") 
                except Exception as e:
                    print(f"      ❌ Failed: {e}")

                # TEST B: Emergency Reporting (Integration Check)
                print("   [2/3] Testing Emergency Reporting...")
                try:
                    res = await session.call_tool("report_emergency", {
                        "clinic_id": "clinic_1", 
                        "patient_id": "pat_123",
                        "description": "Integration Test: Severe pain",
                        "priority": "urgent"
                    })
                    print(f"      Result: {res.content[0].text}")
                except Exception as e:
                    print(f"      ❌ Failed: {e}")

                # TEST C: Communication Log (Async DB Check)
                print("   [3/3] Testing Dashboard Logging...")
                try:
                    res = await session.call_tool("log_communication", {
                        "patient_id": "pat_123",
                        "message": "Test log from verification script",
                        "direction": "outbound"
                    })
                    print(f"      Result: {res.content[0].text}")
                except Exception as e:
                    print(f"      Failed: {e}")

                print("\n✨ Verification Complete!")

    except Exception as e:
        print(f"\n CONNECTION ERROR: {e}")
        print("   -> Is the docker container running? (docker ps)")
        print("   -> Is the URL correct? (http://localhost:8000/sse)")

if __name__ == "__main__":
    asyncio.run(run_tests())