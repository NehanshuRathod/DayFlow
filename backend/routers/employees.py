from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models.schemas import CreateEmployeeRequest, EmployeeResponse, UpdateEmployeeRequest
from utils.db import get_db
from utils.auth_utils import (
    hash_password, get_current_user, require_admin_or_hr, generate_random_password
)
from utils.generators import generate_employee_id
from datetime import datetime, date

router = APIRouter()


@router.get("", response_model=List[EmployeeResponse])
async def list_employees(current_user: dict = Depends(require_admin_or_hr)):
    """List all employees with their today's status (Admin/HR only)"""
    db = get_db()
    
    # Get all users with their employee details
    result = db.table("users").select(
        "user_id, employee_id, email, role, "
        "employees(first_name, last_name, phone, department, job_title, profile_picture_url, join_date)"
    ).neq("role", "admin").execute()
    
    employees = []
    today = date.today().isoformat()
    
    for user in result.data:
        emp = user.get("employees", {}) or {}
        
        # Get today's attendance status
        attendance = db.table("attendance").select("check_in, check_out").eq(
            "user_id", user["user_id"]
        ).eq("attendance_date", today).execute()
        
        # Check if on leave today
        leave = db.table("leave_requests").select("*").eq(
            "user_id", user["user_id"]
        ).eq("status", "approved").lte("start_date", today).gte("end_date", today).execute()
        
        # Determine status
        if leave.data:
            status_val = "leave"
        elif attendance.data and attendance.data[0].get("check_in"):
            status_val = "present"
        else:
            status_val = "absent"
        
        employees.append(EmployeeResponse(
            user_id=user["user_id"],
            employee_id=user["employee_id"],
            email=user["email"],
            role=user["role"],
            first_name=emp.get("first_name", ""),
            last_name=emp.get("last_name", ""),
            phone=emp.get("phone"),
            department=emp.get("department"),
            job_title=emp.get("job_title"),
            profile_picture_url=emp.get("profile_picture_url"),
            join_date=emp.get("join_date"),
            today_status=status_val
        ))
    
    return employees


@router.post("", response_model=dict)
async def create_employee(request: CreateEmployeeRequest, current_user: dict = Depends(require_admin_or_hr)):
    """Create a new employee (Admin/HR only). System generates ID and password."""
    db = get_db()
    
    # Check if email exists
    existing = db.table("users").select("*").eq("email", request.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get company prefix for ID generation
    company = db.table("company").select("prefix").limit(1).execute()
    company_prefix = company.data[0]["prefix"] if company.data else "DF"
    
    # Generate employee ID and password
    employee_id = generate_employee_id(
        company_prefix, 
        request.first_name, 
        request.last_name,
        request.join_date.year
    )
    temp_password = generate_random_password()
    
    # Create user
    user_result = db.table("users").insert({
        "email": request.email,
        "employee_id": employee_id,
        "password_hash": hash_password(temp_password),
        "role": request.role.value,
        "is_verified": True
    }).execute()
    
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    user_id = user_result.data[0]["user_id"]
    
    # Create employee profile
    db.table("employees").insert({
        "user_id": user_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone": request.phone,
        "department": request.department,
        "job_title": request.job_title,
        "join_date": request.join_date.isoformat(),
        "base_salary": request.base_salary
    }).execute()
    
    return {
        "message": "Employee created successfully",
        "employee_id": employee_id,
        "email": request.email,
        "temporary_password": temp_password  # Return this so admin can share with employee
    }


@router.get("/{user_id}")
async def get_employee(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get employee details. Employees can only view their own profile."""
    db = get_db()
    
    # Check if user can view this profile
    if current_user["role"] == "employee" and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    # Get user
    user_result = db.table("users").select("*").eq("user_id", user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = user_result.data[0]
    
    # Get employee details
    emp_result = db.table("employees").select("*").eq("user_id", user_id).execute()
    employee = emp_result.data[0] if emp_result.data else {}
    
    # Get salary structure if admin/hr or self
    salary = None
    if current_user["role"] in ["admin", "hr"] or current_user["user_id"] == user_id:
        salary_result = db.table("salary_structure").select("*").eq(
            "employee_id", employee.get("employee_id")
        ).execute()
        salary = salary_result.data[0] if salary_result.data else None
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "employee_id": user["employee_id"],
        "role": user["role"],
        **employee,
        "salary_structure": salary
    }


@router.put("/{user_id}")
async def update_employee(user_id: int, request: UpdateEmployeeRequest, current_user: dict = Depends(get_current_user)):
    """Update employee profile. Employees can edit limited fields, Admin can edit all."""
    db = get_db()
    
    # Check permissions
    is_admin = current_user["role"] in ["admin", "hr"]
    is_self = current_user["user_id"] == user_id
    
    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own profile"
        )
    
    # Build update data
    update_data = {}
    allowed_self_fields = ["phone", "address", "profile_picture_url", "about", "skills", "certifications"]
    
    for field, value in request.model_dump(exclude_unset=True).items():
        if value is not None:
            if is_admin or field in allowed_self_fields:
                update_data[field] = value
    
    if update_data:
        update_data["updated_at"] = datetime.now().isoformat()
        db.table("employees").update(update_data).eq("user_id", user_id).execute()
    
    return {"message": "Profile updated successfully"}


@router.get("/{user_id}/status")
async def get_employee_status(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get employee's today status (present/absent/leave)"""
    db = get_db()
    today = date.today().isoformat()
    
    # Check attendance
    attendance = db.table("attendance").select("*").eq(
        "user_id", user_id
    ).eq("attendance_date", today).execute()
    
    # Check leave
    leave = db.table("leave_requests").select("*").eq(
        "user_id", user_id
    ).eq("status", "approved").lte("start_date", today).gte("end_date", today).execute()
    
    if leave.data:
        return {"status": "leave", "leave_type": leave.data[0].get("leave_type")}
    elif attendance.data and attendance.data[0].get("check_in"):
        return {
            "status": "present",
            "check_in": attendance.data[0]["check_in"],
            "check_out": attendance.data[0].get("check_out")
        }
    else:
        return {"status": "absent"}
