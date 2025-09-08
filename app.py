import streamlit as st
import bcrypt

# Authentication
st.title("AlphaSys HR Payroll System")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin":
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Replace with proper database lookup and password verification
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = "admin"  # Placeholder role
                st.success("Login successful!")
            else:
                st.error("Invalid credentials.")
        else:
            st.error("Invalid credentials.")
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

    st.subheader("User Management")
    st.button("Add New User")
    st.button("Edit Existing User")
    st.button("Delete User")

    st.subheader("Payroll Configuration")
    st.button("Update Salary Rates")
    st.button("Configure Deductions")

    st.header("Attendance")

    if st.button("Time In"):
        st.write("Time In recorded!")

    if st.button("Time Out"):
        st.write("Time Out recorded!")

    st.header("Overtime Management")
    hours_requested = st.number_input("Enter Overtime Hours", min_value=0.0, step=0.5)
    reason = st.text_input("Reason for Overtime")

    if st.button("Request Overtime"):
        st.write(f"Overtime request submitted for {hours_requested} hours - Reason: {reason}")

    st.header("Payroll Engine")
    st.write("Payroll engine implementation placeholder.  Requires database integration and calculation logic.")

    st.subheader("Export Reports")
    st.button("Export Attendance Data (CSV)")
