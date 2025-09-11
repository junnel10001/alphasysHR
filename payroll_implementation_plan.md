# Payroll Management Module Implementation Plan

## Overview
This document outlines the implementation plan for the Payroll Management module of the AlphaSys HR system. The payroll module will handle salary calculations, deductions, payslip generation, and payroll period management.

## Module Components

### 1. Backend Implementation

#### 1.1 Payroll Router (`backend/routers/payroll.py`)
- **Purpose**: Handle HTTP requests for payroll operations
- **Endpoints needed**:
  - `POST /payroll/` - Create new payroll record
  - `GET /payroll/` - List payroll records (with pagination)
  - `GET /payroll/{payroll_id}` - Get specific payroll record
  - `PUT /payroll/{payroll_id}` - Update payroll record
  - `DELETE /payroll/{payroll_id}` - Delete payroll record
  - `POST /payroll/{payroll_id}/generate-payslip` - Generate payslip for payroll

#### 1.2 Payroll Service (`backend/services/payroll_service.py`)
- **Purpose**: Handle business logic for payroll calculations
- **Functions needed**:
  - `calculate_basic_pay(employee, payroll_period)` - Calculate base salary
  - `calculate_overtime_pay(employee, payroll_period)` - Calculate overtime compensation
  - `calculate_deductions(employee, payroll_period)` - Calculate deductions
  - `calculate_net_pay(basic_pay, overtime_pay, deductions)` - Calculate final net pay
  - `generate_payslip(payroll_record)` - Generate payslip document

#### 1.3 Pydantic Models
- **PayrollCreate**: Input model for creating payroll
- **PayrollOut**: Output model for payroll response
- **PayslipCreate**: Input model for payslip generation
- **PayslipOut**: Output model for payslip response

### 2. Database Operations

#### 2.1 Payroll CRUD Operations
- **Create**: Add new payroll records with calculated values
- **Read**: Retrieve payroll records with employee information
- **Update**: Modify payroll records (status, corrections)
- **Delete**: Remove payroll records (with archival instead of hard delete)

#### 2.2 Payslip Management
- **File Storage**: Store generated payslip files
- **File Retrieval**: Download payslip documents
- **File Management**: Update/ delete payslip files

### 3. Payroll Calculation Logic

#### 3.1 Salary Calculation
- **Basic Pay**: Calculate based on employee's hourly rate and worked hours
- **Overtime Pay**: Calculate overtime based on attendance records
- **Deductions**: Calculate taxes, benefits, other deductions
- **Net Pay**: Final amount after all calculations

#### 3.2 Payroll Period Management
- **Cutoff Dates**: Define payroll periods (e.g., 1st-15th, 16th-end of month)
- **Period Validation**: Ensure dates are valid and logical
- **Historical Data**: Maintain payroll history for reporting

### 4. Integration Points

#### 4.1 Employee Integration
- **Employee Data**: Use existing employee data (hourly_rate, etc.)
- **Leave Integration**: Factor in approved leaves for salary calculation
- **Attendance Integration**: Use attendance records for overtime calculation

#### 4.2 Leave Integration
- **Leave Impact**: Adjust salary for approved leave periods
- **Leave Deductions**: Handle unpaid leave scenarios

#### 4.3 Attendance Integration
- **Overtime Calculation**: Use attendance records for overtime hours
- **Work Hours**: Calculate regular hours vs overtime hours

### 5. API Design

#### 5.1 Payroll Endpoints
```python
# Create payroll
POST /payroll/
{
    "user_id": int,
    "cutoff_start": "date",
    "cutoff_end": "date"
}

# List payroll
GET /payroll/?skip=0&limit=100&user_id=2&start_date=2025-01-01&end_date=2025-12-31

# Get payroll
GET /payroll/{payroll_id}

# Update payroll
PUT /payroll/{payroll_id}
{
    "status": "processed|approved|paid"
}

# Delete payroll
DELETE /payroll/{payroll_id}

# Generate payslip
POST /payroll/{payroll_id}/generate-payslip
```

#### 5.2 Payslip Endpoints
```python
# List payslips
GET /payslips/?skip=0&limit=100&payroll_id=1&user_id=2

# Download payslip
GET /payslips/{payslip_id}/download
```

### 6. Testing Strategy

#### 6.1 Unit Tests
- **Payroll Calculation**: Test salary calculation logic
- **Deduction Calculation**: Test tax and deduction calculations
- **Overtime Calculation**: Test overtime pay calculations

#### 6.2 Integration Tests
- **Employee-Payroll Integration**: Test payroll generation with employee data
- **Attendance-Payroll Integration**: Test overtime calculations with attendance data
- **Leave-Payroll Integration**: Test salary adjustments for leave periods

#### 6.3 API Tests
- **Payroll CRUD Operations**: Test all payroll endpoints
- **Payslip Management**: Test payslip generation and download
- **Error Handling**: Test validation and error responses

### 7. Frontend Integration

#### 7.1 Payroll Dashboard
- **Overview**: Show key payroll metrics
- **Recent Payrolls**: List recent payroll records
- **Quick Actions**: Generate payroll, view payslips

#### 7.2 Payroll Management
- **Payroll List**: Display all payroll records with filters
- **Payroll Details**: Show detailed payroll information
- **Payslip Viewer**: Display and download payslip documents

#### 7.3 Employee Payroll
- **Employee Payslips**: Show individual employee payslip history
- **Pay Summary**: Show salary breakdown for current period

### 8. Security Considerations

#### 8.1 Access Control
- **Admin Access**: Full payroll management access
- **Manager Access**: View payroll for department employees
- **Employee Access**: View only own payslips

#### 8.2 Data Protection
- **Sensitive Data**: Protect salary and financial information
- **Audit Logging**: Log all payroll-related actions
- **File Security**: Secure storage of payslip documents

### 9. Implementation Phases

#### Phase 1: Core Payroll (Week 1)
- Create payroll router and basic CRUD operations
- Implement payroll service layer
- Add basic salary calculation logic

#### Phase 2: Advanced Calculations (Week 2)
- Add overtime pay calculations
- Implement deduction calculations
- Add net pay calculations

#### Phase 3: Payslip Management (Week 3)
- Implement payslip generation
- Add file storage and retrieval
- Create payslip download functionality

#### Phase 4: Testing and Integration (Week 4)
- Add comprehensive unit and integration tests
- Integrate with frontend UI
- Add payroll API tests

#### Phase 5: Enhanced Features (Week 5)
- Add payroll reporting
- Implement bulk payroll generation
- Add payroll export functionality

### 10. Success Criteria

- **Functional**: All payroll operations work correctly
- **Accurate**: All salary calculations are precise
- **Secure**: Proper access control and data protection
- **Usable**: Intuitive frontend interface
- **Testable**: Comprehensive test coverage
- **Performant**: Fast response times for payroll operations