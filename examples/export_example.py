#!/usr/bin/env python3
"""
Example script demonstrating how to use the Export Service
"""

import os
import sys
from datetime import datetime, date

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.export_service import ExportService


def main():
    """Main function to demonstrate export functionality"""
    
    # Get database session
    db = next(get_db())
    
    # Create export service instance
    export_service = ExportService(db)
    
    print("HR Data Export Service Example")
    print("=" * 40)
    
    # Display available formats and data types
    print("\nAvailable export formats:")
    formats = export_service.get_export_formats()
    for fmt in formats:
        print(f"  - {fmt}")
    
    print("\nAvailable data types:")
    data_types = export_service.get_export_data_types()
    for dtype in data_types:
        print(f"  - {dtype}")
    
    # Example 1: Export employees to CSV
    print("\nExample 1: Exporting employees to CSV...")
    try:
        csv_file = export_service.export_employees('csv')
        print(f"✓ Employees exported to: {csv_file}")
    except Exception as e:
        print(f"✗ Failed to export employees: {str(e)}")
    
    # Example 2: Export payroll to Excel (if pandas is available)
    print("\nExample 2: Exporting payroll to Excel...")
    try:
        excel_file = export_service.export_payroll('excel')
        print(f"✓ Payroll exported to: {excel_file}")
    except Exception as e:
        print(f"✗ Failed to export payroll: {str(e)}")
    
    # Example 3: Export overtime with filters
    print("\nExample 3: Exporting overtime with date filters...")
    try:
        filters = {
            'start_date': date(2023, 1, 1),
            'end_date': date(2023, 12, 31)
        }
        overtime_file = export_service.export_overtime('csv', filters)
        print(f"✓ Overtime exported to: {overtime_file}")
    except Exception as e:
        print(f"✗ Failed to export overtime: {str(e)}")
    
    # Example 4: Export all data as zip
    print("\nExample 4: Exporting all data as zip...")
    try:
        zip_file = export_service.export_all_data('zip')
        print(f"✓ All data exported to: {zip_file}")
    except Exception as e:
        print(f"✗ Failed to export all data: {str(e)}")
    
    # Example 5: Export activities with action filter
    print("\nExample 5: Exporting activities with action filter...")
    try:
        filters = {
            'action': 'login'
        }
        activities_file = export_service.export_activities('csv', filters)
        print(f"✓ Activities exported to: {activities_file}")
    except Exception as e:
        print(f"✗ Failed to export activities: {str(e)}")
    
    # Example 6: Validate export parameters
    print("\nExample 6: Validating export parameters...")
    try:
        valid = export_service.validate_export_params('employees', 'csv')
        print(f"✓ Export parameters valid: {valid}")
        
        invalid = export_service.validate_export_params('invalid', 'csv')
        print(f"✓ Export parameters invalid: {invalid}")
    except Exception as e:
        print(f"✗ Failed to validate parameters: {str(e)}")
    
    # Example 7: Cleanup old exports
    print("\nExample 7: Cleaning up old exports...")
    try:
        cleaned_count = export_service.cleanup_old_exports(30)
        print(f"✓ Cleaned up {cleaned_count} old export files")
    except Exception as e:
        print(f"✗ Failed to cleanup exports: {str(e)}")
    
    print("\nExport Service Example Complete!")
    print("=" * 40)


if __name__ == "__main__":
    main()