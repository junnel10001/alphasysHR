"""
Dashboard Page

Streamlit components for Admin/HR Dashboard with KPI Cards and Analytics.
"""

import streamlit as st
import requests
import pandas as pd
import datetime
from typing import Dict, Any, List

# Load backend URL from environment variable with fallback
try:
    backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")
except Exception:
    backend_url = "http://localhost:8000"

def api_get(endpoint: str):
    """Make API GET request with authentication."""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.get(f"{backend_url}{endpoint}", headers=headers)

def api_post(endpoint: str, json_data: dict):
    """Make API POST request with authentication."""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.post(f"{backend_url}{endpoint}", json=json_data, headers=headers)

def check_admin_access():
    """Check if current user has admin access."""
    return st.session_state.get("role") == "admin"

def render_kpi_cards(kpi_data: Dict[str, Any]):
    """Render KPI cards with metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Employees Present Today",
            kpi_data.get("employees_present_today", 0),
            delta=None,
            delta_color="normal"
        )
    
    with col2:
        late_absent = kpi_data.get("late_absent_today", {})
        st.metric(
            "Late Today",
            late_absent.get("late", 0),
            delta=None,
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Absent Today",
            late_absent.get("absent", 0),
            delta=None,
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "Pending Leaves",
            kpi_data.get("pending_leave_requests", 0),
            delta=None,
            delta_color="normal"
        )

def render_attendance_overview(attendance_data: List[Dict[str, Any]]):
    """Render attendance overview bar chart."""
    if not attendance_data:
        st.warning("No attendance data available for the last 7 days.")
        return
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame(attendance_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create bar chart
    st.subheader("Attendance Overview (Last 7 Days)")
    
    # Chart data preparation
    chart_data = df.melt(
        id_vars=['date'],
        value_vars=['total', 'present', 'late', 'absent'],
        var_name='status',
        value_name='count'
    )
    
    # Create bar chart
    st.bar_chart(
        chart_data,
        x='date',
        y='count',
        color='status',
        use_container_width=True
    )

def render_today_attendance_table(attendance_data: List[Dict[str, Any]]):
    """Render today's attendance table."""
    if not attendance_data:
        st.warning("No attendance data available for today.")
        return
    
    st.subheader("Today's Attendance")
    
    # Convert to DataFrame
    df = pd.DataFrame(attendance_data)
    
    # Format time columns for display
    df['time_in'] = df['time_in'].apply(
        lambda x: x if x is None else x[:8]  # Show only HH:MM:SS
    )
    df['time_out'] = df['time_out'].apply(
        lambda x: x if x is None else x[:8]  # Show only HH:MM:SS
    )
    
    # Display table
    st.dataframe(
        df[['name', 'email', 'time_in', 'time_out', 'hours_worked', 'status']],
        use_container_width=True,
        hide_index=True
    )

def render_leave_management(leave_stats: Dict[str, int]):
    """Render leave management section with pending requests."""
    st.subheader("Leave Management")
    
    # Display leave stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pending", leave_stats.get("pending", 0))
    with col2:
        st.metric("Approved", leave_stats.get("approved", 0))
    with col3:
        st.metric("Rejected", leave_stats.get("rejected", 0))
    
    # Get pending leave requests
    response = api_get("/leaves/")
    if response.status_code == 200:
        leave_requests = response.json()
        
        # Filter for pending requests
        pending_requests = [lr for lr in leave_requests if lr.get('status') == 'Pending']
        
        if pending_requests:
            st.write("### Pending Leave Requests")
            
            # Create DataFrame for pending requests
            df = pd.DataFrame(pending_requests)
            
            # Display table with action buttons
            for idx, row in df.iterrows():
                with st.expander(f"Leave Request #{row['leave_id']} - {row['user_id']}"):
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.write(f"**User:** {row.get('first_name', '')} {row.get('last_name', '')}")
                        st.write(f"**Type:** {row.get('leave_type_name', '')}")
                        st.write(f"**Dates:** {row.get('date_from', '')} to {row.get('date_to', '')}")
                    
                    with col2:
                        st.write(f"**Reason:** {row.get('reason', 'N/A')}")
                    
                    with col3:
                        st.write("### Actions")
                        
                        # Approve button
                        if st.button("Approve", key=f"approve_leave_{row['leave_id']}"):
                            approve_response = api_post(f"/dashboard/leaves/{row['leave_id']}/approve", {})
                            if approve_response.status_code == 200:
                                st.success("Leave request approved!")
                                st.experimental_rerun()
                            else:
                                st.error(f"Error: {approve_response.text}")
                        
                        # Reject button
                        if st.button("Reject", key=f"reject_leave_{row['leave_id']}"):
                            reject_response = api_post(f"/dashboard/leaves/{row['leave_id']}/reject", {})
                            if reject_response.status_code == 200:
                                st.success("Leave request rejected!")
                                st.experimental_rerun()
                            else:
                                st.error(f"Error: {reject_response.text}")
        else:
            st.info("No pending leave requests.")
    else:
        st.error("Failed to fetch leave requests.")

