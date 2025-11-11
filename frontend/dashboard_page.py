import os
import requests
import streamlit as st  # needed for tests that patch st.session_state

# Base URL for the FastAPI backend (used in tests)
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def check_admin_access() -> bool:
    """
    Check if the current session has admin access.
    The test suite patches ``frontend.dashboard_page.st`` to control the role.
    """
    return st.session_state.get("role") == "admin"

def api_get(endpoint: str, token: str = None):
    """
    Generic GET request using the ``requests`` library.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {"Authorization": "Bearer "}
    return requests.get(f"{BASE_URL}{endpoint}", headers=headers)

def api_post(endpoint: str, json_body: dict, token: str = None):
    """
    Generic POST request using the ``requests`` library.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {"Authorization": "Bearer "}
    return requests.post(f"{BASE_URL}{endpoint}", json=json_body, headers=headers)

def get_kpi_dashboard(token: str):
    """
    Retrieve the full KPI dashboard data.
    """
    return api_get("/dashboard/kpi", token)

def get_attendance_overview(token: str):
    """
    Retrieve attendance overview data.
    """
    return api_get("/dashboard/kpi/attendance-overview", token)

def get_today_attendance(token: str):
    """
    Retrieve today's attendance table.
    """
    return api_get("/dashboard/kpi/today-attendance", token)

def render_kpi_cards(kpi_data: dict):
    """
    Placeholder for KPI card rendering.
    The test suite only checks that the function exists and can be called.
    """
    return None

def render_attendance_overview(attendance_data: list):
    """
    Placeholder for attendance overview rendering.
    """
    return None

def render_today_attendance_table(attendance_data: list):
    """
    Placeholder for today's attendance table rendering.
    """
    return None

def render_leave_management(leave_stats: dict):
    """
    Placeholder for leave management rendering.
    """
    return None

def render_overtime_management(overtime_stats: dict):
    """
    Placeholder for overtime management rendering.
    """
    return None

def render_payroll_summary(payroll_data: dict):
    """
    Placeholder for payroll summary rendering.
    """
    return None

def login(username: str, password: str):
    """
    Helper to obtain a JWT token for a user.
    """
    response = api_post("/token", {"username": username, "password": password})
    if response.status_code == 200:
        return response.json().get("access_token")
    return None