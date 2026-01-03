from fastapi import APIRouter, HTTPException, status, Depends
from models.schemas import (
    CompanySignupRequest, LoginRequest, TokenResponse, ChangePasswordRequest
)
from utils.db import get_db
from utils.auth_utils import (
    hash_password, verify_password, create_access_token, 
    get_current_user, generate_random_password
)
from utils.generators import generate_employee_id
from datetime import datetime

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup_company(request: CompanySignupRequest):
    """
    Register a new company with its first admin user.
    This is the initial setup - creates company and admin account.
    """
    db = get_db()
    
    # Check if email already exists
    existing = db.table("users").select("*").eq("email", request.admin_email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create company
    company_result = db.table("company").insert({
        "name": request.company_name,
        "prefix": request.company_prefix[:5].upper()
    }).execute()
    
    if not company_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )
    
    company_id = company_result.data[0]["company_id"]
    
    # Generate admin employee ID
    names = request.admin_name.split()
    first_name = names[0]
    last_name = names[-1] if len(names) > 1 else names[0]
    employee_id = generate_employee_id(request.company_prefix, first_name, last_name)
    
    # Create admin user
    user_result = db.table("users").insert({
        "email": request.admin_email,
        "employee_id": employee_id,
        "password_hash": hash_password(request.admin_password),
        "role": "admin",
        "is_verified": True
    }).execute()
    
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )
    
    user_id = user_result.data[0]["user_id"]
    
    # Create employee profile for admin
    db.table("employees").insert({
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "phone": request.admin_phone,
        "join_date": datetime.now().date().isoformat(),
        "department": "Administration",
        "job_title": "Administrator"
    }).execute()
    
    # Generate token
    token = create_access_token({
        "user_id": user_id,
        "email": request.admin_email,
        "employee_id": employee_id,
        "role": "admin"
    })
    
    return TokenResponse(
        access_token=token,
        user={
            "user_id": user_id,
            "email": request.admin_email,
            "employee_id": employee_id,
            "role": "admin",
            "name": request.admin_name
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email or employee ID and password.
    """
    db = get_db()
    
    # Try to find user by email or employee_id
    user = None
    if "@" in request.identifier:
        result = db.table("users").select("*").eq("email", request.identifier).execute()
    else:
        result = db.table("users").select("*").eq("employee_id", request.identifier.upper()).execute()
    
    if result.data:
        user = result.data[0]
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get employee details
    emp_result = db.table("employees").select("*").eq("user_id", user["user_id"]).execute()
    employee = emp_result.data[0] if emp_result.data else {}
    
    # Update last login
    db.table("users").update({"last_login": datetime.now().isoformat()}).eq("user_id", user["user_id"]).execute()
    
    # Generate token
    token = create_access_token({
        "user_id": user["user_id"],
        "email": user["email"],
        "employee_id": user["employee_id"],
        "role": user["role"]
    })
    
    return TokenResponse(
        access_token=token,
        user={
            "user_id": user["user_id"],
            "email": user["email"],
            "employee_id": user["employee_id"],
            "role": user["role"],
            "first_name": employee.get("first_name", ""),
            "last_name": employee.get("last_name", ""),
            "profile_picture_url": employee.get("profile_picture_url")
        }
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user details from JWT token"""
    db = get_db()
    
    user_result = db.table("users").select("*").eq("user_id", current_user["user_id"]).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = user_result.data[0]
    
    emp_result = db.table("employees").select("*").eq("user_id", user["user_id"]).execute()
    employee = emp_result.data[0] if emp_result.data else {}
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "employee_id": user["employee_id"],
        "role": user["role"],
        "is_verified": user["is_verified"],
        **employee
    }


@router.put("/change-password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change current user's password"""
    db = get_db()
    
    # Get current password hash
    user_result = db.table("users").select("password_hash").eq("user_id", current_user["user_id"]).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(request.current_password, user_result.data[0]["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    db.table("users").update({
        "password_hash": hash_password(request.new_password),
        "updated_at": datetime.now().isoformat()
    }).eq("user_id", current_user["user_id"]).execute()
    
    return {"message": "Password updated successfully"}
