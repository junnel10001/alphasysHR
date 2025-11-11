from datetime import date
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class GenderEnum(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"


class CivilStatusEnum(str, Enum):
    single = "Single"
    married = "Married"
    widowed = "Widowed"
    divorced = "Divorced"


class EmploymentStatusEnum(str, Enum):
    regular = "Regular"
    probationary = "Probationary"
    contractual = "Contractual"
    project_based = "Project-Based"
    part_time = "Part-time"


class PaymentMethodEnum(str, Enum):
    atm = "ATM"
    cash = "Cash"
    cheque = "Cheque"


class EmployeeBase(BaseModel):
    company_id: str = Field(..., description="Company identifier")
    first_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., max_length=100)
    suffix: Optional[str] = Field(None, max_length=20)
    nickname: Optional[str] = Field(None, max_length=100)

    date_of_birth: Optional[date] = Field(None)
    place_of_birth: Optional[str] = Field(None, max_length=255)
    gender: Optional[GenderEnum] = None
    civil_status: Optional[CivilStatusEnum] = None
    nationality: Optional[str] = Field(None, max_length=100)
    blood_type: Optional[str] = Field(None, max_length=3)
    religion: Optional[str] = Field(None, max_length=100)

    mobile_number: Optional[str] = Field(None, max_length=20)
    landline_number: Optional[str] = Field(None, max_length=20)
    personal_email: Optional[EmailStr] = None

    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_number: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)

    job_title: Optional[str] = Field(None, max_length=100)
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    office_id: Optional[int] = None
    line_manager_id: Optional[int] = None
    employment_status: Optional[EmploymentStatusEnum] = None
    date_hired: Optional[date] = None
    date_regularised: Optional[date] = None

    basic_salary: Optional[float] = Field(None, gt=0)
    pay_frequency: Optional[str] = Field(None, max_length=20)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[PaymentMethodEnum] = None

    # Document uploads are stored as file paths or URLs
    resume_path: Optional[str] = None
    government_id_paths: Optional[List[str]] = None
    birth_certificate_path: Optional[str] = None
    marriage_certificate_path: Optional[str] = None
    diploma_path: Optional[str] = None

    @validator("date_regularised")
    def regularised_after_hired(cls, v, values):
        hired = values.get("date_hired")
        if v and hired and v < hired:
            raise ValueError("Date regularised must be after date hired")
        return v


class EmployeeCreate(EmployeeBase):
    """Schema for creating a new employee (system‑generated employee_id)."""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for partial updates; all fields optional."""
    company_id: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    nickname: Optional[str] = None

    date_of_birth: Optional[Union[date, str]] = None
    place_of_birth: Optional[str] = None
    gender: Optional[Union[GenderEnum, str]] = None
    civil_status: Optional[Union[CivilStatusEnum, str]] = None
    nationality: Optional[str] = None
    blood_type: Optional[str] = None
    religion: Optional[str] = None

    mobile_number: Optional[str] = None
    landline_number: Optional[str] = None
    personal_email: Optional[EmailStr] = None

    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    job_title: Optional[str] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    office_id: Optional[int] = None
    line_manager_id: Optional[int] = None
    employment_status: Optional[Union[EmploymentStatusEnum, str]] = None
    date_hired: Optional[Union[date, str]] = None
    date_regularised: Optional[Union[date, str]] = None

    basic_salary: Optional[float] = None
    pay_frequency: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    payment_method: Optional[Union[PaymentMethodEnum, str]] = None

    resume_path: Optional[str] = None
    government_id_paths: Optional[List[str]] = None
    birth_certificate_path: Optional[str] = None
    marriage_certificate_path: Optional[str] = None
    diploma_path: Optional[str] = None

    @validator('date_of_birth', 'date_hired', 'date_regularised', pre=True)
    def parse_empty_dates(cls, v):
        if v == "" or v is None:
            return None
        return v

    @validator('gender', 'civil_status', 'employment_status', 'payment_method', pre=True)
    def parse_empty_enums(cls, v):
        if v == "" or v is None:
            return None
        return v


class DepartmentOut(BaseModel):
    department_id: int
    department_name: str

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    role_id: int
    role_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeOut(EmployeeBase):
    """Schema returned from API – includes generated employee_id."""
    employee_id: int
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    department: Optional[DepartmentOut] = None
    role: Optional[RoleOut] = None

    class Config:
        from_attributes = True