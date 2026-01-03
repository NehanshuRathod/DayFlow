from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import auth, employees, attendance, leaves, payroll

app = FastAPI(
    title="DayFlow HRMS API",
    description="Human Resource Management System - Every workday, perfectly aligned.",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including file://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(employees.router, prefix="/employees", tags=["Employees"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(leaves.router, prefix="/leaves", tags=["Leaves"])
app.include_router(payroll.router, prefix="/salary", tags=["Salary"])

# Serve static frontend files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DayFlow HRMS"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DayFlow HRMS API",
        "docs": "/docs",
        "health": "/health",
        "frontend": "/static/index.html"
    }
