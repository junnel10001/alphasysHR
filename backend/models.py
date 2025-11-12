from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Text, TIMESTAMP, func, Boolean
from sqlalchemy.orm import declarative_base, relationship, synonym
import enum
import secrets
import string

Base = declarative_base()

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class InvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
    revoked = "revoked"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    id = synonym('user_id')  # alias for code expecting User.id
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone_number = Column(String(20))
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    role_id = Column(Integer, ForeignKey("roles.role_id"))
    role_name = Column(String(50), default="employee")  # role name for JWT
    status = Column(String(20), default=UserStatus.active.value)

    department = relationship("Department", back_populates="users")
    role_obj = relationship("Role", back_populates="users")
    # Many‑to‑many relationship to support multiple roles per user
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users_m2m",
    )
    attendance = relationship("Attendance", back_populates="user")
    payroll = relationship("Payroll", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    leave_requests = relationship(
        "LeaveRequest",
        back_populates="user",
        foreign_keys="[LeaveRequest.user_id]",
    )
    overtime_requests = relationship(
        "OvertimeRequest",
        back_populates="user",
        foreign_keys="[OvertimeRequest.user_id]",
    )
    invitations_sent = relationship("UserInvitation", back_populates="invited_by_user", foreign_keys="[UserInvitation.invited_by]")
    employee_profile = relationship("Employee", back_populates="user")

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    # One‑to‑many relationship (existing foreign key)
    users = relationship("User", back_populates="role_obj")
    employees = relationship("Employee", back_populates="role")
    # Many‑to‑many relationship for RBAC
    users_m2m = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
    )

class Permission(Base):
    __tablename__ = "permissions"

    permission_id = Column(Integer, primary_key=True, index=True)
    permission_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.permission_id"), primary_key=True)

# ----------------------------------------------------------------------
# Association table for many‑to‑many User ↔ Role
# ----------------------------------------------------------------------
class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", back_populates="department")
    employees = relationship("Employee", back_populates="department")

class AttendanceStatus(str, enum.Enum):
    Present = "Present"
    Late = "Late"
    Absent = "Absent"
    OnLeave = "On Leave"
    Overtime = "Overtime"

class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    time_in = Column(TIMESTAMP)
    time_out = Column(TIMESTAMP)
    hours_worked = Column(Numeric(5, 2))
    status = Column(String(20))

    user = relationship("User", back_populates="attendance")

class Payroll(Base):
    __tablename__ = "payroll"

    payroll_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    cutoff_start = Column(Date, nullable=False)
    cutoff_end = Column(Date, nullable=False)
    basic_pay = Column(Numeric(10, 2), nullable=False)
    overtime_pay = Column(Numeric(10, 2), default=0)
    deductions = Column(Numeric(10, 2), default=0)
    net_pay = Column(Numeric(10, 2), nullable=False)
    generated_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="payroll")

