from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# ============ Enums ============
class UserRole(str, Enum):
    employee = "employee"
    hr = "hr"
    admin = "admin"


class LeaveType(str, Enum):
    paid = "paid"
    sick = "sick"
    unpaid = "unpaid"


class LeaveStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


# ============ Auth Schemas ============
class CompanySignupRequest(BaseModel):
    company_name: str
    company_prefix: str  # 2-5 chars for employee ID
    admin_name: str
    admin_email: EmailStr
    admin_phone: Optional[str] = None
    admin_password: str


class LoginRequest(BaseModel):
    identifier: str  # Email or Employee ID
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============ Employee Schemas ============
class CreateEmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole = UserRole.employee
    department: Optional[str] = None
    job_title: Optional[str] = None
    join_date: date
    base_salary: Optional[float] = None


class EmployeeResponse(BaseModel):
    user_id: int
    employee_id: str
    email: str
    role: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    profile_picture_url: Optional[str] = None
    join_date: Optional[date] = None
    today_status: Optional[str] = None  # present, absent, leave


class UpdateEmployeeRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    # Resume tab
    about: Optional[str] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    # Private info
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    pan_number: Optional[str] = None
    uan_number: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None


# ============ Attendance Schemas ============
class AttendanceRecord(BaseModel):
    attendance_id: int
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    work_hours: Optional[float] = None
    remarks: Optional[str] = None


class AttendanceStats(BaseModel):
    days_present: int
    days_absent: int
    days_leave: int
    total_working_days: int
    extra_hours: float


# ============ Leave Schemas ============
class CreateLeaveRequest(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    description: Optional[str] = None


class LeaveResponse(BaseModel):
    leave_id: int
    user_id: int
    employee_name: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    days_requested: float
    description: Optional[str] = None
    status: str
    created_at: datetime


# ============ Salary Schemas ============
class SalaryStructure(BaseModel):
    monthly_wage: float
    yearly_wage: Optional[float] = None
    basic_percent: float = 50.0
    hra_percent: float = 50.0  # % of basic
    da_percent: float = 4.17
    bonus_percent: float = 8.33
    lta_percent: float = 8.33
    pf_percent: float = 12.0
    prof_tax: float = 200.0
    # Calculated fields
    basic_amount: Optional[float] = None
    hra_amount: Optional[float] = None
    da_amount: Optional[float] = None
    bonus_amount: Optional[float] = None
    lta_amount: Optional[float] = None
    fixed_allowance: Optional[float] = None
    pf_employee: Optional[float] = None
    pf_employer: Optional[float] = None
    net_salary: Optional[float] = None


class UpdateSalaryRequest(BaseModel):
    monthly_wage: float
    basic_percent: Optional[float] = 50.0
    hra_percent: Optional[float] = 50.0
    da_percent: Optional[float] = 4.17
    bonus_percent: Optional[float] = 8.33
    lta_percent: Optional[float] = 8.33
    pf_percent: Optional[float] = 12.0
    prof_tax: Optional[float] = 200.0