def render_overtime_management(overtime_stats: Dict[str, int]):
    """Render overtime management section with pending requests."""
    st.subheader("Overtime Management")
    
    # Display overtime stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pending", overtime_stats.get("pending", 0))
    with col2:
        st.metric("Approved", overtime_stats.get("approved", 0))
    with col3:
        st.metric("Rejected", overtime_stats.get("rejected", 0))
    
    # Get pending overtime requests
    response = api_get("/overtime/")
    if response.status_code == 200:
        overtime_requests = response.json()
        
        # Filter for pending requests
        pending_requests = [or_ for or_ in overtime_requests if or_.get('status') == 'Pending']
        
        if pending_requests:
            st.write("### Pending Overtime Requests")
            
            # Create DataFrame for pending requests
            df = pd.DataFrame(pending_requests)
            
            # Display table with action buttons
            for idx, row in df.iterrows():
                with st.expander(f"Overtime Request #{row['ot_id']} - {row['user_id']}"):
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.write(f"**User:** {row.get('first_name', '')} {row.get('last_name', '')}")
                        st.write(f"**Date:** {row.get('date', '')}")
                        st.write(f"**Hours:** {row.get('hours_requested', '')}")
                    
                    with col2:
                        st.write(f"**Reason:** {row.get('reason', 'N/A')}")
                    
                    with col3:
                        st.write("### Actions")
                        
                        # Approve button
                        if st.button("Approve", key=f"approve_overtime_{row['ot_id']}"):
                            approve_response = api_post(f"/dashboard/overtime/{row['ot_id']}/approve", {})
                            if approve_response.status_code == 200:
                                st.success("Overtime request approved!")
                                st.experimental_rerun()
                            else:
                                st.error(f"Error: {approve_response.text}")
                        
                        # Reject button
                        if st.button("Reject", key=f"reject_overtime_{row['ot_id']}"):
                            reject_response = api_post(f"/dashboard/overtime/{row['ot_id']}/reject", {})
                            if reject_response.status_code == 200:
                                st.success("Overtime request rejected!")
                                st.experimental_rerun()
                            else:
                                st.error(f"Error: {reject_response.text}")
        else:
            st.info("No pending overtime requests.")
    else:
        st.error("Failed to fetch overtime requests.")

def render_payroll_summary(payroll_data: Dict[str, Any]):
    """Render payroll summary charts."""
    st.subheader("Payroll Summary")
    
    if not payroll_data or payroll_data.get("total_payrolls", 0) == 0:
        st.info("No payroll data available for the current month.")
        return
    
    # Create summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Payrolls", payroll_data.get("total_payrolls", 0))
    with col2:
        st.metric("Total Basic Pay", f"${payroll_data.get('total_basic_pay', 0):,.2f}")
    with col3:
        st.metric("Total Net Pay", f"${payroll_data.get('total_net_pay', 0):,.2f}")
    
    # Create breakdown chart
    breakdown_data = {
        "Category": ["Basic Pay", "Overtime Pay", "Deductions"],
        "Amount": [
            payroll_data.get("total_basic_pay", 0),
            payroll_data.get("total_overtime_pay", 0),
            payroll_data.get("total_deductions", 0)
        ]
    }
    
    df_breakdown = pd.DataFrame(breakdown_data)
    
    st.bar_chart(
        df_breakdown,
        x="Category",
        y="Amount",
        use_container_width=True
    )

def render_dashboard():
    """Main dashboard rendering function."""
    if not check_admin_access():
        st.error("Access denied. Admin privileges required.")
        return
    
    st.title("Admin/HR Dashboard")
    
    # Get all dashboard data
    response = api_get("/dashboard/kpi")
    
    if response.status_code == 200:
        kpi_data = response.json()
        
        # Render KPI cards
        render_kpi_cards(kpi_data)
        
        # Render attendance overview
        render_attendance_overview(kpi_data.get("attendance_overview", []))
        
        # Render today's attendance
        render_today_attendance_table(kpi_data.get("today_attendance", []))
        
        # Render leave management
        render_leave_management(kpi_data.get("leave_stats", {}))
        
        # Render overtime management
        render_overtime_management(kpi_data.get("overtime_stats", {}))
        
        # Render payroll summary
        render_payroll_summary(kpi_data.get("payroll_summary", {}))
        
    else:
        st.error("Failed to fetch dashboard data.")
        st.error(f"Error: {response.text}")

if __name__ == "__main__":
    render_dashboard()