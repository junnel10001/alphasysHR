# AlphaSys HR Payroll System

## Overview

AlphaSys is a Streamlit‑based HR and payroll system designed for managing employee information, attendance, overtime, and payroll processing. The backend is built with FastAPI and SQLAlchemy, and the frontend uses Next.js.

## Prerequisites

- Python 3.9 or higher
- Streamlit
- FastAPI
- bcrypt
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

```bash
git clone [repository_url]
cd AlphaSys
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file with any required environment variables (e.g., `DATABASE_URL`).  
   The project defaults to an SQLite database located at `./users.db`.

## Running the Application

### Backend (FastAPI)

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000`.

## Seeding the Database

A set of SQLite‑compatible seed scripts is provided to generate realistic dummy data for the KPI charts on the Admin Dashboard.

### Seed scripts

- `seed_roles_departments.py` – creates default roles, permissions, role‑permissions, and departments.
- `seed_leave_types.py` – inserts the default leave‑type lookup table.
- `seed_users.py` – creates an admin user and 10 demo employee users.
- `seed_attendance.py` – generates attendance records for the past 30 days per employee.
- `seed_payroll.py` – creates payroll entries for the last two pay periods per employee.
- `seed_leave_requests.py` – creates a mix of pending, approved, rejected, and cancelled leave requests.
- `seed_overtime_requests.py` – creates overtime requests with varied statuses.
- `seed_activity_logs.py` – adds a few activity‑log entries for the admin user (optional).

### Master seeder

All individual seeders are orchestrated by **`seed_all.py`**. To run the full seeding process:

```bash
python seed_all.py
```

The script will:

1. Create reference data (roles, permissions, departments, leave types).
2. Create the admin and demo users.
3. Populate attendance, payroll, leave requests, overtime requests, and activity logs.
4. Commit all changes to the SQLite database (`users.db`).

After seeding, start the backend and frontend as described above. The Admin Dashboard will display non‑zero KPI values.

## Testing

Run the test suite with:

```bash
pytest
```

## Employee Management UI

### Overview
The Employee Management page provides a searchable, filterable table of employees with pagination and total count display.

### Filter Toolbar
- **Department** – dropdown to filter employees by department.  
- **Role** – dropdown to filter by role.  
- **Status** – dropdown to filter by employment status (active, inactive, terminated).

### Pagination Controls
- Navigation buttons to move between pages.  
- Page size selector (10, 25, 50 rows per page).  
- Current page indicator and total pages display.

### Total Count Display
Shows the total number of employees matching the current filter criteria.

### Add Employee
Click the **“Add Employee”** button to open a modal form.  
Fields include name, email, department, role, and status.  
Submitting the form sends a `POST /employees` request and closes the modal on success.

### Edit / Delete Icons
- **Edit** (pencil icon) opens a pre‑filled modal for updating employee details, which triggers a `PUT /employees/{id}` request.
- **Delete** (trash icon) opens a confirmation dialog; confirming sends a `DELETE /employees/{id}` request.

---

## Backend API Documentation

| Method | Endpoint | Description | Request Body | Response Model | Required Permission |
|--------|----------|-------------|--------------|----------------|---------------------|
| `POST` | `/employees` | Create a new employee | `EmployeeCreate` schema | `EmployeeRead` | `create_employee` |
| `PUT` | `/employees/{id}` | Update an existing employee | `EmployeeCreate` (partial) | `EmployeeRead` | `update_employee` |
| `DELETE` | `/employees/{id}` | Delete an employee | – | – | `delete_employee` |

**Error Responses** (common to all endpoints):
- `400 Bad Request` – validation errors.  
- `404 Not Found` – employee ID does not exist.  
- `403 Forbidden` – insufficient permissions.

---

## Testing Documentation

- **Backend Tests**: CRUD endpoint tests covering creation, update, deletion, permission checks, and error handling.  
- **Frontend Tests**: UI tests for filter toolbar functionality, pagination behavior, total count accuracy, and modal interactions (add, edit, delete).  

These tests ensure the new employee management features work end‑to‑end and respect RBAC permissions.
## Contributing

Please see `CONTRIBUTING.md` (placeholder) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License – see `LICENSE.md` (placeholder) for details.