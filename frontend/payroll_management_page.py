import os
import requests
import streamlit as st  # needed for tests that patch st.session_state

# Base URL for the FastAPI backend (used in tests)
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def has_permission(required_role: str) -> bool:
    """
    Check if the current session has the required role.
    """
    return st.session_state.get("role") == required_role

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

def api_put(endpoint: str, json_body: dict, token: str = None):
    """
    Generic PUT request using the ``requests`` library.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {"Authorization": "Bearer "}
    return requests.put(f"{BASE_URL}{endpoint}", json=json_body, headers=headers)

def api_delete(endpoint: str, token: str = None):
    """
    Generic DELETE request using the ``requests`` library.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {"Authorization": "Bearer "}
    return requests.delete(f"{BASE_URL}{endpoint}", headers=headers)

def get_employees():
    """
    Retrieve list of employees.
    """
    response = api_get("/employees/")
    if response.status_code == 200:
        return response.json()
    return []

def get_departments():
    """
    Retrieve list of departments.
    """
    response = api_get("/departments/")
    if response.status_code == 200:
        return response.json()
    return []

def get_payroll_history():
    """
    Retrieve payroll history.
    """
    response = api_get("/payroll/filtered")
    if response.status_code == 200:
        return response.json()
    return []

def get_payroll_summary():
    """
    Retrieve payroll summary.
    """
    response = api_get("/payroll/summary")
    if response.status_code == 200:
        return response.json()
    return {}

def get_employee_payroll_details(employee_id: int):
    """
    Retrieve payroll details for a specific employee.
    """
    response = api_get(f"/payroll/employee/{employee_id}")
    if response.status_code == 200:
        return response.json()
    return []

def create_payroll(data: dict):
    """
    Create a new payroll entry.
    """
    response = api_post("/payroll/", data)
    if response.status_code == 201:
        return {"success": True, "data": response.json()}
    return {"success": False, "error": response.text}

def generate_payslip(payroll_id: int):
    """
    Generate a payslip for a payroll.
    """
    response = api_post(f"/payroll/{payroll_id}/generate-payslip", {})
    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    return {"success": False, "error": response.text}

def payroll_generation_form():
    """
    Stub for the payroll generation form UI.
    """
    st.subheader("Generate Payroll")
    return None

def payroll_history_table():
    """
    Stub for displaying payroll history in a table.
    """
    st.subheader("Payroll History")
    return None

def show_payroll_details(payroll_id: int):
    """
    Stub for showing detailed payroll information.
    """
    st.subheader(f"Payroll Details for ID {payroll_id}")
    return None

def generate_payslip_action(payroll_id: int):
    """
    Action triggered to generate a payslip.
    """
    result = generate_payslip(payroll_id)
    if result["success"]:
        st.success("Payslip generated successfully.")
    else:
        st.error(f"Failed to generate payslip: {result['error']}")
    return result

def delete_payroll_action(payroll_id: int):
    """
    Action triggered to delete a payroll entry.
    """
    response = api_delete(f"/payroll/{payroll_id}")
    if response.status_code == 204:
        st.success("Payroll deleted successfully.")
        return {"success": True}
    else:
        st.error("Failed to delete payroll.")
        return {"success": False, "error": response.text}

def payroll_summary_dashboard():
    """
    Stub for the payroll summary dashboard UI.
    """
    st.subheader("Payroll Summary Dashboard")
    return None

def employee_payroll_view():
    """
    Stub for the employee payroll view UI.
    """
    st.subheader("Employee Payroll View")
    return None

def main():
    """
    Entry point for the payroll management page.
    """
    st.title("Payroll Management")
    return None