from fastmcp import Context
from dependencies import dbops
from typing import Optional
import logging
logger = logging.getLogger("dbops-mcp.revenue")
mcp = Context("revenue")


# --- 1. Comprehensive Revenue (GET /analytics/revenue) ---
@mcp.resource("analytics://revenue/comprehensive/{start_date}/{end_date}")
async def get_comprehensive_revenue(start_date: str, end_date: str) -> str:
    """Resource: Detailed revenue analytics including breakdown."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/revenue", params=params)
    # Output formatting only - Logic stays in DBOps
    return f"Comprehensive Report ({start_date}-{end_date}): {data}"

# --- 2. Revenue Data Only (GET /analytics/revenue/data) ---
@mcp.resource("analytics://revenue/raw/{start_date}/{end_date}")
async def get_revenue_data_only(start_date: str, end_date: str) -> str:
    """Resource: Get raw revenue figures without metadata."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/revenue/data", params=params)
    return f"Raw Revenue Data: {data}"

# --- 3. Monthly Trend (GET /analytics/revenue/monthly-trend) ---
@mcp.resource("analytics://revenue/trend/monthly/{start_date}/{end_date}")
async def get_monthly_trend(start_date: str, end_date: str) -> str:
    """Resource: Monthly revenue breakdown for trend analysis."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/revenue/monthly-trend", params=params)
    
    # Format list for LLM readability
    lines = [f"{item['month']}: ${item['revenue']}" for item in data]
    return "Monthly Trends:\n" + "\n".join(lines)

# --- 4. Daily Trend (GET /analytics/revenue/daily-trend) ---
@mcp.resource("analytics://revenue/trend/daily/{start_date}/{end_date}")
async def get_daily_trend(start_date: str, end_date: str) -> str:
    """Resource: Daily revenue breakdown."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/revenue/daily-trend", params=params)
    
    lines = [f"{item['date']}: ${item['revenue']}" for item in data]
    return "Daily Trends:\n" + "\n".join(lines)

# --- 5. Specialty Performance (GET /analytics/specialty-performance) ---
@mcp.resource("analytics://performance/specialty/{start_date}/{end_date}")
async def get_specialty_performance(start_date: str, end_date: str) -> str:
    """Resource: Revenue performance by dental specialty."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/specialty-performance", params=params)
    
    lines = [f"• {s['specialty']}: ${s['revenue']} ({s['appointments']} apps)" for s in data]
    return "Specialty Performance:\n" + "\n".join(lines)

# --- 6. Top Doctors (GET /analytics/top-doctors) ---
@mcp.resource("analytics://performance/doctors/{start_date}/{end_date}")
async def get_top_doctors(start_date: str, end_date: str) -> str:
    """Resource: Doctor ranking by revenue."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/top-doctors", params=params)
    
    lines = [f"#{i+1} {d['name']}: ${d['revenue']} ({d['appointmentCount']} apps)" for i, d in enumerate(data)]
    return "Top Doctors:\n" + "\n".join(lines)

# --- 7. Dashboard Summary (GET /analytics/dashboard) ---
@mcp.resource("analytics://dashboard/summary/{start_date}/{end_date}")
async def get_dashboard_summary(start_date: str, end_date: str) -> str:
    """Resource: High-level executive dashboard summary."""
    params = {"startDate": start_date, "endDate": end_date}
    data = await dbops.get("/analytics/dashboard", params=params)
    
    s = data.get('summary', {})
    return (f"Dashboard ({start_date}-{end_date}):\n"
            f"Active Patients: {s.get('activePatients')}\n"
            f"New Patients: {s.get('newPatientsThisMonth')}\n"
            f"Future Appts: {s.get('upcomingAppointments')}")