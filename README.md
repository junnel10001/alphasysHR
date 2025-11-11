# AlphaHR - Comprehensive HR and Payroll Management System

## Overview

AlphaHR is a full-stack Human Resources and Payroll Management System designed to streamline HR operations, employee management, attendance tracking, leave management, overtime processing, and payroll administration. The system features a modern, responsive frontend built with Next.js and TypeScript, powered by a robust FastAPI backend with SQLAlchemy for data persistence.

### Key Features

- **Employee Management**: Complete employee lifecycle management with role-based access control
- **Attendance Tracking**: Real-time attendance monitoring with comprehensive reporting
- **Leave Management**: Request, approve, and track employee leave with various leave types
- **Overtime Management**: Overtime request processing and approval workflows
- **Payroll Processing**: Automated payroll calculation with payslip generation
- **Dashboard Analytics**: Real-time KPIs and comprehensive reporting
- **Export Functionality**: Multi-format data export (CSV, Excel, PDF, JSON)
- **User Invitations**: Secure employee onboarding with invitation-based registration
- **Activity Logging**: Comprehensive audit trail for all system activities

## Architecture

### Technology Stack

**Backend:**
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **Alembic**: Database migration tool
- **JWT**: Secure token-based authentication
- **RBAC**: Role-Based Access Control for fine-grained permissions
- **bcrypt**: Password hashing for security

**Frontend:**
- **Next.js 14**: React framework with server-side rendering
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Recharts**: Data visualization library
- **React Query**: Data fetching and state management

**Database:**
- **MySQL**: Primary database for production and development

**Server:**
- **Uvicorn**: ASGI server for FastAPI

### System Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│    (MySQL)      │
│                 │    │                 │    │                 │
│ - UI Components │    │ - API Endpoints │    │ - User Data     │
│ - State Mgmt    │    │ - Auth/JWT      │    │ - Attendance    │
│ - Routing       │    │ - RBAC          │    │ - Payroll       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements

- **Node.js** 18.0 or higher
- **Python** 3.9 or higher
- **MySQL** 8.0 or higher

### Development Environment

- **Git** for version control
- **VS Code** or any preferred IDE
- **Postman** or similar API testing tool (optional)

## Installation

### Backend Setup

1. **Clone the repository**
```bash
git clone [repository_url]
cd AlphaHR
```

2. **Create Python virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the root directory with the following variables:
```env
DATABASE_URL=mysql://username:password@localhost:3306/alphahr_db
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
```

5. **Database Setup**
```bash
# Initialize database tables
python -c "from backend.database import engine; from backend.models import Base; Base.metadata.create_all(bind=engine)"

# Seed initial data
python seed_all.py
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install Node.js dependencies**
```bash
npm install
```

3. **Environment Configuration**
Create a `.env.local` file in the frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Development Mode

#### Backend Server
```bash
# From project root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Server
```bash
# From frontend directory
cd frontend
npm run dev
```

### Production Mode

#### Backend Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

#### Frontend Build
```bash
cd frontend
npm run build
npm start
```

## Database Seeding

The system includes comprehensive seeding scripts to populate the database with realistic demo data.

### Individual Seed Scripts

- [`seed_roles_departments.py`](seed_roles_departments.py): Creates default roles, permissions, departments
- [`seed_leave_types.py`](seed_leave_types.py): Sets up leave type categories
- [`seed_users.py`](seed_users.py): Creates admin and demo user accounts
- [`seed_attendance.py`](seed_attendance.py): Generates 30 days of attendance data
- [`seed_payroll.py`](seed_payroll.py): Creates payroll entries for demo periods
- [`seed_leave_requests.py`](seed_leave_requests.py): Generates sample leave requests
- [`seed_overtime_requests.py`](seed_overtime_requests.py): Creates overtime request samples
- [`seed_activity_logs.py`](seed_activity_logs.py): Populates activity audit logs

### Master Seeder

Run all seed scripts in sequence:
```bash
python seed_all.py
```

