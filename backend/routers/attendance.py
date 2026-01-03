from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from models.schemas import AttendanceRecord, AttendanceStats
from utils.db import get_db
from utils.auth_utils import get_current_user, require_admin_or_hr
from datetime import datetime, date, timedelta

router = APIRouter()


@router.post("/check-in")
async def check_in(current_user: dict = Depends(get_current_user)):
    """Record check-in for current user"""
    db = get_db()
    today = date.today().isoformat()
    now = datetime.now().isoformat()
    
    # Check if already checked in today
    existing = db.table("attendance").select("*").eq(
        "user_id", current_user["user_id"]
    ).eq("attendance_date", today).execute()
    
    if existing.data:
        if existing.data[0].get("check_in"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today"
            )
        # Update existing record
        db.table("attendance").update({
            "check_in": now
        }).eq("attendance_id", existing.data[0]["attendance_id"]).execute()
    else:
        # Create new record
        db.table("attendance").insert({
            "user_id": current_user["user_id"],
            "attendance_date": today,
            "check_in": now
        }).execute()
    
    return {"message": "Checked in successfully", "time": now}


@router.post("/check-out")
async def check_out(current_user: dict = Depends(get_current_user)):
    """Record check-out for current user"""
    db = get_db()
    today = date.today().isoformat()
    now = datetime.now().isoformat()
    
    # Get today's attendance
    existing = db.table("attendance").select("*").eq(
        "user_id", current_user["user_id"]
    ).eq("attendance_date", today).execute()
    
    if not existing.data or not existing.data[0].get("check_in"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You haven't checked in today"
        )
    
    if existing.data[0].get("check_out"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked out today"
        )
    
    # Update with check-out time
    db.table("attendance").update({
        "check_out": now
    }).eq("attendance_id", existing.data[0]["attendance_id"]).execute()
    
    return {"message": "Checked out successfully", "time": now}


@router.get("")
async def get_attendance(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user)
):
    """Get own attendance records"""
    db = get_db()
    
    query = db.table("attendance").select("*").eq("user_id", current_user["user_id"])
    
    if start_date:
        query = query.gte("attendance_date", start_date)
    if end_date:
        query = query.lte("attendance_date", end_date)
    
    result = query.order("attendance_date", desc=True).execute()
    
    records = []
    for r in result.data:
        work_hours = None
        if r.get("check_in") and r.get("check_out"):
            check_in = datetime.fromisoformat(r["check_in"].replace("Z", "+00:00"))
            check_out = datetime.fromisoformat(r["check_out"].replace("Z", "+00:00"))
            work_hours = round((check_out - check_in).total_seconds() / 3600, 2)
        
        records.append({
            **r,
            "work_hours": work_hours
        })
    
    return records


@router.get("/all")
async def get_all_attendance(
    attendance_date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    current_user: dict = Depends(require_admin_or_hr)
):
    """Get all employees' attendance for a date (Admin/HR only)"""
    db = get_db()
    
    target_date = attendance_date or date.today().isoformat()
    
    # Get all employees
    users_result = db.table("users").select(
        "user_id, employee_id, employees(first_name, last_name)"
    ).execute()
    
    # Get attendance for the date
    attendance_result = db.table("attendance").select("*").eq(
        "attendance_date", target_date
    ).execute()
    
    attendance_map = {a["user_id"]: a for a in attendance_result.data}
    
    records = []
    for user in users_result.data:
        emp = user.get("employees", {}) or {}
        att = attendance_map.get(user["user_id"], {})
        
        work_hours = None
        if att.get("check_in") and att.get("check_out"):
            check_in = datetime.fromisoformat(att["check_in"].replace("Z", "+00:00"))
            check_out = datetime.fromisoformat(att["check_out"].replace("Z", "+00:00"))
            work_hours = round((check_out - check_in).total_seconds() / 3600, 2)
        
        records.append({
            "user_id": user["user_id"],
            "employee_id": user["employee_id"],
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
            "check_in": att.get("check_in"),
            "check_out": att.get("check_out"),
            "work_hours": work_hours,
            "remarks": att.get("remarks")
        })
    
    return {"date": target_date, "records": records}


@router.get("/today")
async def get_today_attendance(current_user: dict = Depends(require_admin_or_hr)):
    """Get today's attendance summary (Admin/HR only)"""
    return await get_all_attendance(date.today().isoformat(), current_user)


@router.get("/stats")
async def get_attendance_stats(
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: dict = Depends(get_current_user)
):
    """Get attendance statistics for current user"""
    db = get_db()
    
    # Default to current month
    now = date.today()
    target_month = month or now.month
    target_year = year or now.year
    
    # Calculate date range
    start_date = date(target_year, target_month, 1)
    if target_month == 12:
        end_date = date(target_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(target_year, target_month + 1, 1) - timedelta(days=1)
    
    # Get attendance records
    attendance = db.table("attendance").select("*").eq(
        "user_id", current_user["user_id"]
    ).gte("attendance_date", start_date.isoformat()).lte(
        "attendance_date", end_date.isoformat()
    ).execute()
    
    # Get approved leaves
    leaves = db.table("leave_requests").select("*").eq(
        "user_id", current_user["user_id"]
    ).eq("status", "approved").gte(
        "start_date", start_date.isoformat()
    ).lte("end_date", end_date.isoformat()).execute()
    
    # Calculate stats
    days_present = 0
    total_work_hours = 0
    
    for a in attendance.data:
        if a.get("check_in"):
            days_present += 1
            if a.get("check_out"):
                check_in = datetime.fromisoformat(a["check_in"].replace("Z", "+00:00"))
                check_out = datetime.fromisoformat(a["check_out"].replace("Z", "+00:00"))
                total_work_hours += (check_out - check_in).total_seconds() / 3600
    
    days_leave = sum(l.get("days_requested", 0) for l in leaves.data)
    
    # Calculate working days (excluding weekends)
    total_working_days = 0
    current = start_date
    while current <= min(end_date, now):
        if current.weekday() < 5:  # Monday to Friday
            total_working_days += 1
        current += timedelta(days=1)
    
    days_absent = max(0, total_working_days - days_present - int(days_leave))
    
    # Extra hours (assuming 8 hours workday)
    expected_hours = days_present * 8
    extra_hours = round(max(0, total_work_hours - expected_hours), 2)
    
    return AttendanceStats(
        days_present=days_present,
        days_absent=days_absent,
        days_leave=int(days_leave),
        total_working_days=total_working_days,
        extra_hours=extra_hours
    )
