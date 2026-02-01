#!/usr/bin/env python3
"""
MCP Server Test Suite for Docker Environment
Tests all MCP tools against the db-ops service with proper authentication
"""
import asyncio
import sys
import os
from typing import Dict, Any
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dependencies import dbops
from tools.doctors import resolve_doctor_id
from tools.patients import resolve_patient_id
from tools.medication_management import resolve_medication_id

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class MCPTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def print_header(self, text: str):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

    def print_test(self, name: str, status: str, details: str = ""):
        if status == "PASS":
            self.passed += 1
            print(f"{GREEN}✓{RESET} {name} ... {GREEN}PASS{RESET}")
        elif status == "FAIL":
            self.failed += 1
            print(f"{RED}✗{RESET} {name} ... {RED}FAIL{RESET}")
        elif status == "WARN":
            self.warnings += 1
            print(f"{YELLOW}⚠{RESET} {name} ... {YELLOW}WARN{RESET}")

        if details:
            print(f"  → {details}")

    def print_summary(self):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}Passed:{RESET} {self.passed}")
        print(f"{RED}Failed:{RESET} {self.failed}")
        print(f"{YELLOW}Warnings:{RESET} {self.warnings}")
        total = self.passed + self.failed + self.warnings
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")

async def test_environment_config(tester: MCPTester):
    """Test that all environment variables are properly configured"""
    tester.print_header("ENVIRONMENT CONFIGURATION")

    db_ops_url = os.getenv("DB_OPS_URL", "http://db-ops:3000")
    admin_token = os.getenv("ADMIN_ACCESS_TOKEN")

    tester.print_test(
        "DB_OPS_URL configured",
        "PASS" if db_ops_url else "FAIL",
        f"URL: {db_ops_url}"
    )

    tester.print_test(
        "ADMIN_ACCESS_TOKEN configured",
        "PASS" if admin_token else "FAIL",
        "Token is set" if admin_token else "Token is missing!"
    )

async def test_dbops_connection(tester: MCPTester):
    """Test basic connectivity to db-ops service"""
    tester.print_header("DB-OPS CONNECTIVITY")

    try:
        # Test basic connection
        response = await dbops.get("/clinics")
        tester.print_test(
            "Connect to db-ops /clinics endpoint",
            "PASS",
            f"Found {len(response)} clinics"
        )
        return True
    except Exception as e:
        tester.print_test(
            "Connect to db-ops",
            "FAIL",
            f"Error: {str(e)}"
        )
        return False

async def test_patient_tools(tester: MCPTester):
    """Test patient-related MCP tools"""
    tester.print_header("PATIENT TOOLS")

    try:
        # Get all patients
        patients = await dbops.get("/patients")
        tester.print_test(
            "Fetch all patients",
            "PASS",
            f"Found {len(patients)} patients"
        )

        if len(patients) > 0:
            # Test patient resolution
            patient = patients[0]
            patient_name = f"{patient.get('first_name', patient.get('firstName', ''))} {patient.get('last_name', patient.get('lastName', ''))}"

            resolved_id = await resolve_patient_id(patient_name)
            if resolved_id == patient['id']:
                tester.print_test(
                    f"Resolve patient by name: '{patient_name}'",
                    "PASS",
                    f"ID: {resolved_id}"
                )
            else:
                tester.print_test(
                    f"Resolve patient by name: '{patient_name}'",
                    "FAIL",
                    f"Expected {patient['id']}, got {resolved_id}"
                )

            # Test fetching patient details
            patient_details = await dbops.get(f"/patients/{patient['id']}")
            tester.print_test(
                "Fetch patient details",
                "PASS",
                f"Patient: {patient_details.get('first_name')} {patient_details.get('last_name')}"
            )

            # Test fetching patient appointments
            try:
                appointments = await dbops.get(f"/appointments/patient/{patient['id']}")
                tester.print_test(
                    "Fetch patient appointments",
                    "PASS",
                    f"Found {len(appointments)} appointments"
                )
            except Exception as e:
                tester.print_test(
                    "Fetch patient appointments",
                    "WARN",
                    f"No appointments or error: {str(e)}"
                )
        else:
            tester.print_test(
                "Test patient operations",
                "WARN",
                "No patients in database to test with"
            )

    except Exception as e:
        tester.print_test(
            "Patient tools test suite",
            "FAIL",
            f"Error: {str(e)}"
        )

