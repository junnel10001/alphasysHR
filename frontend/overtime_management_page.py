"""
Overtime Management Frontend Page

Streamlit components for comprehensive overtime management with forms, tables, and analytics.
"""

import streamlit as st
import requests
import pandas as pd
import datetime
from typing import Dict, Any, List, Optional
import json

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

def api_put(endpoint: str, json_data: dict):
    """Make API PUT request with authentication."""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.put(f"{backend_url}{endpoint}", json=json_data, headers=headers)

def api_delete(endpoint: str):
    """Make API DELETE request with authentication."""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.delete(f"{backend_url}{endpoint}", headers=headers)

def check_admin_access():
    """Check if current user has admin access."""
    return st.session_state.get("role") == "admin"

def check_employee_access():
    """Check if current user has employee access."""
    return st.session_state.get("role") in ["employee", "admin"]

def format_date(date_str: str) -> str:
    """Format date string for display."""
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d-%b-%Y")
    except:
        return date_str

def get_status_color(status: str) -> str:
    """Get color for status badge."""
    status_colors = {
        "Pending": "orange",
        "Approved": "green",
        "Rejected": "red"
    }
    return status_colors.get(status, "gray")

def render_status_badge(status: str) -> str:
    """Render status badge with color."""
    color = get_status_color(status)
    return f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{status}</span>'

def render_overtime_request_form():
    """Render overtime request submission form."""
    st.subheader("File Overtime Request")
    
    with st.form("overtime_request_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.date.today())
        
        with col2:
            hours_requested = st.number_input(
                "Hours Requested", 
                min_value=0.1, 
                max_value=24.0, 
                step=0.5,
                value=1.0
            )
        
        reason = st.text_area(
            "Reason (optional)", 
            height=60, 
            help="Provide a brief reason for the overtime request"
        )
        
        submitted = st.form_submit_button("Submit Overtime Request")
        
        if submitted:
            payload = {
                "date": date.strftime("%Y-%m-%d"),
                "hours_requested": hours_requested,
                "reason": reason
            }
            
            try:
                response = api_post("/overtime/", payload)
                if response.status_code == 200:
                    # Log activity
                    try:
                        activity_payload = {
                            "action": "overtime_request_created",
                            "resource": "overtime",
                            "resource_id": response.json().get("ot_id"),
                            "details": {
                                "date": date.strftime("%Y-%m-%d"),
                                "hours_requested": hours_requested,
                                "reason": reason
                            }
                        }
                        activity_response = api_post("/activity/log", activity_payload)
                        if activity_response.status_code != 200:
                            print(f"Warning: Failed to log activity: {activity_response.text}")
                    except Exception as e:
                        print(f"Warning: Failed to log activity: {str(e)}")
                    
                    st.success("Overtime request submitted successfully!")
                    st.experimental_rerun()
                else:
                    st.error(f"Error submitting request: {response.text}")
            except Exception as e:
                st.error(f"Error connecting to server: {str(e)}")

def render_overtime_request_history_table():
    """Render overtime request history table with status display."""
    st.subheader("Overtime Request History")
    
    # Get filter parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Start Date", value=None)
    
    with col2:
        end_date = st.date_input("End Date", value=None)
    
    with col3:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + ["Pending", "Approved", "Rejected"]
        )
    
    # Build filter parameters
    filter_params = {}
    if start_date:
        filter_params["start_date"] = start_date.strftime("%Y-%m-%d")
    if end_date:
        filter_params["end_date"] = end_date.strftime("%Y-%m-%d")
    if status_filter != "All":
        filter_params["status"] = status_filter
    
    try:
        # Get overtime requests
        if check_admin_access():
            # Admin can see all requests
            response = api_get("/overtime/")
        else:
            # Employee can only see their own requests
            response = api_get(f"/overtime/user/{st.session_state.get('user_id', 1)}")
        
        if response.status_code == 200:
            overtime_requests = response.json()
            
            if not overtime_requests:
                st.info("No overtime requests found.")
                return
            
            # Create DataFrame
            df = pd.DataFrame(overtime_requests)
            
            # Format the data for display
            df_display = df[["ot_id", "date", "hours_requested", "reason", "status"]].copy()
            df_display.columns = ["ID", "Date", "Hours", "Reason", "Status"]
            
            # Format date and status
            df_display["Date"] = df_display["Date"].apply(format_date)
            df_display["Status"] = df_display["Status"].apply(render_status_badge)
            
            # Display table
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.Column(
                        "Status",
                        help="Current status of the overtime request",
                        width="100"
                    )
                }
            )
            
            # Add action buttons for managers
            if check_admin_access():
                st.write("### Actions")
                for idx, row in df.iterrows():
                    ot_id = row['ot_id']
                    status = row['status']
                    
                    if status == "Pending":
                        col1, col2, col3 = st.columns([1, 1, 1])
                        
                        with col1:
                            st.write(f"**Request #{ot_id}**")
                        
                        with col2:
                            if st.button("Approve", key=f"approve_{ot_id}"):
                                approve_response = api_post(f"/overtime/{ot_id}/approve", {})
                                if approve_response.status_code == 200:
                                    # Log activity
                                    try:
                                        activity_payload = {
                                            "action": "overtime_request_approved",
                                            "resource": "overtime",
                                            "resource_id": ot_id,
                                            "details": {
                                                "status": "Approved",
                                                "approved_by": st.session_state.get("user_id"),
                                                "approved_by_name": st.session_state.get("username", "Unknown")
                                            }
                                        }
                                        activity_response = api_post("/activity/log", activity_payload)
                                        if activity_response.status_code != 200:
                                            print(f"Warning: Failed to log activity: {activity_response.text}")
                                    except Exception as e:
                                        print(f"Warning: Failed to log activity: {str(e)}")
                                    
                                    st.success("Overtime request approved!")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Error: {approve_response.text}")
                        
                        with col3:
                            if st.button("Reject", key=f"reject_{ot_id}"):
                                reject_response = api_post(f"/overtime/{ot_id}/reject", {})
                                if reject_response.status_code == 200:
                                    # Log activity
                                    try:
                                        activity_payload = {
                                            "action": "overtime_request_rejected",
                                            "resource": "overtime",
                                            "resource_id": ot_id,
                                            "details": {
                                                "status": "Rejected",
                                                "rejected_by": st.session_state.get("user_id"),
                                                "rejected_by_name": st.session_state.get("username", "Unknown")
                                            }
                                        }
                                        activity_response = api_post("/activity/log", activity_payload)
                                        if activity_response.status_code != 200:
                                            print(f"Warning: Failed to log activity: {activity_response.text}")
                                    except Exception as e:
                                        print(f"Warning: Failed to log activity: {str(e)}")
                                    
                                    st.success("Overtime request rejected!")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Error: {reject_response.text}")
            
        else:
            st.error("Failed to fetch overtime requests.")
            st.error(f"Error: {response.text}")
            
    except Exception as e:
        st.error(f"Error loading overtime requests: {str(e)}")