### Database Initialization

After running the seed scripts, the database will be populated with:
- Default roles and permissions
- Admin and demo user accounts
- Sample departments and leave types
- Initial configuration data

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token` | User login - returns JWT token |
| POST | `/register` | User registration |
| GET | `/users/me` | Get current user profile |
| GET | `/me/permissions` | Get current user permissions |

### Employee Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/employees` | List all employees | `employee_access` |
| GET | `/employees/{id}` | Get employee details | `employee_access` |
| POST | `/employees` | Create new employee | `create_employee` |
| PUT | `/employees/{id}` | Update employee | `update_employee` |
| DELETE | `/employees/{id}` | Delete employee | `delete_employee` |

### Attendance Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/attendance` | List attendance records | `read_attendance` |
| POST | `/attendance` | Create attendance record | `create_attendance` |
| GET | `/attendance/{id}` | Get attendance details | `read_attendance` |
| PUT | `/attendance/{id}` | Update attendance | `update_attendance` |
| DELETE | `/attendance/{id}` | Delete attendance | `delete_attendance` |

### Leave Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/leave` | List leave requests | `read_leave` |
| POST | `/leave` | Create leave request | `create_leave` |
| GET | `/leave/{id}` | Get leave details | `read_leave` |
| PUT | `/leave/{id}` | Update leave request | `update_leave` |

### Overtime Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/overtime` | List overtime requests | `read_overtime` |
| POST | `/overtime` | Create overtime request | `create_overtime` |
| GET | `/overtime/{id}` | Get overtime details | `read_overtime` |
| PUT | `/overtime/{id}` | Update overtime request | `update_overtime` |
| POST | `/overtime/{id}/approve` | Approve overtime | `approve_overtime` |
| POST | `/overtime/{id}/reject` | Reject overtime | `reject_overtime` |

### Payroll Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/payroll` | List payroll records | `read_payroll` |
| POST | `/payroll` | Create payroll record | `create_payroll` |
| GET | `/payroll/{id}` | Get payroll details | `read_payroll` |
| PUT | `/payroll/{id}` | Update payroll record | `update_payroll` |
| POST | `/payroll/{id}/generate-payslip` | Generate PDF payslip | `generate_payslip` |
| GET | `/payroll/{id}/download-payslip` | Download payslip | `read_payroll` |

### Dashboard Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/dashboard/kpi` | Get dashboard KPIs | `dashboard_access` |
| GET | `/dashboard/kpi/employees-present` | Get present employees | `dashboard_access` |
| GET | `/dashboard/kpi/pending-leave` | Get pending leave requests | `dashboard_access` |
| GET | `/dashboard/kpi/pending-overtime` | Get pending overtime requests | `dashboard_access` |

### Export Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| POST | `/export/export` | Export HR data in various formats | `export_data` |
| GET | `/export/stats` | Get export statistics | `export_view` |
| GET | `/export/download/{file_path}` | Download exported file | `export_download` |

### Department Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/departments` | List all departments | `department_view` |
| POST | `/departments` | Create new department | `department_manage` |
| GET | `/departments/{id}` | Get department details | `department_view` |
| PUT | `/departments/{id}` | Update department | `department_manage` |
| DELETE | `/departments/{id}` | Delete department | `department_manage` |

### Role & Permission Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/roles` | List all roles | `view_roles` |
| POST | `/roles` | Create new role | `manage_roles` |
| GET | `/permissions` | List all permissions | `manage_permissions` |
| POST | `/permissions` | Create new permission | `manage_permissions` |

### Invitation Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/invitations` | List invitations | `manage_invitations` |
| POST | `/invitations` | Create invitation | `manage_invitations` |
| GET | `/invitations/{id}` | Get invitation details | `manage_invitations` |
| POST | `/invitations/accept` | Accept invitation | None (public) |
| POST | `/invitations/resend` | Resend invitation | `manage_invitations` |
| POST | `/invitations/revoke` | Revoke invitation | `manage_invitations` |

