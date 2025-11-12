from pydantic import BaseModel

class DepartmentSchema(BaseModel):
    department_id: int
    department_name: str

    class Config:
        from_attributes = True  # Pydantic v2 equivalent of orm_mode

class RoleSchema(BaseModel):
    role_id: int
    role_name: str

    class Config:
        from_attributes = True

class OfficeSchema(BaseModel):
    office_id: int
    office_name: str
    location: str | None = None

class PositionSchema(BaseModel):
    position_id: int
    position_name: str
    description: str | None = None
    department_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

class EmploymentStatusSchema(BaseModel):
    employment_status_id: int
    status_name: str
    description: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    user_id: int
    username: str
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True

# Import invitation schemas
from . import invitation