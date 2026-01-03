from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from models.schemas import CreateLeaveRequest, LeaveResponse
from utils.db import get_db
from utils.auth_utils import get_current_user, require_admin_or_hr
from datetime import datetime, date

router = APIRouter()


@router.post("")
async def apply_leave(request: CreateLeaveRequest, current_user: dict = Depends(get_current_user)):
    """Apply for leave"""
    db = get_db()
    
    # Validate dates
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )
    
    if request.start_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply for leave in the past"
        )
    
    # Calculate days
    days = (request.end_date - request.start_date).days + 1
    
    # Determine if paid based on leave type
    is_paid = request.leave_type.value != "unpaid"
    
    # Create leave request
    result = db.table("leave_requests").insert({
        "user_id": current_user["user_id"],
        "leave_type": request.leave_type.value,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "days_requested": days,
        "is_paid": is_paid,
        "description": request.description,
        "status": "pending"
    }).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create leave request"
        )
    
    return {"message": "Leave request submitted successfully", "leave_id": result.data[0]["leave_id"]}


@router.get("")
async def get_leaves(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    current_user: dict = Depends(get_current_user)
):
    """Get own leave requests"""
    db = get_db()
    
    query = db.table("leave_requests").select("*").eq("user_id", current_user["user_id"])
    
    if status_filter:
        query = query.eq("status", status_filter)
    
    result = query.order("created_at", desc=True).execute()
    
    return result.data


@router.get("/pending")
async def get_pending_leaves(current_user: dict = Depends(require_admin_or_hr)):
    """Get all pending leave requests (Admin/HR only)"""
    db = get_db()
    
    result = db.table("leave_requests").select(
        "*, users(employee_id, employees(first_name, last_name))"
    ).eq("status", "pending").order("created_at", desc=True).execute()
    
    leaves = []
    for leave in result.data:
        user = leave.get("users", {}) or {}
        emp = user.get("employees", {}) or {}
        
        leaves.append({
            **leave,
            "employee_id": user.get("employee_id"),
            "employee_name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        })
    
    return leaves


@router.get("/all")
async def get_all_leaves(
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin_or_hr)
):
    """Get all leave requests (Admin/HR only)"""
    db = get_db()
    
    query = db.table("leave_requests").select(
        "*, users(employee_id, employees(first_name, last_name))"
    )
    
    if status_filter:
        query = query.eq("status", status_filter)
    
    result = query.order("created_at", desc=True).execute()
    
    leaves = []
    for leave in result.data:
        user = leave.get("users", {}) or {}
        emp = user.get("employees", {}) or {}
        
        leaves.append({
            **leave,
            "employee_id": user.get("employee_id"),
            "employee_name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        })
    
    return leaves


@router.put("/{leave_id}/approve")
async def approve_leave(leave_id: int, current_user: dict = Depends(require_admin_or_hr)):
    """Approve a leave request (Admin/HR only)"""
    db = get_db()
    
    # Check if leave exists and is pending
    leave = db.table("leave_requests").select("*").eq("leave_id", leave_id).execute()
    
    if not leave.data:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.data[0]["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave request already {leave.data[0]['status']}"
        )
    
    # Update status
    db.table("leave_requests").update({
        "status": "approved",
        "approver_id": current_user["user_id"],
        "updated_at": datetime.now().isoformat()
    }).eq("leave_id", leave_id).execute()
    
    return {"message": "Leave request approved"}


@router.put("/{leave_id}/reject")
async def reject_leave(leave_id: int, current_user: dict = Depends(require_admin_or_hr)):
    """Reject a leave request (Admin/HR only)"""
    db = get_db()
    
    # Check if leave exists and is pending
    leave = db.table("leave_requests").select("*").eq("leave_id", leave_id).execute()
    
    if not leave.data:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.data[0]["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave request already {leave.data[0]['status']}"
        )
    
    # Update status
    db.table("leave_requests").update({
        "status": "rejected",
        "approver_id": current_user["user_id"],
        "updated_at": datetime.now().isoformat()
    }).eq("leave_id", leave_id).execute()
    
    return {"message": "Leave request rejected"}