### Activity Logging Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|-------------------|
| GET | `/activity/logs` | Get activity logs | `view_activity` |
| GET | `/activity/logs/{id}` | Get specific log | `view_activity` |
| GET | `/activity/stats` | Get activity statistics | `view_activity` |
| DELETE | `/activity/logs/cleanup` | Clean up old logs | `manage_activity` |

## Frontend Pages and Functionality

### Frontend Functionality Verification

All functionality previously available in Streamlit has been successfully migrated to the Next.js frontend:

**✅ Authentication & User Management**
- Login/logout with JWT authentication (`/login`)
- User registration (`/register`)
- Profile management (`/profile`)
- User invitations (`/invitations`)

**✅ Employee Management**
- Employee listing with search and filters (`/employees`)
- Add/edit/delete employees
- Department and role management

**✅ Attendance Management**
- Global attendance overview (`/attendance`)
- Personal attendance records (`/my-attendance`)
- Check-in/check-out functionality
- Attendance analytics and reporting

**✅ Leave Management**
- Leave request submission (`/my-leave`)
- Leave approval workflow (`/leave`)
- Leave balance tracking
- Leave calendar view

**✅ Overtime Management**
- Overtime request submission (`/my-overtime`)
- Overtime approval (`/overtime`)
- Overtime reporting and analytics

**✅ Payroll Management**
- Payroll processing and generation (`/payroll`)
- Payslip creation and download
- Personal payroll history (`/my-payroll`)
- Payroll analytics and reporting

**✅ Dashboard & Analytics**
- Admin dashboard with KPIs (`/dashboard`)
- Real-time data visualization
- Departmental analytics
- Performance metrics

**✅ System Administration**
- Role and permission management
- Department management
- System settings (`/settings`)
- Activity logging and audit trails

**✅ Export & Reporting**
- Multi-format data export (`/export`)
- Custom filtering options
- Export history tracking

### Authentication Pages

#### Login (`/login`)
- User authentication with email and password
- JWT token management
- Redirects to dashboard upon successful login

#### Register (`/register`)
- New user registration
- Form validation
- Account creation with default permissions

### Main Application Pages

#### Dashboard (`/dashboard`)
- **Admin Dashboard**: System-wide KPIs and metrics
- **Employee Dashboard**: Personal statistics and quick actions
- Real-time data visualization with charts
- Quick access to common functions

#### Employee Management (`/employees`)
- **Employee List**: Searchable, filterable employee table
- **Add Employee**: Modal form for new employee creation
- **Edit Employee**: Update existing employee details
- **Employee Profile**: View comprehensive employee information
- **Permissions**: Role-based access control implementation

#### Attendance (`/attendance` & `/my-attendance`)
- **Attendance Overview**: Global attendance monitoring (Admin)
- **Personal Attendance**: Individual attendance records (Employee)
- **Check-in/Check-out**: Time tracking functionality
- **Attendance Reports**: Comprehensive attendance analytics

#### Leave Management (`/leave` & `/my-leave`)
- **Leave Requests**: Submit and manage leave applications
- **Approval Workflow**: Multi-level leave approval system
- **Leave Calendar**: Visual representation of team leave
- **Leave Balance**: Track remaining leave days

#### Overtime Management (`/overtime` & `/my-overtime`)
- **Overtime Requests**: Submit overtime hours for approval
- **Approval Process**: Manager approval workflow
- **Overtime Reports**: Analytics on overtime hours
- **Compensation Tracking**: Calculate overtime pay

#### Payroll Management (`/payroll` & `/my-payroll`)
- **Payroll Processing**: Generate payroll for pay periods
- **Payslip Generation**: PDF payslip creation
- **Payroll History**: Historical payroll records
- **Payroll Analytics**: Comprehensive payroll reporting

#### Export (`/export`)
- **Data Export**: Export in CSV, Excel, PDF, JSON formats
- **Custom Filters**: Filter data by date, department, role
- **Export History**: Track all export activities
- **Download Center**: Access previously exported files

