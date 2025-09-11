import streamlit as st
import requests
import json
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Optional

def api_get(endpoint: str):
    """Make authenticated GET request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.get(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", headers=headers)

def has_permission(required_role: str) -> bool:
    """Check if current user has required role"""
    return st.session_state.get("role", "") == required_role

def get_activity_logs(filters: dict = None):
    """Get activity logs with optional filters"""
    try:
        endpoint = "/activity/logs"
        params = {}
        
        if filters:
            if filters.get('limit'):
                params['limit'] = str(filters['limit'])
            if filters.get('offset'):
                params['offset'] = str(filters['offset'])
            if filters.get('user_id'):
                params['user_id'] = str(filters['user_id'])
            if filters.get('action'):
                params['action'] = str(filters['action'])
            if filters.get('start_date'):
                params['start_date'] = str(filters['start_date'])
            if filters.get('end_date'):
                params['end_date'] = str(filters['end_date'])
        
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"/activity/logs?{query_string}"
        
        response = api_get(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch activity logs")
            return None
    except Exception as e:
        st.error(f"Error fetching activity logs: {e}")
        return None

def get_activity_stats(user_id: int = None):
    """Get activity statistics"""
    try:
        endpoint = "/activity/stats"
        if user_id:
            endpoint += f"?user_id={user_id}"
        
        response = api_get(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch activity stats")
            return None
    except Exception as e:
        st.error(f"Error fetching activity stats: {e}")
        return None

def get_recent_activities(limit: int = 20):
    """Get recent activities"""
    try:
        endpoint = f"/activity/recent?limit={limit}"
        response = api_get(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch recent activities")
            return None
    except Exception as e:
        st.error(f"Error fetching recent activities: {e}")
        return None

def cleanup_old_activities(days_to_keep: int = 90):
    """Clean up old activities (admin only)"""
    try:
        endpoint = f"/activity/logs/cleanup?days_to_keep={days_to_keep}"
        response = api_delete(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to cleanup activities")
            return None
    except Exception as e:
        st.error(f"Error cleaning up activities: {e}")
        return None

def api_delete(endpoint: str):
    """Make authenticated DELETE request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.delete(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", headers=headers)

def activity_logs_table():
    """Render activity logs table"""
    st.subheader("Activity Logs")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager") and not has_permission("employee"):
        st.error("You don't have permission to view activity logs")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limit = st.number_input("Limit", min_value=1, max_value=200, value=50)
    
    with col2:
        # User ID filter (only for admin and managers)
        user_id_filter = None
        if has_permission("admin") or has_permission("manager"):
            user_id_filter = st.number_input("Filter by User ID", min_value=1, step=1, value=None)
    
    with col3:
        # Action filter
        action_filter = st.text_input("Filter by Action", placeholder="Enter action keyword...")
    
    # Date filters
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", value=None, max_value=date.today())
    with col2:
        end_date = st.date_input("End Date", value=None, max_value=date.today())
    
    # Apply filters
    filters = {'limit': limit}
    if user_id_filter:
        filters['user_id'] = user_id_filter
    if action_filter:
        filters['action'] = action_filter
    if start_date:
        filters['start_date'] = str(start_date)
    if end_date:
        filters['end_date'] = str(end_date)
    
    # Fetch activity data
    activity_data = get_activity_logs(filters)
    
    if not activity_data:
        st.info("No activity logs found")
        return
    
    # Create DataFrame
    df = pd.DataFrame(activity_data['activities'])
    
    # Display table
    st.dataframe(
        df[[
            'log_id',
            'user_id',
            'action',
            'timestamp'
        ]].rename(columns={
            'log_id': 'ID',
            'user_id': 'User ID',
            'action': 'Action',
            'timestamp': 'Timestamp'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Pagination info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total:** {activity_data['total']} activities")
    with col2:
        st.write(f"**Showing:** {activity_data['limit']} activities (offset: {activity_data['offset']})")

def activity_dashboard():
    """Render activity dashboard"""
    st.subheader("Activity Dashboard")
    
    # Get stats for current user or admin stats
    user_id = None
    if has_permission("admin") or has_permission("manager"):
        # Show overall stats for admin/manager
        stats = get_activity_stats()
        if stats:
            st.write("### System Activity Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Today's Activities", stats['stats']['today_activities'])
            with col2:
                st.metric("Week's Activities", stats['stats']['week_activities'])
            with col3:
                st.metric("Month's Activities", stats['stats']['month_activities'])
            with col4:
                st.metric("Active Users", stats['stats']['active_users'])
    else:
        # Show personal stats for employees
        stats = get_activity_stats(st.session_state.get('user_id'))
        if stats:
            st.write("### Your Activity Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Activities", stats['stats']['total_activities'])
            with col2:
                st.metric("Recent Activities (30 days)", stats['stats']['recent_activities'])
    
    # Recent activities section
    st.write("### Recent Activities")
    recent_data = get_recent_activities(10)
    
    if recent_data:
        df = pd.DataFrame(recent_data['activities'])
        
        st.dataframe(
            df[[
                'log_id',
                'user_id',
                'action',
                'timestamp'
            ]].rename(columns={
                'log_id': 'ID',
                'user_id': 'User ID',
                'action': 'Action',
                'timestamp': 'Timestamp'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No recent activities found")

def cleanup_activities_section():
    """Render cleanup activities section (admin only)"""
    if not has_permission("admin") and not has_permission("manager"):
        return
    
    st.subheader("Cleanup Activities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_to_keep = st.number_input("Days to Keep", min_value=1, max_value=365, value=90)
    
    with col2:
        if st.button("Cleanup Old Activities", type="primary"):
            if st.checkbox("Confirm cleanup"):
                result = cleanup_old_activities(days_to_keep)
                if result:
                    st.success(f"Successfully deleted {result['message'].split()[-2]} old activity logs")
                    st.rerun()
                else:
                    st.error("Failed to cleanup activities")
            else:
                st.info("Please confirm the cleanup by checking the box above")

def main():
    """Main activity logging page"""
    st.title("Activity Logging")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager") and not has_permission("employee"):
        st.error("You don't have permission to access this page")
        return
    
    # Activity dashboard
    activity_dashboard()
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["Activity Logs", "Cleanup"])
    
    with tab1:
        activity_logs_table()
    
    with tab2:
        cleanup_activities_section()

if __name__ == "__main__":
    main()