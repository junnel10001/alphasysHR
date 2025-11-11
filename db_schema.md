# Database Schema – AlphaSys HR Payroll System

Below is the relational schema for the HR system. Primary keys are **PK**, foreign keys are **FK**.

## Users & Roles

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **users** | `user_id` | SERIAL | PK |
|  | `username` | VARCHAR(50) | UNIQUE, NOT NULL |
|  | `password_hash` | VARCHAR(255) | NOT NULL |
|  | `first_name` | VARCHAR(100) | NOT NULL |
|  | `last_name` | VARCHAR(100) | NOT NULL |
|  | `email` | VARCHAR(150) | UNIQUE, NOT NULL |
|  | `phone_number` | VARCHAR(20) | |
|  | `department_id` | INT | FK → **departments.department_id** |
|  | `role_id` | INT | FK → **roles.role_id** |
|  | `hourly_rate` | NUMERIC(10,2) | NOT NULL |
|  | `date_hired` | DATE | NOT NULL |
|  | `status` | VARCHAR(20) | DEFAULT 'active' |

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **roles** | `role_id` | SERIAL | PK |
|  | `role_name` | VARCHAR(50) | UNIQUE, NOT NULL |
|  | `description` | TEXT | |

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **permissions** | `permission_id` | SERIAL | PK |
|  | `permission_name` | VARCHAR(50) | UNIQUE, NOT NULL |
|  | `description` | TEXT | |

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **role_permissions** | `role_id` | INT | PK, FK → **roles.role_id** |
|  | `permission_id` | INT | PK, FK → **permissions.permission_id** |

## Departments

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **departments** | `department_id` | SERIAL | PK |
|  | `department_name` | VARCHAR(100) | UNIQUE, NOT NULL |

## Attendance Tracking

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **attendance** | `attendance_id` | SERIAL | PK |
|  | `user_id` | INT | FK → **users.user_id**, NOT NULL |
|  | `date` | DATE | NOT NULL |
|  | `time_in` | TIMESTAMP | |
|  | `time_out` | TIMESTAMP | |
|  | `hours_worked` | NUMERIC(5,2) | Computed |
|  | `status` | VARCHAR(20) | CHECK (status IN ('Present','Late','Absent','On Leave','Overtime')) |

## Payroll Management

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **payroll** | `payroll_id` | SERIAL | PK |
|  | `user_id` | INT | FK → **users.user_id**, NOT NULL |
|  | `cutoff_start` | DATE | NOT NULL |
|  | `cutoff_end` | DATE | NOT NULL |
|  | `basic_pay` | NUMERIC(10,2) | NOT NULL |
|  | `overtime_pay` | NUMERIC(10,2) | DEFAULT 0 |
|  | `deductions` | NUMERIC(10,2) | DEFAULT 0 |
|  | `net_pay` | NUMERIC(10,2) | NOT NULL |
|  | `generated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **payslips** | `payslip_id` | SERIAL | PK |
|  | `payroll_id` | INT | FK → **payroll.payroll_id**, NOT NULL |
|  | `file_path` | VARCHAR(255) | NOT NULL |

## Leave Management

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **leave_types** | `leave_type_id` | SERIAL | PK |
|  | `leave_name` | VARCHAR(50) | UNIQUE, NOT NULL |
|  | `default_allocation` | INT | NOT NULL |

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **leave_requests** | `leave_id` | SERIAL | PK |
|  | `user_id` | INT | FK → **users.user_id**, NOT NULL |
|  | `leave_type_id` | INT | FK → **leave_types.leave_type_id**, NOT NULL |
|  | `date_from` | DATE | NOT NULL |
|  | `date_to` | DATE | NOT NULL |
|  | `reason` | TEXT | |
|  | `status` | VARCHAR(20) | CHECK (status IN ('Pending','Approved','Rejected','Cancelled')) |
|  | `approver_id` | INT | FK → **users.user_id** |
|  | `approved_at` | TIMESTAMP | |

## Overtime Management

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **overtime_requests** | `ot_id` | SERIAL | PK |
|  | `user_id` | INT | FK → **users.user_id**, NOT NULL |
|  | `date` | DATE | NOT NULL |
|  | `hours_requested` | NUMERIC(4,2) | NOT NULL |
|  | `reason` | TEXT | |
|  | `status` | VARCHAR(20) | CHECK (status IN ('Pending','Approved','Rejected')) |
|  | `approver_id` | INT | FK → **users.user_id** |
|  | `approved_at` | TIMESTAMP | |

## Activity Logging (Optional)

| Table | Column | Type | Constraints |
|-------|--------|------|-------------|
| **activity_logs** | `log_id` | SERIAL | PK |
|  | `user_id` | INT | FK → **users.user_id**, NOT NULL |
|  | `action` | TEXT | NOT NULL |
|  | `timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |