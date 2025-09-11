import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Load backend URL from environment variable with fallback
backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")

def api_get(endpoint: str):
    """Make authenticated GET request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.get(f"{backend_url}{endpoint}", headers=headers)

def api_post(endpoint: str, json_data: dict):
    """Make authenticated POST request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.post(f"{backend_url}{endpoint}", json=json_data, headers=headers)

def render_employee_dashboard():
    """Render the employee dashboard with personal metrics"""
    st.title("Employee Dashboard")
    
    # Check if user is logged in
    if "token" not in st.session_state:
        st.error("Please login to access the dashboard")
        return
    
    try:
        # Get personal KPI data
        kpi_response = api_get("/employee-dashboard/kpi")
        
        if kpi_response.status_code != 200:
            st.error("Failed to load dashboard data")
            return
        
        kpi_data = kpi_response.json()
        
        # Create KPI cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Days Worked This Month",
                kpi_data["days_worked_this_month"],
                delta=None,
                help="Number of days you've worked this month"
            )
        
        with col2:
            total_overtime = kpi_data["total_overtime_hours_this_month"]
            st.metric(
                "Overtime Hours This Month",
                f"{total_overtime:.1f}",
                delta=None,
                help="Total overtime hours worked this month"
            )
        
        with col3:
            if kpi_data["latest_payslip"]:
                net_pay = kpi_data["latest_payslip"]["net_pay"]
                st.metric(
                    "Latest Net Pay",
                    f"${net_pay:,.2f}",
                    delta=None,
                    help="Net pay from your latest payslip"
                )
            else:
                st.metric(
                    "Latest Net Pay",
                    "$0.00",
                    delta=None,
                    help="No payslip data available"
                )
        
        with col4:
            # Calculate total remaining leave
            total_leave = sum(balance["remaining_balance"] for balance in kpi_data["remaining_leave_balance"])
            st.metric(
                "Remaining Leave",
                f"{total_leave} days",
                delta=None,
                help="Total remaining leave days"
            )
        
        # Attendance Summary Chart
        st.subheader("Attendance Summary - Current Month")
        attendance_response = api_get("/employee-dashboard/attendance-summary")
        
        if attendance_response.status_code == 200:
            attendance_data = attendance_response.json()
            
            if attendance_data:
                # Convert to DataFrame for chart
                df = pd.DataFrame(attendance_data)
                
                # Create bar chart
                st.bar_chart(
                    df,
                    x="date",
                    y="hours_worked",
                    use_container_width=True,
                    height=300
                )
            else:
                st.info("No attendance data available for this month")
        else:
            st.error("Failed to load attendance data")
        
        # Leave Balance by Type
        st.subheader("Leave Balance by Type")
        leave_balance_data = kpi_data["remaining_leave_balance"]
        
        if leave_balance_data:
            # Create cards for each leave type
            cols = st.columns(len(leave_balance_data))
            
            for i, balance in enumerate(leave_balance_data):
                with cols[i]:
                    st.info(
                        f"**{balance['leave_type']}**\n"
                        f"Remaining: {balance['remaining_balance']} days"
                    )
        else:
            st.info("No leave balance data available")
        
        # Personal Attendance Log
        st.subheader("Personal Attendance Log")
        attendance_log_response = api_get("/employee-dashboard/attendance-log")
        
        if attendance_log_response.status_code == 200:
            attendance_log_data = attendance_log_response.json()
            
            if attendance_log_data:
                df = pd.DataFrame(attendance_log_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No attendance log data available")
        else:
            st.error("Failed to load attendance log data")
        
        # Personal Leave Request History
        st.subheader("Personal Leave Request History")
        leave_history_response = api_get("/employee-dashboard/leave-history")
        
        if leave_history_response.status_code == 200:
            leave_history_data = leave_history_response.json()
            
            if leave_history_data:
                df = pd.DataFrame(leave_history_data)
                # Format the dataframe for better display
                df_display = df[["date_from", "date_to", "leave_type", "days_requested", "status", "approver"]]
                df_display.columns = ["From", "To", "Type", "Days", "Status", "Approver"]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No leave request history available")
        else:
            st.error("Failed to load leave request history")
        
        # Personal Overtime Request History
        st.subheader("Personal Overtime Request History")
        overtime_history_response = api_get("/employee-dashboard/overtime-history")
        
        if overtime_history_response.status_code == 200:
            overtime_history_data = overtime_history_response.json()
            
            if overtime_history_data:
                df = pd.DataFrame(overtime_history_data)
                # Format the dataframe for better display
                df_display = df[["date", "hours_requested", "reason", "status", "approver"]]
                df_display.columns = ["Date", "Hours", "Reason", "Status", "Approver"]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No overtime request history available")
        else:
            st.error("Failed to load overtime request history")
        
        # Personal Payroll History
        st.subheader("Personal Payroll History")
        payroll_history_response = api_get("/employee-dashboard/payroll-history")
        
        if payroll_history_response.status_code == 200:
            payroll_history_data = payroll_history_response.json()
            
            if payroll_history_data:
                df = pd.DataFrame(payroll_history_data)
                # Format the dataframe for better display
                df_display = df[["cutoff_start", "cutoff_end", "basic_pay", "overtime_pay", "deductions", "net_pay"]]
                df_display.columns = ["Period Start", "Period End", "Basic Pay", "Overtime Pay", "Deductions", "Net Pay"]
                # Format currency columns
                df_display["Basic Pay"] = df_display["Basic Pay"].apply(lambda x: f"${x:,.2f}")
                df_display["Overtime Pay"] = df_display["Overtime Pay"].apply(lambda x: f"${x:,.2f}")
                df_display["Deductions"] = df_display["Deductions"].apply(lambda x: f"${x:,.2f}")
                df_display["Net Pay"] = df_display["Net Pay"].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No payroll history available")
        else:
            st.error("Failed to load payroll history")
        
        # File Leave Request Form
        st.subheader("File Leave Request")
        with st.form("leave_request_form"):
            st.write("Submit a new leave request:")
            
            # Get available leave types
            leave_types_response = api_get("/leave-types/")
            leave_type_options = {}
            
            if leave_types_response.status_code == 200:
                leave_types = leave_types_response.json()
                for leave_type in leave_types:
                    leave_type_options[leave_type['leave_name']] = leave_type['leave_type_id']
            
            if leave_type_options:
                selected_leave_type = st.selectbox("Leave Type", list(leave_type_options.keys()))
                leave_type_id = leave_type_options[selected_leave_type]
                
                date_from = st.date_input("From Date")
                date_to = st.date_input("To Date")
                reason = st.text_area("Reason (optional)", height=60)
                
                submitted = st.form_submit_button("Submit Leave Request")
                
                if submitted:
                    payload = {
                        "leave_type_id": leave_type_id,
                        "date_from": date_from.strftime("%Y-%m-%d"),
                        "date_to": date_to.strftime("%Y-%m-%d"),
                        "reason": reason
                    }
                    
                    response = api_post("/employee-dashboard/leave-requests", payload)
                    
                    if response.status_code == 200:
                        st.success("Leave request submitted successfully!")
                        st.experimental_rerun()
                    else:
                        st.error(f"Error submitting leave request: {response.text}")
            else:
                st.error("Failed to load leave types. Please try again later.")
        
        # File Overtime Request Form
        st.subheader("File Overtime Request")
        with st.form("overtime_request_form"):
            st.write("Submit a new overtime request:")
            
            date = st.date_input("Date")
            hours_requested = st.number_input("Hours Requested", min_value=0.1, max_value=24.0, step=0.5)
            reason = st.text_area("Reason (optional)", height=60)
            
            submitted = st.form_submit_button("Submit Overtime Request")
            
            if submitted:
                payload = {
                    "date": date.strftime("%Y-%m-%d"),
                    "hours_requested": hours_requested,
                    "reason": reason
                }
                
                response = api_post("/employee-dashboard/overtime-requests", payload)
                
                if response.status_code == 200:
                    st.success("Overtime request submitted successfully!")
                    st.experimental_rerun()
                else:
                    st.error(f"Error submitting overtime request: {response.text}")
        
    except Exception as e:
        st.error(f"An error occurred while loading the dashboard: {str(e)}")