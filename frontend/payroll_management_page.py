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

def api_post(endpoint: str, json_data: dict):
    """Make authenticated POST request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.post(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", json=json_data, headers=headers)

def api_put(endpoint: str, json_data: dict):
    """Make authenticated PUT request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.put(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", json=json_data, headers=headers)

def api_delete(endpoint: str):
    """Make authenticated DELETE request to backend"""
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    return requests.delete(f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}{endpoint}", headers=headers)

def has_permission(required_role: str) -> bool:
    """Check if current user has required role"""
    return st.session_state.get("role", "") == required_role

def get_employees():
    """Get list of all employees"""
    try:
        response = api_get("/employees/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch employees")
            return []
    except Exception as e:
        st.error(f"Error fetching employees: {e}")
        return []

def get_departments():
    """Get list of all departments"""
    try:
        response = api_get("/departments/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch departments")
            return []
    except Exception as e:
        st.error(f"Error fetching departments: {e}")
        return []

def get_payroll_history(filters: dict = None):
    """Get payroll history with optional filters"""
    try:
        endpoint = "/payroll/filtered"
        params = {}
        
        if filters:
            if filters.get('start_date'):
                params['start_date'] = str(filters['start_date'])
            if filters.get('end_date'):
                params['end_date'] = str(filters['end_date'])
            if filters.get('department_id'):
                params['department_id'] = str(filters['department_id'])
            if filters.get('user_id'):
                params['user_id'] = str(filters['user_id'])
        
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"/payroll/filtered?{query_string}"
        
        response = api_get(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch payroll history")
            return []
    except Exception as e:
        st.error(f"Error fetching payroll history: {e}")
        return []

def get_payroll_summary():
    """Get payroll summary statistics"""
    try:
        response = api_get("/payroll/summary")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch payroll summary")
            return {}
    except Exception as e:
        st.error(f"Error fetching payroll summary: {e}")
        return {}

def get_employee_payroll_details(employee_id: int):
    """Get payroll details for a specific employee"""
    try:
        response = api_get(f"/payroll/employee/{employee_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch employee payroll details")
            return []
    except Exception as e:
        st.error(f"Error fetching employee payroll details: {e}")
        return []

def create_payroll(payroll_data: dict):
    """Create a new payroll record"""
    try:
        response = api_post("/payroll/", payroll_data)
        if response.status_code == 201:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_payslip(payroll_id: int):
    """Generate payslip for a payroll record"""
    try:
        response = api_post(f"/payroll/{payroll_id}/generate-payslip", {})
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def bulk_generate_payslips(payroll_ids: List[int]):
    """Generate payslips for multiple payroll records"""
    try:
        response = api_post("/payroll/bulk-generate-payslips", {"payroll_ids": payroll_ids})
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_payslip(payroll_id: int):
    """Download payslip PDF"""
    try:
        response = api_get(f"/payroll/{payroll_id}/download-payslip", stream=True)
        if response.status_code == 200:
            return {"success": True, "data": response.content}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def view_payslip(payroll_id: int):
    """View payslip PDF in browser"""
    try:
        response = api_get(f"/payroll/{payroll_id}/view-payslip", stream=True)
        if response.status_code == 200:
            return {"success": True, "data": response.content}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def payroll_generation_form():
    """Render payroll generation form"""
    st.subheader("Create New Payroll")
    
    with st.form("create_payroll"):
        # Employee selection
        employees = get_employees()
        employee_options = {f"{emp['first_name']} {emp['last_name']} ({emp['email']}": emp['user_id'] for emp in employees}
        
        if not employee_options:
            st.error("No employees found. Please add employees first.")
            return
        
        selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
        user_id = employee_options[selected_employee]
        
        # Cutoff dates
        col1, col2 = st.columns(2)
        with col1:
            cutoff_start = st.date_input("Cutoff Start Date", value=date.today().replace(day=1))
        with col2:
            cutoff_end = st.date_input("Cutoff End Date", value=date.today())
        
        # Payroll details
        col1, col2, col3 = st.columns(3)
        with col1:
            basic_pay = st.number_input("Basic Pay", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            overtime_pay = st.number_input("Overtime Pay", min_value=0.0, step=0.01, format="%.2f")
        with col3:
            deductions = st.number_input("Deductions", min_value=0.0, step=0.01, format="%.2f")
        
        # Form validation
        form_errors = []
        
        if cutoff_start >= cutoff_end:
            form_errors.append("Cutoff start date must be before end date")
        
        if basic_pay <= 0:
            form_errors.append("Basic pay must be greater than 0")
        
        if overtime_pay < 0:
            form_errors.append("Overtime pay cannot be negative")
        
        if deductions < 0:
            form_errors.append("Deductions cannot be negative")
        
        # Display errors
        for error in form_errors:
            st.error(error)
        
        submitted = st.form_submit_button("Create Payroll")
        
        if submitted and not form_errors:
            payroll_data = {
                "user_id": user_id,
                "cutoff_start": str(cutoff_start),
                "cutoff_end": str(cutoff_end),
                "basic_pay": basic_pay,
                "overtime_pay": overtime_pay,
                "deductions": deductions
            }
            
            # Show confirmation dialog
            if st.checkbox("Confirm payroll creation"):
                with st.spinner("Creating payroll..."):
                    result = create_payroll(payroll_data)
                    if result["success"]:
                        st.success("Payroll created successfully!")
                        # Log payroll creation activity
                        try:
                            activity_endpoint = f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}/activity/logs"
                            activity_data = {
                                "user_id": st.session_state.get('user_id', 1),
                                "action": f"Created payroll for user ID: {user_id}",
                            }
                            requests.post(activity_endpoint, json=activity_data)
                        except Exception:
                            # Silently fail if activity logging fails
                            pass
                        st.rerun()
                    else:
                        st.error(f"Failed to create payroll: {result['error']}")
            else:
                st.info("Please confirm the payroll creation by checking the box above")

def bulk_payslip_generation_form():
    """Render bulk payslip generation form"""
    st.subheader("Bulk Generate Payslips")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager"):
        st.error("You don't have permission to bulk generate payslips")
        return
    
    # Get payroll data for selection
    payroll_data = get_payroll_history()
    
    if not payroll_data:
        st.info("No payroll records found to generate payslips for")
        return
    
    # Create selection interface
    st.write("Select payroll records to generate payslips for:")
    
    # Create multi-select box
    payroll_options = {f"Payroll {payroll['payroll_id']} - {payroll['cutoff_start']} to {payroll['cutoff_end']}": payroll['payroll_id'] for payroll in payroll_data}
    selected_payrolls = st.multiselect("Select Payrolls", list(payroll_options.keys()))
    
    selected_payroll_ids = [payroll_options[option] for option in selected_payrolls]
    
    # Validation
    if not selected_payroll_ids:
        st.warning("Please select at least one payroll record")
        return
    
    # Show summary
    st.write(f"**Selected {len(selected_payroll_ids)} payroll records**")
    
    # Bulk generate button
    if st.button("Bulk Generate Payslips", type="primary"):
        if st.checkbox("Confirm bulk payslip generation"):
            with st.spinner("Generating payslips..."):
                result = bulk_generate_payslips(selected_payroll_ids)
            
            if result["success"]:
                result_data = result["data"]
                st.success(f"Bulk generation completed!")
                # Log bulk payslip generation activity
                try:
                    activity_endpoint = f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}/activity/logs"
                    activity_data = {
                        "user_id": st.session_state.get('user_id', 1),
                        "action": f"Bulk generated payslips for {len(selected_payroll_ids)} payrolls",
                    }
                    requests.post(activity_endpoint, json=activity_data)
                except Exception:
                    # Silently fail if activity logging fails
                    pass
                
                st.write(f"**Total Processed:** {result_data['total_payrolls']}")
                st.write(f"**Successful:** {result_data['successful_count']}")
                st.write(f"**Failed:** {result_data['failed_count']}")
                
                # Show results
                if result_data['results']:
                    st.write("### Results:")
                    for result_item in result_data['results']:
                        if result_item['status'] == 'success':
                            st.success(f"✓ Payroll {result_item['payroll_id']}: Generated")
                        else:
                            st.error(f"✗ Payroll {result_item['payroll_id']}: {result_item['error']}")
                
                st.rerun()
            else:
                st.error(f"Bulk generation failed: {result['error']}")
        else:
            st.info("Please confirm the bulk generation by checking the box above")

def payroll_history_table():
    """Render payroll history table"""
    st.subheader("Payroll History")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager") and not has_permission("employee"):
        st.error("You don't have permission to view payroll history")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Start Date", value=None, max_value=date.today())
    with col2:
        end_date = st.date_input("End Date", value=None, max_value=date.today())
    with col3:
        if has_permission("admin"):
            departments = get_departments()
            dept_options = {dept['department_name']: dept['department_id'] for dept in departments}
            dept_options["All"] = None
            selected_dept = st.selectbox("Department", list(dept_options.keys()))
            department_id = dept_options[selected_dept] if selected_dept != "All" else None
        else:
            department_id = None
    
    # User ID filter (only for admin and managers)
    user_id_filter = None
    if has_permission("admin") or has_permission("manager"):
        user_id_filter = st.number_input("Filter by User ID", min_value=1, step=1, value=None)
    
    # Apply filters
    filters = {}
    if start_date:
        filters['start_date'] = str(start_date)
    if end_date:
        filters['end_date'] = str(end_date)
    if department_id:
        filters['department_id'] = department_id
    if user_id_filter:
        filters['user_id'] = user_id_filter
    
    # Fetch payroll data
    payroll_data = get_payroll_history(filters)
    
    if not payroll_data:
        st.info("No payroll records found")
        return
    
    # Create DataFrame
    df = pd.DataFrame(payroll_data)
    
    # Display table
    st.dataframe(
        df[[
            'payroll_id',
            'user_id',
            'cutoff_start',
            'cutoff_end',
            'basic_pay',
            'overtime_pay',
            'deductions',
            'net_pay',
            'generated_at'
        ]].rename(columns={
            'payroll_id': 'ID',
            'user_id': 'Employee ID',
            'cutoff_start': 'Start Date',
            'cutoff_end': 'End Date',
            'basic_pay': 'Basic Pay',
            'overtime_pay': 'Overtime',
            'deductions': 'Deductions',
            'net_pay': 'Net Pay',
            'generated_at': 'Generated At'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Action buttons for each row
    st.write("### Actions")
    
    for payroll in payroll_data:
        # Check permissions for actions
        can_view = True
        can_generate_payslip = has_permission("admin") or has_permission("manager") or payroll['user_id'] == st.session_state.get('user_id', None)
        can_delete = has_permission("admin")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if can_view and st.button(f"View Details", key=f"view_{payroll['payroll_id']}"):
                show_payroll_details(payroll['payroll_id'])
        
        with col2:
            if can_generate_payslip and st.button(f"Generate Payslip", key=f"payslip_{payroll['payroll_id']}"):
                generate_payslip_action(payroll['payroll_id'])
        
        with col3:
            if can_delete and st.button(f"Delete", key=f"delete_{payroll['payroll_id']}", type="secondary"):
                delete_payroll_action(payroll['payroll_id'])

def show_payroll_details(payroll_id: int):
    """Show detailed payroll information"""
    try:
        response = api_get(f"/payroll/{payroll_id}")
        if response.status_code == 200:
            payroll = response.json()
            
            st.subheader(f"Payroll Details - ID: {payroll_id}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Employee ID:** {payroll['user_id']}")
                st.write(f"**Cutoff Start:** {payroll['cutoff_start']}")
                st.write(f"**Cutoff End:** {payroll['cutoff_end']}")
            
            with col2:
                st.write(f"**Basic Pay:** ${payroll['basic_pay']:.2f}")
                st.write(f"**Overtime Pay:** ${payroll['overtime_pay']:.2f}")
                st.write(f"**Deductions:** ${payroll['deductions']:.2f}")
                st.write(f"**Net Pay:** ${payroll['net_pay']:.2f}")
                st.write(f"**Generated At:** {payroll['generated_at']}")
            
            # Check if payslip exists
            payslip_response = api_get(f"/payroll/{payroll_id}/payslips/list")
            payslip_exists = payslip_response.status_code == 200 and payslip_response.json()
            
            if payslip_exists:
                st.success("✓ Payslip Generated")
                
                # PDF actions
                st.write("### Payslip Actions")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Download Payslip", type="primary"):
                        download_payslip_action(payroll_id)
                
                with col2:
                    if st.button("View Payslip", type="secondary"):
                        view_payslip_action(payroll_id)
            else:
                # Generate payslip button
                if st.button("Generate Payslip"):
                    generate_payslip_action(payroll_id)
        else:
            st.error("Failed to fetch payroll details")
    except Exception as e:
        st.error(f"Error fetching payroll details: {e}")

def generate_payslip_action(payroll_id: int):
    """Generate payslip for a specific payroll"""
    with st.spinner("Generating payslip..."):
        result = generate_payslip(payroll_id)
    
    if result["success"]:
        st.success("Payslip generated successfully!")
        # Log payslip generation activity
        try:
            activity_endpoint = f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}/activity/logs"
            activity_data = {
                "user_id": st.session_state.get('user_id', 1),
                "action": f"Generated payslip for payroll ID: {payroll_id}",
            }
            requests.post(activity_endpoint, json=activity_data)
        except Exception:
            # Silently fail if activity logging fails
            pass
        
        # Show payslip actions
        st.write("### Payslip Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download Payslip", type="primary"):
                download_payslip_action(payroll_id)
        
        with col2:
            if st.button("View Payslip", type="secondary"):
                view_payslip_action(payroll_id)
    else:
        st.error(f"Failed to generate payslip: {result['error']}")

def download_payslip_action(payroll_id: int):
    """Download payslip PDF"""
    with st.spinner("Downloading payslip..."):
        result = download_payslip(payroll_id)
    
    if result["success"]:
        st.success("Payslip downloaded successfully!")
        
        # Create download button
        st.download_button(
            label="Download PDF",
            data=result["data"],
            file_name=f"payslip_{payroll_id}.pdf",
            mime="application/pdf"
        )
    else:
        st.error(f"Failed to download payslip: {result['error']}")

def view_payslip_action(payroll_id: int):
    """View payslip PDF in browser"""
    with st.spinner("Loading payslip..."):
        result = view_payslip(payroll_id)
    
    if result["success"]:
        st.success("Payslip loaded successfully!")
        
        # Create a temporary file and display it
        import tempfile
        import base64
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(result["data"])
            tmp_file_path = tmp_file.name
        
        try:
            # Display PDF using st.markdown with data URL
            b64_pdf = base64.b64encode(result["data"]).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
            
            st.markdown(
                f'<div style="width:100%;height:600px;border:1px solid #ccc;">{pdf_display}</div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Error displaying PDF: {e}")
            # Alternative: provide download link
            st.download_button(
                label="Download PDF Instead",
                data=result["data"],
                file_name=f"payslip_{payroll_id}.pdf",
                mime="application/pdf"
            )
    else:
        st.error(f"Failed to view payslip: {result['error']}")

def delete_payroll_action(payroll_id: int):
    """Delete a payroll record"""
    if st.confirm(f"Are you sure you want to delete payroll record {payroll_id}?"):
        try:
            response = api_delete(f"/payroll/{payroll_id}")
            if response.status_code == 204:
                st.success("Payroll record deleted successfully!")
                # Log deletion activity
                try:
                    activity_endpoint = f"{st.secrets.get('BACKEND_URL', 'http://localhost:8000')}/activity/logs"
                    activity_data = {
                        "user_id": st.session_state.get('user_id', 1),
                        "action": f"Deleted payroll record ID: {payroll_id}",
                    }
                    requests.post(activity_endpoint, json=activity_data)
                except Exception:
                    # Silently fail if activity logging fails
                    pass
                st.rerun()
            else:
                st.error("Failed to delete payroll record")
        except Exception as e:
            st.error(f"Error deleting payroll: {e}")

def payroll_summary_dashboard():
    """Render payroll summary dashboard"""
    st.subheader("Payroll Summary")
    
    summary_data = get_payroll_summary()
    
    if not summary_data:
        st.info("No payroll summary data available")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Payrolls", summary_data.get('total_payrolls', 0))
    
    with col2:
        total_amount = summary_data.get('total_net_pay', 0)
        st.metric("Total Net Pay", f"${total_amount:,.2f}")
    
    with col3:
        avg_pay = summary_data.get('average_net_pay', 0)
        st.metric("Average Net Pay", f"${avg_pay:,.2f}")
    
    with col4:
        recent_count = summary_data.get('recent_payrolls', 0)
        st.metric("This Month", recent_count)

def employee_payroll_view():
    """Render employee-specific payroll view"""
    st.subheader("Employee Payroll Details")
    
    # Employee selection
    employees = get_employees()
    if not employees:
        st.error("No employees found")
        return
    
    employee_options = {f"{emp['first_name']} {emp['last_name']} ({emp['email']}": emp['user_id'] for emp in employees}
    selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
    employee_id = employee_options[selected_employee]
    
    # Get employee payroll details
    payroll_details = get_employee_payroll_details(employee_id)
    
    if not payroll_details:
        st.info("No payroll records found for this employee")
        return
    
    # Create DataFrame
    df = pd.DataFrame(payroll_details)
    
    # Display table
    st.dataframe(
        df[[
            'payroll_id', 
            'cutoff_start', 
            'cutoff_end', 
            'basic_pay', 
            'overtime_pay', 
            'deductions', 
            'net_pay'
        ]].rename(columns={
            'payroll_id': 'ID',
            'cutoff_start': 'Start Date',
            'cutoff_end': 'End Date',
            'basic_pay': 'Basic Pay',
            'overtime_pay': 'Overtime',
            'deductions': 'Deductions',
            'net_pay': 'Net Pay'
        }),
        use_container_width=True,
        hide_index=True
    )

def main():
    """Main payroll management page"""
    st.title("Payroll Management")
    
    # Check permissions
    if not has_permission("admin") and not has_permission("manager") and not has_permission("employee"):
        st.error("You don't have permission to access this page")
        return
    
    # Summary dashboard
    payroll_summary_dashboard()
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Create Payroll", "Payroll History", "Employee View", "Bulk Payslips"])
    
    with tab1:
        if has_permission("admin") or has_permission("manager"):
            payroll_generation_form()
        else:
            st.info("You don't have permission to create payrolls")
    
    with tab2:
        payroll_history_table()
    
    with tab3:
        if has_permission("admin") or has_permission("manager") or has_permission("employee"):
            employee_payroll_view()
        else:
            st.info("You don't have permission to view employee payroll details")
    
    with tab4:
        if has_permission("admin") or has_permission("manager"):
            bulk_payslip_generation_form()
        else:
            st.info("You don't have permission to bulk generate payslips")

if __name__ == "__main__":
    main()