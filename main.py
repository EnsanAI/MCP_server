from fastmcp import FastMCP
from tools.doctors import (
    list_all_doctors_resource, 
    get_doctor_availability_resource,
    add_availability_tool,
    resolve_doctor_id
)
# main.py updates
from tools.patients import (
    get_patient_summary_resource,
    get_patient_appointments_resource,
    create_patient_tool
)

# main.py updates
from tools.appointments import (
    get_doctor_appointments,
    book_appointment,
    cancel_appointment
)
from tools.reminders import (
    get_pending_med_reminders,
    get_adherence_stats,
    create_medication_reminder,
    log_medication_taken
)
from tools.medication_management import (
    get_all_medications,
    get_active_medications,
    get_medication_history,
    get_medication_statistics,
    prescribe_medication,
    update_prescription,
    discontinue_medication,
    add_medication_refill
)
from tools.revenue import (
    get_comprehensive_revenue,
    get_revenue_data_only,
    get_monthly_trend,
    get_daily_trend,
    get_specialty_performance,
    get_top_doctors,
    get_dashboard_summary
)
from tools.clinical import (
    get_appointment_soap_notes,
    get_latest_soap_note,
    get_soap_note_history,
    create_soap_note,
    update_soap_note,
    version_soap_note,
    get_active_treatment_plans,
    get_treatment_plan_history,
    get_plan_by_appointment,
    create_treatment_plan,
    update_treatment_plan,
    discontinue_treatment_plan
)
from tools.previsit import (
    get_all_previsit_responses,
    get_previsit_by_date,
    submit_previsit_response
)
from tools.clinic_management import (
    get_all_clinics_resource,
    get_clinic_details
)
mcp = FastMCP("CareBot-DBOps-MCP")

# --- Doctors Family Registration ---
mcp.resource("doctors://list", list_all_doctors_resource)
mcp.resource("doctors://availability/{doctor_name}/{date}", get_doctor_availability_resource)
mcp.tool()(add_availability_tool)

# --- Patient Family Registration ---
mcp.resource("patients://summary/{name}", get_patient_summary_resource)
mcp.resource("patients://history/{name}", get_patient_appointments_resource)
mcp.tool()(create_patient_tool)
# --- Appointment Family Registration ---
mcp.resource("appointments://doctor/{doctor_name}", get_doctor_appointments)
mcp.tool()(book_appointment)
mcp.tool()(cancel_appointment)
# --- Reminder Family Registration ---
mcp.resource("reminders://medication/pending/{patient_name}", get_pending_med_reminders)
mcp.resource("reminders://adherence/{patient_name}", get_adherence_stats)
mcp.tool()(create_medication_reminder)
mcp.tool()(log_medication_taken)
# --- Medication Family Registration ---
mcp.resource("medications://all/{patient_name}", get_all_medications)
mcp.resource("medications://active/{patient_name}", get_active_medications)
mcp.resource("medications://history/{patient_name}/{start_date}/{end_date}", get_medication_history)
mcp.resource("medications://statistics/{patient_name}", get_medication_statistics)

mcp.tool()(prescribe_medication)
mcp.tool()(update_prescription)
mcp.tool()(discontinue_medication)
mcp.tool()(add_medication_refill)
# --- Revenue Family Registration ---
mcp.resource("analytics://revenue/comprehensive/{start_date}/{end_date}", get_comprehensive_revenue)
mcp.resource("analytics://revenue/raw/{start_date}/{end_date}", get_revenue_data_only)
mcp.resource("analytics://revenue/trend/monthly/{start_date}/{end_date}", get_monthly_trend)
mcp.resource("analytics://revenue/trend/daily/{start_date}/{end_date}", get_daily_trend)
mcp.resource("analytics://performance/specialty/{start_date}/{end_date}", get_specialty_performance)
mcp.resource("analytics://performance/doctors/{start_date}/{end_date}", get_top_doctors)
mcp.resource("analytics://dashboard/summary/{start_date}/{end_date}", get_dashboard_summary)
# --- SOAP Notes Family ---
mcp.resource("clinical://soap/all/{appointment_id}", get_appointment_soap_notes)
mcp.resource("clinical://soap/latest/{patient_name}", get_latest_soap_note)
mcp.resource("clinical://soap/history/{appointment_id}", get_soap_note_history)

mcp.tool()(create_soap_note)
mcp.tool()(update_soap_note)
mcp.tool()(version_soap_note)

# --- Treatment Plans Family ---
mcp.resource("clinical://plans/active/{patient_name}", get_active_treatment_plans)
mcp.resource("clinical://plans/history/{patient_name}", get_treatment_plan_history)
mcp.resource("clinical://plans/appointment/{appointment_id}", get_plan_by_appointment)

mcp.tool()(create_treatment_plan)
mcp.tool()(update_treatment_plan)
mcp.tool()(discontinue_treatment_plan)
# --- Pre-visit Family ---
mcp.resource("previsit://all", get_all_previsit_responses)
mcp.resource("previsit://date-range/{start_date}/{end_date}", get_previsit_by_date)
mcp.tool()(submit_previsit_response)

# --- Clinic Management Family ---
mcp.resource("clinics://all", get_all_clinics_resource)
mcp.resource("clinics://details/{clinic_id}", get_clinic_details)

# --- JARVIS Pattern: Capability Search(My logic)---
@mcp.tool()
async def search_staff_tools(query: str) -> str:
    """Dynamically identifies relevant staff/doctor tools based on intent."""
    catalog = {
        "check availability": "doctors://availability/{name}/{date}",
        "list staff": "doctors://list",
        "update schedule": "add_availability_tool"
    }
    # Simple semantic match logic
    results = [f"Match: {k} -> Use {v}" for k, v in catalog.items() if query.lower() in k]
    return "\n".join(results) if results else "No specific staff tool matched. Try 'list staff'."

if __name__ == "__main__":
    mcp.run()

if __name__ == "__main__":
    mcp.run()