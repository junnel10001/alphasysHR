import streamlit as st
import requests
import json
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Optional
import os
import tempfile

def api_get(endpoint: str):
    """Make authenticated GET request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.get(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", headers=headers)

def api_post(endpoint: str, json_data: dict):
    """Make authenticated POST request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.post(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", json=json_data, headers=headers)

def api_delete(endpoint: str):
    """Make authenticated DELETE request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.delete(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", headers=headers)

def has_permission(required_role: str) -> bool:
    """Check if current user has required role"""
    return st.session_state.get("role", "") == required_role

def get_export_stats():
    """Get export statistics"""
    try:
        response = api_get("/export/stats")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch export statistics")
            return None
    except Exception as e:
        st.error(f"Error fetching export statistics: {e}")
        return None

def get_departments():
    """Get list of all departments"""
    try:
        response = api_get("/export/departments")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch departments")
            return []
    except Exception as e:
        st.error(f"Error fetching departments: {e}")
        return []

def get_employees():
    """Get list of all employees for filtering"""
    try:
        response = api_get("/export/employees")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch employees")
            return []
    except Exception as e:
        st.error(f"Error fetching employees: {e}")
        return []

def get_export_history(filters: dict = None):
    """Get export history with optional filters"""
    try:
        # This would be implemented in a real system with tracking
        # For now, return empty list
        return []
    except Exception as e:
        st.error(f"Error fetching export history: {e}")
        return []

def perform_export(data_type: str, format_type: str, filters: dict):
    """Perform export operation"""
    try:
        export_data = {
            "data_type": data_type,
            "format_type": format_type,
            "start_date": filters.get('start_date'),
            "end_date": filters.get('end_date'),
            "department_id": filters.get('department_id'),
            "user_id": filters.get('user_id')
        }
        
        response = api_post("/export/export", export_data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Export failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error performing export: {e}")
        return None

def download_file(file_path: str, file_name: str):
    """Download exported file"""
    try:
        response = api_get(f"/export/download/{file_path}")
        if response.status_code == 200:
            # Determine appropriate MIME type based on file extension
            file_ext = os.path.splitext(file_name)[1].lower()
            
            if file_ext == '.xlsx' or file_ext == '.xls':
                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif file_ext == '.pdf':
                mime_type = 'application/pdf'
            elif file_ext == '.csv':
                mime_type = 'text/csv'
            elif file_ext == '.zip':
                mime_type = 'application/zip'
            elif file_ext == '.json':
                mime_type = 'application/json'
            else:
                mime_type = 'application/octet-stream'
            
            st.download_button(
                label=f"Download {file_name}",
                data=response.content,
                file_name=file_name,
                mime=mime_type
            )
            return True
        else:
            st.error(f"Failed to download file: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return False

def view_file(file_path: str, file_name: str):
    """View exported file in browser"""
    try:
        response = api_get(f"/export/view/{file_path}")
        if response.status_code == 200:
            # Determine content type
            file_ext = os.path.splitext(file_name)[1].lower()
            
            if file_ext == '.pdf':
                st.success(f"PDF file '{file_name}' loaded successfully!")
                # Create a temporary file and display it
                import tempfile
                import base64
                import os
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Display PDF using st.markdown with data URL
                    b64_pdf = base64.b64encode(response.content).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
                    
                    st.markdown(
                        f'<div style="width:100%;height:600px;border:1px solid #ccc;">{pdf_display}</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Clean up temporary file after display
                    try:
                        os.unlink(tmp_file_path)
                    except OSError:
                        pass  # File might already be deleted or inaccessible
                except Exception as e:
                    st.error(f"Error displaying PDF: {e}")
                    # Alternative: provide download link
                    st.download_button(
                        label="Download PDF Instead",
                        data=response.content,
                        file_name=file_name,
                        mime="application/pdf"
                    )
            elif file_ext == '.xlsx' or file_ext == '.xls':
                st.success(f"Excel file '{file_name}' loaded successfully!")
                st.info("Excel files cannot be displayed in the browser. Please download the file to view it.")
                st.download_button(
                    label=f"Download {file_name}",
                    data=response.content,
                    file_name=file_name,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                st.success(f"File '{file_name}' ready for download!")
                st.download_button(
                    label=f"Download {file_name}",
                    data=response.content,
                    file_name=file_name,
                    mime="application/octet-stream"
                )
            return True
        else:
            st.error(f"Failed to view file: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error viewing file: {e}")
        return False

def cleanup_old_exports(days_to_keep: int = 30):
    """Clean up old export files (admin only)"""
    try:
        response = api_post(f"/export/cleanup", {"days_old": days_to_keep})
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to cleanup export files")
            return None
    except Exception as e:
        st.error(f"Error cleaning up export files: {e}")
        return None

def export_dashboard():
    """Render export dashboard"""
    st.subheader("Export Dashboard")
    
    # Get stats
    stats = get_export_stats()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Exports", stats.get('total_exports', 0))
        
        with col2:
            st.metric("Successful", stats.get('successful_exports', 0))
        
        with col3:
            st.metric("Failed", stats.get('failed_exports', 0))
        
        with col4:
            st.metric("Available Formats", len(stats.get('available_formats', [])))
        
        # Show available formats and data types
        st.write("### Available Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Supported Formats:**")
            for fmt in stats.get('available_formats', []):
                st.write(f"- {fmt.upper()}")
        
        with col2:
            st.write("**Supported Data Types:**")
            for dtype in stats.get('available_data_types', []):
                st.write(f"- {dtype.title()}")

def export_form():
    """Render export form"""
    st.subheader("Export Data")
    
    with st.form("export_form"):
        # Data type selection
        col1, col2 = st.columns(2)
        
        with col1:
            data_types = ["employees", "payroll", "overtime", "activities", "all"]
            selected_data_type = st.selectbox("Select Data Type", data_types)
        
        with col2:
            format_types = ["csv", "excel", "pdf", "json", "zip"]
            selected_format = st.selectbox("Select Format", format_types)
        
        # Date range filters
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=None, max_value=date.today())
        
        with col2:
            end_date = st.date_input("End Date", value=None, max_value=date.today())
        
        # Department filter
        departments = get_departments()
        dept_options = {dept['department_name']: dept['department_id'] for dept in departments}
        dept_options["All"] = None
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_dept = st.selectbox("Department", list(dept_options.keys()))
            department_id = dept_options[selected_dept] if selected_dept != "All" else None
        
        with col2:
            # User ID filter (only for admin and managers)
            user_id_filter = None
            if has_permission("admin") or has_permission("manager"):
                employees = get_employees()
                emp_options = {f"{emp['first_name']} {emp['last_name']}": emp['employee_id'] for emp in employees}
                emp_options["All"] = None
                selected_emp = st.selectbox("Employee", list(emp_options.keys()))
                user_id_filter = emp_options[selected_emp] if selected_emp != "All" else None
        
        with col3:
            # Additional options
            include_headers = st.checkbox("Include Headers", value=True)
        
        # Build filters
        filters = {}
        if start_date:
            filters['start_date'] = str(start_date)
        if end_date:
            filters['end_date'] = str(end_date)
        if department_id:
            filters['department_id'] = department_id
        if user_id_filter:
            filters['user_id'] = user_id_filter
        
        submitted = st.form_submit_button("Export Data")
        
        if submitted:
            if st.checkbox("Confirm export operation"):
                with st.spinner("Exporting data..."):
                    result = perform_export(selected_data_type, selected_format, filters)
                    
                    if result:
                        if result.get('success'):
                            st.success(f"Successfully exported {selected_data_type} data as {selected_format}!")
                            st.write(f"**File Size:** {result.get('file_size', 0)} bytes")
                            st.write(f"**File Name:** {result.get('file_name', 'N/A')}")
                            
                            # Show download/view buttons
                            file_path = result.get('file_path', '')
                            file_name = result.get('file_name', '')
                            
                            if file_path and file_name:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    if st.button("Download File", type="primary"):
                                        if download_file(file_path, file_name):
                                            st.success("File downloaded successfully!")
                                
                                with col2:
                                    if st.button("View File", type="secondary"):
                                        if view_file(file_path, file_name):
                                            st.success("File loaded successfully!")
                        else:
                            st.error(f"Export failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error("Export operation failed")
            else:
                st.info("Please confirm the export operation by checking the box above")
        else:
            st.info("Fill in the export parameters and click Export Data")

def export_history_table():
    """Render export history table"""
    st.subheader("Export History")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager") and not has_permission("employee"):
        st.error("You don't have permission to view export history")
        return
    
    # Get export history
    export_history = get_export_history()
    
    if not export_history:
        st.info("No export history found")
        return
    
    # Create DataFrame
    df = pd.DataFrame(export_history)
    
    # Display table
    st.dataframe(
        df.rename(columns={
            'export_id': 'ID',
            'data_type': 'Data Type',
            'format_type': 'Format',
            'export_date': 'Export Date',
            'file_name': 'File Name',
            'file_size': 'File Size',
            'status': 'Status'
        }),
        use_container_width=True,
        hide_index=True
    )

def cleanup_exports_section():
    """Render cleanup exports section (admin only)"""
    if not has_permission("admin") and not has_permission("manager"):
        return
    
    st.subheader("Cleanup Exports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days_to_keep = st.number_input("Days to Keep", min_value=1, max_value=365, value=30)
    
    with col2:
        if st.button("Cleanup Old Exports", type="primary"):
            if st.checkbox("Confirm cleanup"):
                result = cleanup_old_exports(days_to_keep)
                if result:
                    st.success(f"Successfully cleaned up {result['cleaned_count']} old export files")
                    st.rerun()
                else:
                    st.error("Failed to cleanup export files")
            else:
                st.info("Please confirm the cleanup by checking the box above")

def export_guidelines():
    """Render export guidelines and tips"""
    st.subheader("Export Guidelines")
    
    guidelines = """
    ### Best Practices for Data Export
    
    1. **Choose the Right Format**
       - Use CSV for simple data analysis
       - Use Excel for complex spreadsheets and formulas
       - Use PDF for reports and documentation
       - Use JSON for data interchange and APIs
       - Use ZIP for multiple files or large datasets
    
    2. **Filter Wisely**
       - Use date ranges to limit data size
       - Filter by department for focused reports
       - Use employee filters for individual data
    
    3. **Data Considerations**
       - Exports include all accessible data based on your permissions
       - Sensitive data should be exported with appropriate filters
       - Large datasets may take longer to process
    
    4. **File Management**
       - Regular cleanup of old export files is recommended
       - Download files promptly after export
       - Use descriptive file names for easy identification
    
    ### Format-Specific Tips
    
    **Excel Files (.xlsx)**
    - Best for complex spreadsheets with formulas
    - Supports multiple sheets for "All Data" exports
    - Preserves formatting and formulas
    - Larger file size compared to CSV
    
    **PDF Files**
    - Best for reports and documentation
    - Preserves formatting and layout
    - Cannot be edited, ideal for final reports
    - Supports multi-section documents for "All Data" exports
    
    **CSV Files**
    - Best for simple data analysis
    - Smaller file size and faster processing
    - Compatible with most spreadsheet applications
    - No formatting or formulas preserved
    
    **JSON Files**
    - Best for data interchange and APIs
    - Structured format for programmatic use
    - Preserves all data types accurately
    - Larger file size than CSV
    
    **ZIP Files**
    - Best for multiple files or large datasets
    - Compressed format reduces file size
    - Contains multiple CSV files for "All Data" exports
    - Slower to generate due to compression
    """
    
    st.markdown(guidelines)

def main():
    """Main export management page"""
    st.title("Export Management")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager") and not has_permission("employee"):
        st.error("You don't have permission to access this page")
        return
    
    # Export dashboard
    export_dashboard()
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Export Data", "Export History", "Guidelines"])
    
    with tab1:
        export_form()
    
    with tab2:
        export_history_table()
        cleanup_exports_section()
    
    with tab3:
        export_guidelines()

if __name__ == "__main__":
    main()