async def test_doctor_tools(tester: MCPTester):
    """Test doctor-related MCP tools"""
    tester.print_header("DOCTOR TOOLS")

    try:
        # Get all doctors
        doctors = await dbops.get("/doctors")
        tester.print_test(
            "Fetch all doctors",
            "PASS",
            f"Found {len(doctors)} doctors"
        )

        if len(doctors) > 0:
            # Test doctor resolution
            doctor = doctors[0]
            doctor_name = f"{doctor.get('first_name', doctor.get('firstName', ''))} {doctor.get('last_name', doctor.get('lastName', ''))}"

            resolved_id = await resolve_doctor_id(doctor_name)
            if resolved_id == doctor['id']:
                tester.print_test(
                    f"Resolve doctor by name: '{doctor_name}'",
                    "PASS",
                    f"ID: {resolved_id}"
                )
            else:
                tester.print_test(
                    f"Resolve doctor by name: '{doctor_name}'",
                    "FAIL",
                    f"Expected {doctor['id']}, got {resolved_id}"
                )

            # Test fetching doctor details
            doctor_details = await dbops.get(f"/doctors/{doctor['id']}")
            tester.print_test(
                "Fetch doctor details",
                "PASS",
                f"Doctor: Dr. {doctor_details.get('first_name')} {doctor_details.get('last_name')}"
            )

            # Test fetching doctor availability
            try:
                availability = await dbops.get(f"/doctors/{doctor['id']}/availability")
                tester.print_test(
                    "Fetch doctor availability",
                    "PASS",
                    f"Found {len(availability)} availability slots"
                )
            except Exception as e:
                tester.print_test(
                    "Fetch doctor availability",
                    "WARN",
                    f"No availability or error: {str(e)}"
                )
        else:
            tester.print_test(
                "Test doctor operations",
                "WARN",
                "No doctors in database to test with"
            )

    except Exception as e:
        tester.print_test(
            "Doctor tools test suite",
            "FAIL",
            f"Error: {str(e)}"
        )

async def test_appointment_tools(tester: MCPTester):
    """Test appointment-related MCP tools"""
    tester.print_header("APPOINTMENT TOOLS")

    try:
        # Get all appointments
        appointments = await dbops.get("/appointments")
        tester.print_test(
            "Fetch all appointments",
            "PASS",
            f"Found {len(appointments)} appointments"
        )

        if len(appointments) > 0:
            appointment = appointments[0]

            # Test fetching single appointment
            appointment_details = await dbops.get(f"/appointments/{appointment['id']}")
            tester.print_test(
                "Fetch appointment details",
                "PASS",
                f"Appointment on {appointment_details.get('appointment_date')}"
            )
        else:
            tester.print_test(
                "Test appointment operations",
                "WARN",
                "No appointments in database to test with"
            )

    except Exception as e:
        tester.print_test(
            "Appointment tools test suite",
            "FAIL",
            f"Error: {str(e)}"
        )

async def test_clinic_tools(tester: MCPTester):
    """Test clinic-related MCP tools"""
    tester.print_header("CLINIC TOOLS")

    try:
        # Get all clinics
        clinics = await dbops.get("/clinics")
        tester.print_test(
            "Fetch all clinics",
            "PASS",
            f"Found {len(clinics)} clinics"
        )

        if len(clinics) > 0:
            clinic = clinics[0]

            # Test fetching single clinic
            clinic_details = await dbops.get(f"/clinics/{clinic['id']}")
            tester.print_test(
                "Fetch clinic details",
                "PASS",
                f"Clinic: {clinic_details.get('name', 'N/A')}"
            )
        else:
            tester.print_test(
                "Test clinic operations",
                "WARN",
                "No clinics in database to test with"
            )

    except Exception as e:
        tester.print_test(
            "Clinic tools test suite",
            "FAIL",
            f"Error: {str(e)}"
        )

async def test_medication_tools(tester: MCPTester):
    """Test medication-related MCP tools"""
    tester.print_header("MEDICATION TOOLS")

    try:
        # Get patients first
        patients = await dbops.get("/patients")

        if len(patients) > 0:
            patient = patients[0]
            patient_id = patient['id']

            # Try to get medications for this patient
            try:
                medications = await dbops.get(f"/patients/{patient_id}/medications")
                tester.print_test(
                    "Fetch patient medications",
                    "PASS",
                    f"Found {len(medications)} medications"
                )

                if len(medications) > 0:
                    med = medications[0]
                    med_name = med.get('medication_name', med.get('name', 'Unknown'))

                    # Test medication resolution
                    resolved_id = await resolve_medication_id(patient_id, med_name)
                    if resolved_id:
                        tester.print_test(
                            f"Resolve medication: '{med_name}'",
                            "PASS",
                            f"ID: {resolved_id}"
                        )
                    else:
                        tester.print_test(
                            f"Resolve medication: '{med_name}'",
                            "WARN",
                            "Could not resolve medication"
                        )
            except Exception as e:
                tester.print_test(
                    "Fetch patient medications",
                    "WARN",
                    f"No medications or error: {str(e)}"
                )
        else:
            tester.print_test(
                "Test medication operations",
                "WARN",
                "No patients in database to test with"
            )

    except Exception as e:
        tester.print_test(
            "Medication tools test suite",
            "FAIL",
            f"Error: {str(e)}"
        )

async def main():
    """Run all MCP tests"""
    tester = MCPTester()

    print(f"{BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         MCP SERVER TEST SUITE - DOCKER ENVIRONMENT        ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    # Run test suites
    await test_environment_config(tester)

    # Only continue if db-ops is reachable
    if await test_dbops_connection(tester):
        await test_clinic_tools(tester)
        await test_patient_tools(tester)
        await test_doctor_tools(tester)
        await test_appointment_tools(tester)
        await test_medication_tools(tester)
    else:
        print(f"\n{RED}Cannot continue tests - db-ops connection failed{RESET}")
        print(f"{YELLOW}Make sure db-ops service is running and healthy{RESET}")

    # Print summary
    tester.print_summary()

    # Cleanup
    await dbops.close()

    # Return exit code based on failures
    return 0 if tester.failed == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
