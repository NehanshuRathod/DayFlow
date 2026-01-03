"""
DayFlow HRMS - Database Initialization & Dummy Data Script
Run this script to reset the database and insert sample data for testing.

Usage:
    cd db
    python dummyinsert.py
"""

import os
import sys
from datetime import datetime, date, timedelta
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    sys.exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Password hashing using bcrypt directly
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def clear_tables():
    """Clear all data from tables (in correct order due to foreign keys)"""
    print("🗑️  Clearing existing data...")
    
    # Tables in order (children before parents due to foreign keys)
    tables_with_pk = [
        ('salary_structure', 'id'),
        ('employee_documents', 'id'),
        ('payroll', 'payroll_id'),
        ('leave_requests', 'leave_id'),
        ('attendance', 'attendance_id'),
        ('employees', 'employee_id'),
        ('users', 'user_id'),
        ('company', 'company_id')
    ]
    
    for table, pk in tables_with_pk:
        try:
            # Delete all records using the correct primary key
            supabase.table(table).delete().gte(pk, 0).execute()
            print(f"   ✓ Cleared {table}")
        except Exception as e:
            error_msg = str(e)
            if 'PGRST204' in error_msg:
                # No rows to delete - this is OK
                print(f"   ✓ {table} (already empty)")
            elif 'PGRST205' in error_msg or 'Could not find' in error_msg:
                print(f"   ⏭ Skipped {table} (table not found)")
            else:
                print(f"   ⚠ {table}: {error_msg[:60]}")


def create_company():
    """Create a sample company"""
    print("\n🏢 Creating company...")
    
    try:
        result = supabase.table('company').insert({
            'name': 'Odoo India Pvt Ltd',
            'prefix': 'OI',
            'logo_url': None
        }).execute()
        
        company_id = result.data[0]['company_id']
        print(f"   ✓ Created company: Odoo India (ID: {company_id})")
        return company_id
    except Exception as e:
        if 'PGRST205' in str(e):
            print("   ⏭ Skipped (company table not found - run updated schema.sql)")
            return None
        raise