class Payslip(Base):
    __tablename__ = "payslips"

    payslip_id = Column(Integer, primary_key=True, index=True)
    payroll_id = Column(Integer, ForeignKey("payroll.payroll_id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    generation_status = Column(String(20), default="pending")  # pending, generated, failed
    download_count = Column(Integer, default=0)  # Number of times downloaded
    generated_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class LeaveType(Base):
    __tablename__ = "leave_types"

    leave_type_id = Column(Integer, primary_key=True, index=True)
    leave_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    default_allocation = Column(Integer, nullable=False)

class LeaveStatus(str, enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"
    Cancelled = "Cancelled"

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    leave_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.leave_type_id"), nullable=False)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default=LeaveStatus.Pending.value)
    approver_id = Column(Integer, ForeignKey("users.user_id"))
    approved_at = Column(TIMESTAMP)

    user = relationship(
        "User",
        back_populates="leave_requests",
        foreign_keys=[user_id],
    )
    leave_type = relationship("LeaveType")
    approver = relationship("User", foreign_keys=[approver_id])

class OvertimeStatus(str, enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"

class OvertimeRequest(Base):
    __tablename__ = "overtime_requests"

    ot_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    hours_requested = Column(Numeric(4, 2), nullable=False)
    reason = Column(Text)
    status = Column(String(20), default=OvertimeStatus.Pending.value)
    approver_id = Column(Integer, ForeignKey("users.user_id"))
    approved_at = Column(TIMESTAMP)

    user = relationship(
        "User",
        back_populates="overtime_requests",
        foreign_keys=[user_id],
    )
    approver = relationship("User", foreign_keys=[approver_id])

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    action = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="activity_logs")
# ----------------------------------------------------------------------
# Office and Employee models
# ----------------------------------------------------------------------
class Office(Base):
    __tablename__ = "offices"

    office_id = Column(Integer, primary_key=True, index=True)
    office_name = Column(String(100), unique=True, nullable=False)
    location = Column(String(255), nullable=True)

    # relationship to employees (optional)
    employees = relationship("Employee", back_populates="office")


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)

    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    suffix = Column(String(20), nullable=True)
    nickname = Column(String(100), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    place_of_birth = Column(String(255), nullable=True)
    gender = Column(String(20), nullable=True)
    civil_status = Column(String(20), nullable=True)
    nationality = Column(String(100), nullable=True)
    blood_type = Column(String(3), nullable=True)
    religion = Column(String(100), nullable=True)

    mobile_number = Column(String(20), nullable=True)
    landline_number = Column(String(20), nullable=True)
    personal_email = Column(String(150), nullable=True)

    current_address = Column(Text, nullable=True)
    permanent_address = Column(Text, nullable=True)

    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_number = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)

    job_title = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=True)
    office_id = Column(Integer, ForeignKey("offices.office_id"), nullable=True)
    line_manager_id = Column(Integer, nullable=True)  # Remove foreign key for now

    employment_status = Column(String(20), nullable=True)
    date_hired = Column(Date, nullable=True)
    date_regularised = Column(Date, nullable=True)

    basic_salary = Column(Numeric(10, 2), nullable=True)
    pay_frequency = Column(String(20), nullable=True)

    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    payment_method = Column(String(20), nullable=True)

    # Document file paths (optional)
    resume_path = Column(String(255), nullable=True)
    government_id_paths = Column(Text, nullable=True)  # could store JSON list
    birth_certificate_path = Column(String(255), nullable=True)
    marriage_certificate_path = Column(String(255), nullable=True)
    diploma_path = Column(String(255), nullable=True)

    # Relationships
    department = relationship("Department", back_populates="employees")
    role = relationship("Role", back_populates="employees")
    office = relationship("Office", back_populates="employees")
    # line_manager = relationship("User", foreign_keys=[line_manager_id])  # Commented out for now
    
    # Link to user account
    user = relationship("User", back_populates="employee_profile")

# ----------------------------------------------------------------------
# UserInvitation model
# ----------------------------------------------------------------------
class UserInvitation(Base):
    __tablename__ = "user_invitations"

    invitation_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    invited_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    employee_profile_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    status = Column(String(20), default=InvitationStatus.pending.value, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    accepted_at = Column(TIMESTAMP, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    invited_by_user = relationship("User", back_populates="invitations_sent", foreign_keys=[invited_by])
    role = relationship("Role")
    department = relationship("Department")
    employee_profile = relationship("Employee")

    def __repr__(self):
        return f"<UserInvitation(email={self.email}, status={self.status})>"
    
    @staticmethod
    def generate_token():
        """Generate a secure random token for invitation"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))

# ----------------------------------------------------------------------
# Position and Employment Status models
# ----------------------------------------------------------------------
class Position(Base):
    __tablename__ = "positions"

    position_id = Column(Integer, primary_key=True, index=True)
    position_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    department = relationship("Department")


class EmploymentStatus(Base):
    __tablename__ = "employment_statuses"

    employment_status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())