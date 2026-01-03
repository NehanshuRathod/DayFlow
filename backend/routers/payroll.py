from fastapi import APIRouter, HTTPException, status, Depends
from models.schemas import SalaryStructure, UpdateSalaryRequest
from utils.db import get_db
from utils.auth_utils import get_current_user, require_admin_or_hr
from datetime import datetime

router = APIRouter()


def calculate_salary_components(monthly_wage: float, structure: dict) -> dict:
    """Calculate all salary components based on wage and percentages"""
    basic_percent = structure.get("basic_percent", 50.0)
    hra_percent = structure.get("hra_percent", 50.0)
    da_percent = structure.get("da_percent", 4.17)
    bonus_percent = structure.get("bonus_percent", 8.33)
    lta_percent = structure.get("lta_percent", 8.33)
    pf_percent = structure.get("pf_percent", 12.0)
    prof_tax = structure.get("prof_tax", 200.0)
    
    # Calculate amounts
    basic = monthly_wage * (basic_percent / 100)
    hra = basic * (hra_percent / 100)
    da = basic * (da_percent / 100)
    bonus = basic * (bonus_percent / 100)
    lta = basic * (lta_percent / 100)
    
    # Fixed allowance = wage - all calculated components
    fixed_allowance = monthly_wage - (basic + hra + da + bonus + lta)
    
    # Deductions
    pf_employee = basic * (pf_percent / 100)
    pf_employer = basic * (pf_percent / 100)
    
    # Net salary
    net_salary = monthly_wage - pf_employee - prof_tax
    
    return {
        "monthly_wage": monthly_wage,
        "yearly_wage": monthly_wage * 12,
        "basic_percent": basic_percent,
        "hra_percent": hra_percent,
        "da_percent": da_percent,
        "bonus_percent": bonus_percent,
        "lta_percent": lta_percent,
        "pf_percent": pf_percent,
        "prof_tax": prof_tax,
        "basic_amount": round(basic, 2),
        "hra_amount": round(hra, 2),
        "da_amount": round(da, 2),
        "bonus_amount": round(bonus, 2),
        "lta_amount": round(lta, 2),
        "fixed_allowance": round(max(0, fixed_allowance), 2),
        "pf_employee": round(pf_employee, 2),
        "pf_employer": round(pf_employer, 2),
        "net_salary": round(net_salary, 2)
    }


@router.get("/{employee_id}")
async def get_salary(employee_id: int, current_user: dict = Depends(get_current_user)):
    """Get employee's salary structure"""
    db = get_db()
    
    # Get user_id for the employee
    emp = db.table("employees").select("user_id, base_salary").eq("employee_id", employee_id).execute()
    
    if not emp.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    user_id = emp.data[0]["user_id"]
    
    # Check permissions (only admin/hr or self can view)
    if current_user["role"] not in ["admin", "hr"] and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own salary"
        )
    
    # Get salary structure
    structure = db.table("salary_structure").select("*").eq("employee_id", employee_id).execute()
    
    if not structure.data:
        # Return default structure based on base_salary
        base_salary = emp.data[0].get("base_salary") or 0
        return SalaryStructure(**calculate_salary_components(base_salary, {}))
    
    return SalaryStructure(**calculate_salary_components(
        structure.data[0]["monthly_wage"],
        structure.data[0]
    ))


@router.put("/{employee_id}")
async def update_salary(employee_id: int, request: UpdateSalaryRequest, current_user: dict = Depends(require_admin_or_hr)):
    """Update employee's salary structure (Admin/HR only)"""
    db = get_db()
    
    # Check if employee exists
    emp = db.table("employees").select("*").eq("employee_id", employee_id).execute()
    
    if not emp.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Prepare data
    salary_data = {
        "employee_id": employee_id,
        "monthly_wage": request.monthly_wage,
        "basic_percent": request.basic_percent,
        "hra_percent": request.hra_percent,
        "da_percent": request.da_percent,
        "bonus_percent": request.bonus_percent,
        "lta_percent": request.lta_percent,
        "pf_percent": request.pf_percent,
        "prof_tax": request.prof_tax,
        "updated_at": datetime.now().isoformat()
    }
    
    # Check if structure exists
    existing = db.table("salary_structure").select("id").eq("employee_id", employee_id).execute()
    
    if existing.data:
        # Update existing
        db.table("salary_structure").update(salary_data).eq("employee_id", employee_id).execute()
    else:
        # Insert new
        db.table("salary_structure").insert(salary_data).execute()
    
    # Also update base_salary in employees table
    db.table("employees").update({
        "base_salary": request.monthly_wage,
        "updated_at": datetime.now().isoformat()
    }).eq("employee_id", employee_id).execute()
    
    # Return calculated structure
    return SalaryStructure(**calculate_salary_components(
        request.monthly_wage,
        request.model_dump()
    ))
