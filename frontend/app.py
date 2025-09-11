import streamlit as st
import requests
import json

import os
# Load backend URL from environment variable with fallback
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

def login(username: str, password: str):
    token_endpoint = f"{backend_url}/token"
    data = {"username": username, "password": password}
    response = requests.post(token_endpoint, data=data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        st.session_state["token"] = token
        st.session_state["username"] = username
        # Decode token to get role (in production use proper JWT lib)
        # For simplicity, we just set admin role for the seed user
        st.session_state["role"] = "admin" if username == "junnel@alphasys.com.au" else "employee"
        
        # Log login activity
        try:
            activity_payload = {
                "action": "user_login",
                "resource": "auth",
                "details": {
                    "username": username,
                    "login_time": datetime.datetime.now().isoformat()
                }
            }
            requests.post(f"{backend_url}/activity/log", json=activity_payload)
        except Exception as e:
            print(f"Warning: Failed to log login activity: {str(e)}")
            
        return True
    else:
        st.error("Invalid credentials")
        return False

import streamlit as st
import requests
import json
import datetime

# Load backend URL from env (set in Docker‑Compose)
# Retrieve backend URL from Streamlit secrets if available.
# If the secrets file is missing (common in test environments), fall back
# to a default localhost URL so the module can be imported without error.
try:
    # Retrieve backend URL from Streamlit secrets if available.
    # If the secrets file is missing (common in test environments), fall back
    # to a default localhost URL so the module can be imported without error.
    try:
        backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")
    except Exception:  # pragma: no cover
        backend_url = "http://localhost:8000"
except Exception:  # pragma: no cover
    backend_url = "http://localhost:8000"

# This appears to be a duplicate function, so we'll keep it as is

def api_get(endpoint: str):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.get(f"{backend_url}{endpoint}", headers=headers)

def api_post(endpoint: str, json_data: dict):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.post(f"{backend_url}{endpoint}", json=json_data, headers=headers)

def employee_page():
    st.header("Employees")
    # List employees
    resp = api_get("/employees/")
    if resp.status_code == 200:
        employees = resp.json()
        for emp in employees:
            st.write(f"{emp['user_id']}: {emp.get('first_name','')} {emp.get('last_name','')} ({emp['email']})")
    else:
        st.error("Failed to fetch employees")
    # Add new employee
    st.subheader("Add New Employee")
    with st.form("add_employee"):
        username = st.text_input("Username (email)")
        password = st.text_input("Password", type="password")
        first_name = st.text_input("First name")
        last_name = st.text_input("Last name")
        email = st.text_input("Email")
        hourly_rate = st.number_input("Hourly Rate", min_value=0.0, step=0.1)
        submitted = st.form_submit_button("Create")
        if submitted:
            payload = {
                "username": username,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "hourly_rate": hourly_rate,
                "role": "employee"
            }
            r = api_post("/employees/", payload)
            if r.status_code == 201:
                st.success("Employee created")
                # Log employee creation activity
                try:
                    activity_payload = {
                        "action": "employee_created",
                        "resource": "employee",
                        "resource_id": r.json().get("user_id"),
                        "details": {
                            "username": username,
                            "created_by": st.session_state.get("username", "Unknown"),
                            "first_name": first_name,
                            "last_name": last_name
                        }
                    }
                    requests.post(f"{backend_url}/activity/log", json=activity_payload)
                except Exception as e:
                    print(f"Warning: Failed to log employee creation activity: {str(e)}")
            else:
                st.error(f"Error: {r.text}")

def leave_page():
    st.header("Leave Requests")
    resp = api_get("/leaves/")
    if resp.status_code == 200:
        leaves = resp.json()
        for lv in leaves:
            st.write(f"{lv['leave_id']}: User {lv['user_id']} {lv['status']} from {lv['date_from']} to {lv['date_to']}")
    else:
        st.error("Failed to fetch leaves")
    st.subheader("Create Leave Request")
    with st.form("add_leave"):
        user_id = st.number_input("User ID", min_value=1, step=1)
        leave_type_id = st.number_input("Leave Type ID", min_value=1, step=1)
        date_from = st.date_input("From")
        date_to = st.date_input("To")
        reason = st.text_area("Reason")
        submitted = st.form_submit_button("Create")
        if submitted:
            payload = {
                "user_id": int(user_id),
                "leave_type_id": int(leave_type_id),
                "date_from": str(date_from),
                "date_to": str(date_to),
                "reason": reason
            }
            r = api_post("/leaves/", payload)
            if r.status_code == 201:
                st.success("Leave request created")
            else:
                st.error(f"Error: {r.text}")

def attendance_page():
    st.header("Attendance")
    resp = api_get("/attendance/")
    if resp.status_code == 200:
        records = resp.json()
        for rec in records:
            st.write(f"{rec['attendance_id']}: User {rec['user_id']} on {rec['attendance_date']} - {rec['status']}")
    else:
        st.error("Failed to fetch attendance")
    st.subheader("Add Attendance")
    with st.form("add_attendance"):
        user_id = st.number_input("User ID", min_value=1, step=1)
        att_date = st.date_input("Date")
        time_in = st.time_input("Time In", value=None)
        time_out = st.time_input("Time Out", value=None)
        status = st.selectbox("Status", ["Present", "Late", "Absent"])
        submitted = st.form_submit_button("Create")
        if submitted:
            payload = {
                "user_id": int(user_id),
                "attendance_date": str(att_date),
                "time_in": time_in.isoformat() if time_in else None,
                "time_out": time_out.isoformat() if time_out else None,
                "status": status
            }
            r = api_post("/attendance/", payload)
            if r.status_code == 201:
                st.success("Attendance recorded")
            else:
                st.error(f"Error: {r.text}")

st.title("AlphaSys HR Payroll System")
 
def logout():
    """Logout the current user"""
    try:
        # Log logout activity
        activity_payload = {
            "action": "user_logout",
            "resource": "auth",
            "details": {
                "username": st.session_state.get("username", "Unknown"),
                "logout_time": datetime.datetime.now().isoformat()
            }
        }
        requests.post(f"{backend_url}/activity/log", json=activity_payload)
    except Exception as e:
        print(f"Warning: Failed to log logout activity: {str(e)}")
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
 
if not st.session_state["logged_in"]:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            st.session_state["logged_in"] = True
            st.success("Login successful")
else:
    def has_permission(required_role):
        return st.session_state["role"] == required_role

    # Navigation
    # Add logout button
    if st.sidebar.button("Logout"):
        logout()
    
    if st.session_state["role"] == "admin":
        page = st.sidebar.radio("Navigation", ["Dashboard", "Employees", "Leaves", "Attendance", "Payroll Management", "Overtime Management", "Activity Logging", "Export Management"])
        
        if page == "Dashboard":
            from .dashboard_page import render_dashboard
            render_dashboard()
        elif page == "Employees":
            employee_page()
        elif page == "Leaves":
            leave_page()
        elif page == "Attendance":
            attendance_page()
        elif page == "Payroll Management":
            from .payroll_management_page import main
            main()
        elif page == "Overtime Management":
            from .overtime_management_page import main
            main()
        elif page == "Activity Logging":
            from .activity_logging_page import main
            main()
        elif page == "Export Management":
            from .export_management_page import main
            main()
    else:
        # Employee role - show employee dashboard
        page = st.sidebar.radio("Navigation", ["Employee Dashboard", "Payroll Management", "Overtime Management", "Activity Logging", "Export Management"])
        
        if page == "Employee Dashboard":
            from .employee_dashboard_page import render_employee_dashboard
            render_employee_dashboard()
        elif page == "Payroll Management":
            from .payroll_management_page import main
            main()
        elif page == "Overtime Management":
            from .overtime_management_page import main
            main()
        elif page == "Activity Logging":
            from .activity_logging_page import main
            main()
        elif page == "Export Management":
            from .export_management_page import main
            main()