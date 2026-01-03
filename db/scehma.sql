-- 1. Enums
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other', 'prefer_not_to_say');
CREATE TYPE user_role_enum AS ENUM ('employee', 'hr', 'admin');
CREATE TYPE leave_status_enum AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE payroll_status_enum AS ENUM ('pending', 'paid', 'processed');

-- 2. Users / Authentication
CREATE TABLE users (
    user_id         BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    employee_id     VARCHAR(50) UNIQUE,               -- can be NULL for admin-only users
    password_hash   VARCHAR(255) NOT NULL,
    role            user_role_enum NOT NULL DEFAULT 'employee',
    is_verified     BOOLEAN DEFAULT FALSE,            
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now(),
    last_login      TIMESTAMP NULL
);

-- 3. Employee Profile
CREATE TABLE employees (
    employee_id         BIGSERIAL PRIMARY KEY,
    user_id             BIGINT UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    date_of_birth       DATE,
    gender              gender_enum,
    phone               VARCHAR(30),
    address             TEXT,
    profile_picture_url VARCHAR(500),
    join_date           DATE NOT NULL,
    department          VARCHAR(100),
    job_title           VARCHAR(150),
    base_salary         NUMERIC(12,2),
    bank_account        VARCHAR(100),
    created_at          TIMESTAMP DEFAULT now(),
    updated_at          TIMESTAMP DEFAULT now()
);

-- 4. Attendance Records
CREATE TABLE attendance (
    attendance_id   BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in        TIMESTAMP NULL,
    check_out       TIMESTAMP NULL,
    remarks         TEXT,
    UNIQUE(user_id, attendance_date)
);

CREATE INDEX idx_attendance_user_date ON attendance(user_id, attendance_date);

-- 5. Leave Requests
CREATE TABLE leave_requests (
    leave_id        BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    days_requested  NUMERIC(4,1) NOT NULL,
    is_paid         BOOLEAN DEFAULT TRUE,
    description     TEXT,
    status          leave_status_enum NOT NULL DEFAULT 'pending',
    approver_id     BIGINT REFERENCES users(user_id),
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_leave_user_status ON leave_requests(user_id, status);

-- 6. Payroll / Salary
CREATE TABLE payroll (
    payroll_id      BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    pay_period      VARCHAR(50) NOT NULL,             -- e.g. "2025-12"
    base_salary     NUMERIC(12,2) NOT NULL,
    gross_salary    NUMERIC(12,2) NOT NULL,
    deductions      NUMERIC(12,2) DEFAULT 0,
    net_salary      NUMERIC(12,2) NOT NULL,
    payment_date    DATE,
    status          payroll_status_enum DEFAULT 'pending',
    payslip_url     VARCHAR(500),
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_payroll_user_period ON payroll(user_id, pay_period);

-- 7. Employee Documents
CREATE TABLE employee_documents (
    id              BIGSERIAL PRIMARY KEY,
    employee_id     BIGINT NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    document_type   VARCHAR(100) NOT NULL,
    file_url        VARCHAR(500) NOT NULL,
    uploaded_at     TIMESTAMP DEFAULT now(),
    uploaded_by     BIGINT NOT NULL REFERENCES employees(employee_id)
);

CREATE INDEX idx_documents_employee ON employee_documents(employee_id);
