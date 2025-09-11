# AlphaSys HR Payroll System

## Overview

AlphaSys is a Streamlit-based HR and payroll system designed for managing employee information, attendance, overtime, and payroll processing.

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

3. (Optional) Create a `.env` file with any required environment variables (e.g., database URL).

## Running the Application

### Backend (FastAPI)

Start the FastAPI server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Frontend (Streamlit)

Start the Streamlit UI:

```bash
streamlit run frontend/app.py
```

The UI will be available at `http://localhost:8501`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/token` | Obtain JWT access token |
| `POST` | `/employees/` | Create a new employee |
| `GET` | `/employees/` | List all employees |
| `GET` | `/employees/{user_id}` | Retrieve a specific employee |
| `PUT` | `/employees/{user_id}` | Update an employee |
| `DELETE` | `/employees/{user_id}` | Delete an employee |
| `POST` | `/leaves/` | Create a leave request |
| `GET` | `/leaves/` | List leave requests |
| `GET` | `/leaves/{leave_id}` | Retrieve a specific leave request |
| `PUT` | `/leaves/{leave_id}` | Update a leave request |
| `DELETE` | `/leaves/{leave_id}` | Delete a leave request |
| `POST` | `/attendance/` | Record attendance |
| `GET` | `/attendance/` | List attendance records |
| `GET` | `/attendance/{attendance_id}` | Retrieve a specific attendance record |
| `PUT` | `/attendance/{attendance_id}` | Update an attendance record |
| `DELETE` | `/attendance/{attendance_id}` | Delete an attendance record |

## Testing

Run the test suite with:

```bash
pytest
```

The test suite includes unit and integration tests for both backend API endpoints and frontend utility functions.

## Contributing

Please see `CONTRIBUTING.md` (placeholder) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see `LICENSE.md` (placeholder) for details.