# DayFlow HRMS

**DayFlow** is a modern, lightweight Human Resource Management System (HRMS) built with **FastAPI** (Backend) and **Vanilla HTML/JS** (Frontend). It maps every workday to a unified flow, handling employees, attendance, leaves, and payroll.

## 🚀 Features

- **Authentication:** Secure login for Admins, HR, and Employees (JWT-based).
- **Role-Based Access:** 
  - **Admin/HR:** Manage employees, approve leaves, payroll management.
  - **Employees:** Check-in/out, apply for leaves, view profile & salary.
- **Attendance:** Real-time check-in/out widget with daily logs.
- **Leave Management:** Apply, approve, and reject leave requests.
- **Payroll:** Automated salary component calculation (Basic, HRA, DA, PF, etc.).
- **Dashboard:** Responsive UI with dark/light mode aesthetics.

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI, Supabase (PostgreSQL), PyJWT, Bcrypt
- **Frontend:** HTML5, TailwindCSS (CDN), Vanilla JavaScript
- **Database:** Supabase (Cloud PostgreSQL)

## 📂 Project Structure

```
DayFlow/
├── backend/                    # Core API Logic
│   ├── main.py                 # App entry point & Router inclusion
│   ├── routers/                # API Endpoints (Auth, Employees, etc.)
│   ├── models/                 # Pydantic Schemas
│   └── utils/                  # DB connection & Helpers
├── frontend/                   # Minimal UI
│   ├── index.html              # Login Page
│   ├── dashboard.html          # Main Dashboard
│   └── js/                     # Application Logic
└── db/                         # Database Scripts
    ├── scehma.sql              # Database Setup SQL
    └── dummyinsert.py          # Test Data Generator
```

## ⚙️ Setup Instructions

### 1. Database Setup (Supabase)
1. Create a project on [Supabase](https://supabase.com).
2. Go to **SQL Editor** and run the contents of `db/scehma.sql`.
3. Note your `SUPABASE_URL` and `SUPABASE_KEY`.

### 2. Backend Setup
Navigate to the `backend` directory:
```bash
cd backend
```

Create a `.env` file in the project root (or update existing) with:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET=your_secret_key
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the Server:
```bash
uvicorn main:app --reload --port 8000
```
*The backend must be running for the frontend to work.*

### 3. Initialize Dummy Data (Optional)
To pre-fill the database with a company, admin, and simple data:
```bash
cd db
python dummyinsert.py
```

### 4. Running the Frontend
Since this is a static frontend, you can simply open the file in your browser:
*   Open `frontend/index.html`

or serve via the backend static mount:
*   Visit `http://localhost:8000/static/index.html`

## 🔐 Default Credentials (if using dummyinsert.py)

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@odoo.in` | `admin123` |
| **HR** | `hr@odoo.in` | `hr123456` |
| **Employee** | `john.doe@odoo.in` | `john1234` |

## 📝 API Documentation
Once the backend is running, visit the auto-generated Swagger docs at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---
*Built with ❤️ for efficient HR management.*