def create_users_and_employees():
    """Create sample users and their employee profiles"""
    print("\n👥 Creating users and employees...")
    
    users_data = [
        {
            'email': 'admin@odoo.in',
            'employee_id': 'OIAD20250001',
            'password': 'admin123',
            'role': 'admin',
            'first_name': 'Rahul',
            'last_name': 'Sharma',
            'department': 'Administration',
            'job_title': 'System Administrator',
            'phone': '+91 98765 43210',
            'base_salary': 75000
        },
        {
            'email': 'hr@odoo.in',
            'employee_id': 'OIHR20250002',
            'password': 'hr123456',
            'role': 'hr',
            'first_name': 'Priya',
            'last_name': 'Patel',
            'department': 'Human Resources',
            'job_title': 'HR Manager',
            'phone': '+91 98765 43211',
            'base_salary': 65000
        },
        {
            'email': 'john.doe@odoo.in',
            'employee_id': 'OIJD20250003',
            'password': 'john1234',
            'role': 'employee',
            'first_name': 'John',
            'last_name': 'Doe',
            'department': 'Engineering',
            'job_title': 'Software Developer',
            'phone': '+91 98765 43212',
            'base_salary': 55000
        },
        {
            'email': 'jane.smith@odoo.in',
            'employee_id': 'OIJS20250004',
            'password': 'jane1234',
            'role': 'employee',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'department': 'Engineering',
            'job_title': 'Senior Developer',
            'phone': '+91 98765 43213',
            'base_salary': 70000
        },
        {
            'email': 'amit.kumar@odoo.in',
            'employee_id': 'OIAK20250005',
            'password': 'amit1234',
            'role': 'employee',
            'first_name': 'Amit',
            'last_name': 'Kumar',
            'department': 'Sales',
            'job_title': 'Sales Executive',
            'phone': '+91 98765 43214',
            'base_salary': 45000
        },
        {
            'email': 'neha.gupta@odoo.in',
            'employee_id': 'OING20250006',
            'password': 'neha1234',
            'role': 'employee',
            'first_name': 'Neha',
            'last_name': 'Gupta',
            'department': 'Marketing',
            'job_title': 'Marketing Specialist',
            'phone': '+91 98765 43215',
            'base_salary': 50000
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        # Create user
        user_result = supabase.table('users').insert({
            'email': user_data['email'],
            'employee_id': user_data['employee_id'],
            'password_hash': hash_password(user_data['password']),
            'role': user_data['role'],
            'is_verified': True
        }).execute()
        
        user_id = user_result.data[0]['user_id']
        
        # Create employee profile (only base schema fields)
        emp_result = supabase.table('employees').insert({
            'user_id': user_id,
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'phone': user_data['phone'],
            'department': user_data['department'],
            'job_title': user_data['job_title'],
            'join_date': '2025-01-01',
            'base_salary': user_data['base_salary'],
            'date_of_birth': '1990-05-15',
            'gender': random.choice(['male', 'female']),
            'address': 'Mumbai, Maharashtra, India',
            'bank_account': f"1234567890{user_id}"
        }).execute()
        
        employee_id = emp_result.data[0]['employee_id']
        
        created_users.append({
            'user_id': user_id,
            'employee_id': employee_id,
            'employee_id_str': user_data['employee_id'],
            'name': f"{user_data['first_name']} {user_data['last_name']}",
            'base_salary': user_data['base_salary']
        })
        
        print(f"   ✓ Created: {user_data['first_name']} {user_data['last_name']} ({user_data['role']})")
    
    return created_users


def create_attendance(users):
    """Create attendance records for the past 10 days"""
    print("\n📅 Creating attendance records...")
    
    today = date.today()
    
    for user in users:
        for days_ago in range(10):
            record_date = today - timedelta(days=days_ago)
            
            # Skip weekends
            if record_date.weekday() >= 5:
                continue
            
            # Random attendance pattern (90% present)
            if random.random() < 0.9:
                check_in_hour = random.randint(8, 10)
                check_in_min = random.randint(0, 59)
                check_out_hour = random.randint(17, 19)
                check_out_min = random.randint(0, 59)
                
                check_in = datetime.combine(record_date, datetime.min.time().replace(
                    hour=check_in_hour, minute=check_in_min
                ))
                check_out = datetime.combine(record_date, datetime.min.time().replace(
                    hour=check_out_hour, minute=check_out_min
                ))
                
                try:
                    supabase.table('attendance').insert({
                        'user_id': user['user_id'],
                        'attendance_date': record_date.isoformat(),
                        'check_in': check_in.isoformat(),
                        'check_out': check_out.isoformat()
                    }).execute()
                except:
                    pass  # Skip if duplicate
    
    print(f"   ✓ Created attendance for {len(users)} employees (past 10 days)")


def create_leave_requests(users):
    """Create sample leave requests"""
    print("\n🏖️  Creating leave requests...")
    
    leave_types = ['paid', 'sick', 'unpaid']
    statuses = ['pending', 'approved', 'rejected']
    
    # Create 2-3 leave requests per non-admin user
    for user in users[2:]:  # Skip admin and HR
        num_leaves = random.randint(2, 3)
        
        for i in range(num_leaves):
            start_offset = random.randint(5, 30)
            duration = random.randint(1, 3)
            
            start_date = date.today() + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=duration - 1)
            
            try:
                supabase.table('leave_requests').insert({
                    'user_id': user['user_id'],
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days_requested': duration,
                    'is_paid': random.choice([True, False]),
                    'description': random.choice([
                        'Personal work',
                        'Family function',
                        'Medical appointment',
                        'Travel plans'
                    ]),
                    'status': random.choice(statuses)
                }).execute()
            except:
                pass
    
    print(f"   ✓ Created leave requests for employees")


def create_salary_structure(users):
    """Create salary structure for employees"""
    print("\n💰 Creating salary structures...")
    
    count = 0
    for user in users:
        monthly_wage = user['base_salary']
        
        try:
            supabase.table('salary_structure').insert({
                'employee_id': user['employee_id'],
                'monthly_wage': monthly_wage,
                'basic_percent': 50.0,
                'hra_percent': 50.0,
                'da_percent': 4.17,
                'bonus_percent': 8.33,
                'lta_percent': 8.33,
                'pf_percent': 12.0,
                'prof_tax': 200.0
            }).execute()
            count += 1
        except Exception as e:
            if 'PGRST205' in str(e):
                print("   ⏭ Skipped (salary_structure table not found)")
                return
    
    print(f"   ✓ Created salary structures for {count} employees")


def print_credentials(users):
    """Print login credentials for testing"""
    print("\n" + "="*60)
    print("🔐 LOGIN CREDENTIALS FOR TESTING")
    print("="*60)
    
    creds = [
        ('Admin', 'admin@odoo.in', 'admin123'),
        ('HR', 'hr@odoo.in', 'hr123456'),
        ('Employee', 'john.doe@odoo.in', 'john1234'),
    ]
    
    for role, email, password in creds:
        print(f"\n{role}:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
    
    print("\n" + "="*60)


def main():
    print("\n" + "="*60)
    print("🚀 DayFlow HRMS - Database Initialization")
    print("="*60)
    
    try:
        # Clear existing data
        clear_tables()
        
        # Create fresh data
        company_id = create_company()
        users = create_users_and_employees()
        
        if users:
            create_attendance(users)
            create_leave_requests(users)
            create_salary_structure(users)
            
            # Print credentials
            print_credentials(users)
            
            print("\n✅ Database initialization complete!")
            print("   You can now test the application.\n")
        else:
            print("\n❌ No users were created. Please check the errors above.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
