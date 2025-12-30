# test_mcp.py
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.doctors import resolve_doctor_id
from tools.patients import resolve_patient_id
from tools.medication_management import resolve_medication_id
from dependencies import dbops

async def run_diagnostics():
    print(" Starting DBOps-MCP Diagnostics...")
    
    # 1. Test Connection
    try:
        print("  Testing DBOps Connection...", end=" ")
        users = await dbops.get("/users")
        print(f" OK! (Found {len(users)} users)")
    except Exception as e:
        print(f" FAILED: {str(e)}")
        return

    # 2. Test Doctor Enrichment (Name -> ID)
    # REPLACE 'Dr. John Doe' with a REAL name from your DB
    test_doc_name = "John Doe" 
    print(f"  Resolving Doctor '{test_doc_name}'...", end=" ")
    doc_id = await resolve_doctor_id(test_doc_name)
    if doc_id:
        print(f" OK! (UUID: {doc_id})")
    else:
        print("  Warning: Doctor not found (Check the name in your DB)")

    # 3. Test Patient Enrichment (Name -> ID)
    # REPLACE 'Jane Smith' with a REAL name from your DB
    test_patient_name = "Jane Smith"
    print(f"  Resolving Patient '{test_patient_name}'...", end=" ")
    pat_id = await resolve_patient_id(test_patient_name)
    if pat_id:
        print(f" OK! (UUID: {pat_id})")
        
        # 4. Test Medication Linkage (Only if patient found)
        print(f"  Checking Medications for Patient...", end=" ")
        med_id = await resolve_medication_id(pat_id, "Metformin")
        if med_id:
            print(f" OK! Found Metformin (UUID: {med_id})")
        else:
            print("  No 'Metformin' found (Expected if not prescribed)")
    else:
        print("  Warning: Patient not found (Check the name in your DB)")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())