#### Invitations (`/invitations`)
- **Invite Employees**: Send invitations to new team members
- **Invitation Tracking**: Monitor invitation status
- **Resend Invitations**: Resend expired invitations
- **Invitation Statistics**: Analytics on invitation process

#### Profile (`/profile`)
- **Personal Information**: Update contact details
- **Password Change**: Secure password update
- **Preferences**: User configuration options
- **Activity History**: Personal audit trail

#### Settings (`/settings`)
- **System Configuration**: Administrative settings
- **Role Management**: Define user roles and permissions
- **Department Management**: Organizational structure
- **System Maintenance**: Database and system utilities

## Authentication and Authorization

### Authentication Flow

1. **User Login**: Credentials validated against database
2. **JWT Generation**: Access token created with user information
3. **Token Storage**: Token stored in frontend localStorage
4. **API Requests**: Token included in Authorization header
5. **Token Validation**: Backend validates token on each request

### Role-Based Access Control (RBAC)

The system implements a comprehensive RBAC system with:

#### Default Roles
- **Admin**: Full system access
- **Manager**: Department-level access
- **HR**: HR-specific permissions
- **Employee**: Self-service access only

#### Permission Categories
- **Employee Management**: `create_employee`, `update_employee`, `delete_employee`, `employee_access`
- **Attendance**: `read_attendance`, `create_attendance`, `update_attendance`
- **Leave**: `read_leave`, `create_leave`, `approve_leave`, `update_leave`
- **Overtime**: `read_overtime`, `create_overtime`, `approve_overtime`, `update_overtime`
- **Payroll**: `read_payroll`, `create_payroll`, `update_payroll`, `generate_payslip`
- **Dashboard**: `dashboard_access`, `kpi_view`
- **Export**: `export_data`, `export_download`, `export_view`
- **System**: `manage_permissions`, `manage_roles`, `view_activity`

### Middleware Implementation

The system uses FastAPI middleware to:
- Validate JWT tokens on protected routes
- Extract user information from tokens
- Check permissions based on endpoint requirements
- Log user activities for audit trails

## Database Schema

The database schema is designed for scalability and includes the following main entities:

### Core Tables
- **users**: Employee information and authentication
- **roles**: User role definitions
- **permissions**: System permissions
- **role_permissions**: Role-permission mapping
- **departments**: Organizational structure

### Operational Tables
- **attendance**: Time tracking data
- **leave_requests**: Leave applications and approvals
- **overtime_requests**: Overtime applications and approvals
- **payroll**: Payroll records and calculations
- **payslips**: Generated payslip files

### System Tables
- **activity_logs**: Audit trail of all system activities
- **user_invitations**: Employee invitation management

For detailed schema information, refer to [`db_schema.md`](db_schema.md).

## Testing

### Backend Tests

Run the backend test suite:
```bash
# From project root
pytest tests/
```

#### Test Coverage
- **API Endpoint Tests**: CRUD operations for all entities
- **Authentication Tests**: Login, registration, token validation
- **Permission Tests**: RBAC implementation verification
- **Service Tests**: Business logic validation

### Frontend Tests

Run the frontend test suite:
```bash
# From frontend directory
cd frontend
npm test
```

#### Test Coverage
- **Component Tests**: Individual component functionality
- **Integration Tests**: Component interaction
- **E2E Tests**: Full user workflows

### Test Data

The system includes comprehensive test data scripts:
- [`create_test_database.py`](create_test_database.py): Sets up test database
- [`test_app.py`](test_app.py): Application testing utilities
- [`conftest.py`](tests/conftest.py): pytest configuration

## Configuration

### Environment Variables

#### Backend (.env)
```env
# Database Configuration
DATABASE_URL=mysql://username:password@localhost:3306/alphahr_db

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application Configuration
DEBUG=False
CORS_ORIGINS=["http://localhost:3000"]
```

#### Python Dependencies

The backend requires the following Python packages (defined in [`requirements.txt`](requirements.txt)):