def render_overtime_statistics():
    """Render overtime statistics and analytics."""
    st.subheader("Overtime Statistics")
    
    try:
        # Get overtime statistics
        response = api_get("/overtime/stats/summary")
        
        if response.status_code == 200:
            stats = response.json()
            
            # Create statistics cards
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Pending",
                    stats.get("pending", 0),
                    delta=None,
                    delta_color="normal"
                )
            
            with col2:
                st.metric(
                    "Approved",
                    stats.get("approved", 0),
                    delta=None,
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "Rejected",
                    stats.get("rejected", 0),
                    delta=None,
                    delta_color="normal"
                )
            
            # Create trend chart
            st.write("### Overtime Trends")
            
            # Get last 30 days of overtime data
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=30)
            
            trend_data = {
                "Date": [],
                "Pending": [],
                "Approved": [],
                "Rejected": []
            }
            
            # Generate trend data (in a real app, this would come from the API)
            for i in range(30):
                current_date = start_date + datetime.timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")
                
                trend_data["Date"].append(date_str)
                trend_data["Pending"].append(0)  # Placeholder data
                trend_data["Approved"].append(0)  # Placeholder data
                trend_data["Rejected"].append(0)  # Placeholder data
            
            # Create DataFrame for chart
            df_trend = pd.DataFrame(trend_data)
            df_trend['Date'] = pd.to_datetime(df_trend['Date'])
            
            # Create line chart
            st.line_chart(
                df_trend,
                x="Date",
                y=["Pending", "Approved", "Rejected"],
                use_container_width=True,
                height=300
            )
            
        else:
            st.error("Failed to fetch overtime statistics.")
            st.error(f"Error: {response.text}")
            
    except Exception as e:
        st.error(f"Error loading overtime statistics: {str(e)}")

def render_overtime_analytics():
    """Render overtime analytics with charts."""
    st.subheader("Overtime Analytics")
    
    try:
        # Get user's overtime requests for analytics
        if check_admin_access():
            response = api_get("/overtime/")
        else:
            response = api_get(f"/overtime/user/{st.session_state.get('user_id', 1)}")
        
        if response.status_code == 200:
            overtime_requests = response.json()
            
            if not overtime_requests:
                st.info("No overtime data available for analytics.")
                return
            
            # Create DataFrame
            df = pd.DataFrame(overtime_requests)
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Create hours by status chart
            st.write("### Hours by Status")
            
            # Group by status and sum hours
            status_hours = df.groupby('status')['hours_requested'].sum().reset_index()
            
            # Create bar chart
            st.bar_chart(
                status_hours,
                x="status",
                y="hours_requested",
                use_container_width=True
            )
            
            # Create monthly trend chart
            st.write("### Monthly Trend")
            
            # Extract month from date
            df['month'] = df['date'].dt.to_period('M')
            
            # Group by month and sum hours
            monthly_hours = df.groupby('month')['hours_requested'].sum().reset_index()
            monthly_hours['month'] = monthly_hours['month'].astype(str)
            
            # Create line chart
            st.line_chart(
                monthly_hours,
                x="month",
                y="hours_requested",
                use_container_width=True
            )
            
        else:
            st.error("Failed to fetch overtime data for analytics.")
            st.error(f"Error: {response.text}")
            
    except Exception as e:
        st.error(f"Error loading overtime analytics: {str(e)}")

def render_role_based_content():
    """Render content based on user role."""
    if check_admin_access():
        st.title("Overtime Management - Admin View")
        
        # Admin can see all statistics and manage requests
        render_overtime_statistics()
        st.write("---")
        render_overtime_request_history_table()
        st.write("---")
        render_overtime_analytics()
        
    elif check_employee_access():
        st.title("Overtime Management - Employee View")
        
        # Employee can see their own requests and statistics
        render_overtime_request_form()
        st.write("---")
        render_overtime_request_history_table()
        st.write("---")
        render_overtime_analytics()
        
    else:
        st.error("Access denied. Please login to continue.")

def main():
    """Main function to render the overtime management page."""
    # Check if user is logged in
    if "token" not in st.session_state:
        st.error("Please login to access the overtime management page.")
        return
    
    # Check if user has the required role
    if not check_employee_access():
        st.error("Access denied. You don't have permission to view this page.")
        return
    
    # Render role-based content
    render_role_based_content()

if __name__ == "__main__":
    main()