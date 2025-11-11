import streamlit as st
import bcrypt
from datetime import datetime
from backend.database import engine, SessionLocal
from backend.models import Base, User, Role


# User model imported from backend.models


# Create tables
Base.metadata.create_all(bind=engine)


def _init_admin():
    """Create a default admin user if none exists."""
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        # bcrypt hash for password "admin123"
        admin_hash = b"$2b$12$fxiFcZwyoOd6Db2uUxDyMurj2PMLkyulTjRXjPk4bpEmonIpUMqPi".decode()
        # Ensure the admin role exists
        admin_role = db.query(Role).filter(Role.role_name == "admin").first()
        if not admin_role:
            admin_role = Role(role_name="admin", description="Administrator with full access")
            db.add(admin_role)
            db.flush()
        # Provide required fields with placeholder values and assign role
        admin_user = User(
            username="admin",
            password_hash=admin_hash,
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            hourly_rate=0.0,
            date_hired=datetime.utcnow().date(),
            status="active",
            role_name="admin",
            role_id=admin_role.role_id,
            role_obj=admin_role
        )
        # Assign many‑to‑many admin role
        admin_user.roles = [admin_role]
        db.add(admin_user)
        db.commit()
        db.add(admin_user)
        db.commit()
    db.close()


# Ensure admin account exists
_init_admin()

# ----------------------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------------------
st.title("AlphaSys HR Payroll System")

# Initialise session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["username"] = None


def login(username: str, password: str) -> bool:
    """Authenticate against the local SQLite DB."""
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        # Simple role assignment – admin user gets admin role
        st.session_state["role"] = "admin" if username == "admin" else "employee"
        st.success("Login successful")
        return True
    else:
        st.error("Invalid credentials")
        return False


def has_permission(required_role: str) -> bool:
    """Utility used by tests and UI to check role permissions."""
    return st.session_state.get("role") == required_role


# Expose to Streamlit namespace for test imports
st.has_permission = has_permission

# ----------------------------------------------------------------------
# Authentication flow
# ----------------------------------------------------------------------
if not st.session_state["logged_in"]:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(username, password)
else:
    # Navigation sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Page", ["Dashboard", "Employees", "Leaves", "Attendance"])

    st.write(f"Welcome, {st.session_state.get('username')} ({st.session_state.get('role')})!")

    if page == "Dashboard":
        st.header("Dashboard")
        st.write("Dashboard content goes here.")
    elif page == "Employees":
        st.header("Employees")
        st.write("Employee management UI.")
    elif page == "Leaves":
        st.header("Leaves")
        st.write("Leave management UI.")
    elif page == "Attendance":
        st.header("Attendance")
        st.write("Attendance UI.")