- **FastAPI** (0.104+): Modern web framework for building APIs
- **SQLAlchemy** (1.4.53): SQL toolkit and ORM
- **Alembic** (1.12.0): Database migration tool
- **PyMySQL** (1.1.0): MySQL database connector
- **PyJWT** (2.8.0): JWT token handling
- **bcrypt** (4.1.2): Password hashing
- **python-dotenv** (1.0.0): Environment variable management
- **uvicorn**: ASGI server for FastAPI
- **pytest** (8.0.0): Testing framework
- **httpx** (0.27.0): HTTP client for testing
- **reportlab** (4.0.4): PDF generation
- **openpyxl** (3.1.2): Excel file handling
- **pandas** (2.1.4): Data manipulation and analysis
- **PyPDF2** (3.0.1): PDF manipulation
- **loguru**: Advanced logging
- **cryptography** (41.0.7): Cryptographic functions
- **email-validator** (2.2.0): Email validation
- **python-multipart** (0.0.9): Form data parsing
- **psutil**: System and process utilities
- **requests**: HTTP library for API calls
- **schedule**: Task scheduling

**Note**: Legacy dependencies (Streamlit, Flask) have been removed from requirements.txt as all functionality has been migrated to the Next.js frontend.

#### Frontend (.env.local)
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Configuration
NEXT_PUBLIC_APP_NAME=AlphaHR
NEXT_PUBLIC_APP_VERSION=1.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_EXPORT=true
NEXT_PUBLIC_ENABLE_INVITATIONS=true
```

## Development Workflow

### Git Workflow

1. **Create feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and commit**
```bash
git add .
git commit -m "feat: add new feature description"
```

3. **Push and create pull request**
```bash
git push origin feature/your-feature-name
```

### Code Standards

- **Python**: Follow PEP 8 style guide
- **TypeScript**: Use ESLint and Prettier for formatting
- **Commits**: Follow conventional commit message format

### Database Migrations

1. **Create migration**
```bash
alembic revision --autogenerate -m "description of changes"
```

2. **Apply migration**
```bash
alembic upgrade head
```

## Deployment

### Production Environment Configuration

For production deployment:
1. Set strong JWT secrets
2. Configure MySQL database
3. Set up email services for notifications
4. Configure SSL certificates
5. Set up backup procedures

## Troubleshooting

### Common Issues

#### Backend Issues

**Problem**: Database connection errors
**Solution**:
1. Verify DATABASE_URL in .env file (should be MySQL format)
2. Check MySQL server status
3. Ensure database credentials are correct
4. Verify MySQL database exists and user has proper permissions

**Problem**: JWT authentication failures
**Solution**:
1. Verify JWT_SECRET is set
2. Check token expiration settings
3. Ensure frontend includes token in requests

#### Frontend Issues

**Problem**: API connection errors
**Solution**:
1. Verify NEXT_PUBLIC_API_URL
2. Check backend server status
3. Verify CORS configuration

**Problem**: Build failures
**Solution**:
1. Clear node_modules and reinstall
2. Check for TypeScript errors
3. Verify all dependencies are installed

#### Database Issues

**Problem**: Migration failures
**Solution**:
1. Check migration file syntax
2. Verify database state
3. Manually apply changes if needed

### Performance Optimization

1. **Database**: Add indexes for frequently queried columns
2. **API**: Implement pagination for large datasets
3. **Frontend**: Use React.memo for expensive components
4. **Caching**: Implement Redis for session storage

## Contributing

Please follow these guidelines when contributing to AlphaHR:

1. **Code Quality**: Ensure code passes all tests
2. **Documentation**: Update documentation for new features
3. **Commit Messages**: Use clear, descriptive commit messages
4. **Pull Requests**: Provide clear description of changes

## Support

For support and questions:
- Create an issue in the project repository
- Check existing documentation
- Review test files for implementation examples

## License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

## Changelog

### Version 0.0.1
- Initial release of AlphaHR
- Complete HR and payroll management system
- Full API documentation
- Comprehensive frontend implementation