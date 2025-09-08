import streamlit as st
import requests
import json

# Load backend URL from env (set in Docker‑Compose)
backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")

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
        return True
    else:
        st.error("Invalid credentials")
        return False

st.title("AlphaSys HR Payroll System")

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

    st.write(f"Welcome, {st.session_state['username']} ({st.session_state['role']})!")
    st.sidebar.header("Navigation")
    st.sidebar.write("Welcome to AlphaSys HR Payroll System!")

    st.sidebar.subheader("Dashboard")
    st.sidebar.button("Employee Dashboard")

    if has_permission("admin"):
        st.sidebar.subheader("Administration")
        st.sidebar.button("Manage Users")
        st.sidebar.button("Configure Payroll")

    st.header("Admin/HR Dashboard")
    st.write("Welcome to the Admin/HR Dashboard!")

    # ... (rest of UI unchanged for now) ...

    st.write("Main content area.")