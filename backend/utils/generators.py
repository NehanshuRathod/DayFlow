from datetime import datetime
from utils.db import get_db


def generate_employee_id(company_prefix: str, first_name: str, last_name: str, join_year: int = None) -> str:
    """
    Generate employee ID in format: XXYYZZZZ####
    - XX = Company prefix (2 chars)
    - YY = First letter of first name + first letter of last name
    - ZZZZ = Year of joining
    - #### = Serial number (0001, 0002, etc.)
    
    Example: OIJODO20220001
    """
    if join_year is None:
        join_year = datetime.now().year
    
    # Get first 2 chars of company prefix (uppercase)
    company_code = company_prefix[:2].upper()
    
    # Get first letters of first and last name
    name_code = (first_name[0] + last_name[0]).upper()
    
    # Year as 4 digits
    year_code = str(join_year)
    
    # Get next serial number for this year
    db = get_db()
    prefix = f"{company_code}{name_code}{year_code}"
    
    # Count existing employees with same prefix pattern
    result = db.table("users").select("employee_id").like("employee_id", f"{prefix}%").execute()
    serial = len(result.data) + 1
    serial_code = str(serial).zfill(4)
    
    return f"{prefix}{serial_code}"
