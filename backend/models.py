from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.orm import declarative_base, relationship, synonym
import enum

Base = declarative_base()

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"

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
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    date_hired = Column(Date, nullable=False)
    status = Column(String(20), default=UserStatus.active.value)

    department = relationship("Department", back_populates="users")
    role_obj = relationship("Role", back_populates="users")
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

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    users = relationship("User", back_populates="role_obj")
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

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", back_populates="department")

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