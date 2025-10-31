from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
import bcrypt
import secrets
import string
from datetime import datetime

from database import get_db
from models.admin_user import AdminUser, AdminRole, AdminStatus, DepartmentType
from schemas.admin_user import (
    AdminUserCreate, AdminUserUpdate, AdminUserResponse, 
    AdminUserLogin, AdminUserLoginResponse, PasswordResetRequest, 
    PasswordResetResponse
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

# Dashboard URL mapping
DASHBOARD_URLS = {
    (AdminRole.MAIN_ADMIN, None): "/admin/dashboard.html",
    (AdminRole.DEPARTMENT_ADMIN, DepartmentType.IT): "/dashboards/it/it-dashboard.html",
    (AdminRole.DEPARTMENT_ADMIN, DepartmentType.MAINTENANCE): "/dashboards/maintenance/maintenance-dashboard.html",
    (AdminRole.DEPARTMENT_ADMIN, DepartmentType.RECTOR): "/dashboards/rector/rector-dashboard.html",
    (AdminRole.DEPARTMENT_ADMIN, DepartmentType.WARDEN): "/dashboards/warden/warden-dashboard.html",
    (AdminRole.DEPARTMENT_ADMIN, DepartmentType.ADMINISTRATION): "/dashboards/admin/admin-dashboard.html",
}

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_random_password(length: int = 8) -> str:
    """Generate a random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def get_dashboard_url(role: AdminRole, department: DepartmentType = None) -> str:
    """Get the appropriate dashboard URL for an admin user"""
    return DASHBOARD_URLS.get((role, department), "/admin/dashboard.html")

@router.post("/login", response_model=AdminUserLoginResponse)
def login_admin(login_data: AdminUserLogin, db: Session = Depends(get_db)):
    """Authenticate admin user and return dashboard URL"""
    
    # Find admin user by email
    admin_user = db.query(AdminUser).filter(AdminUser.email == login_data.email).first()
    
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check password
    if not verify_password(login_data.password, admin_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if admin_user.status != AdminStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive or suspended"
        )
    
    # Update last login
    admin_user.last_login = datetime.utcnow()
    db.commit()
    
    # Get dashboard URL
    dashboard_url = get_dashboard_url(admin_user.role, admin_user.department)
    
    return AdminUserLoginResponse(
        user=AdminUserResponse.from_orm(admin_user),
        dashboard_url=dashboard_url
    )

@router.get("/users", response_model=List[AdminUserResponse])
def get_admin_users(db: Session = Depends(get_db)):
    """Get all admin users"""
    admin_users = db.query(AdminUser).all()
    return [AdminUserResponse.from_orm(user) for user in admin_users]

@router.post("/users", response_model=AdminUserResponse)
def create_admin_user(user_data: AdminUserCreate, db: Session = Depends(get_db)):
    """Create a new admin user"""
    
    # Check if email already exists
    existing_user = db.query(AdminUser).filter(AdminUser.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate department assignment
    if user_data.role == AdminRole.DEPARTMENT_ADMIN and not user_data.department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department admin must be assigned to a department"
        )
    
    if user_data.role == AdminRole.MAIN_ADMIN and user_data.department:
        user_data.department = None  # Main admin should not have department
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create admin user
    admin_user = AdminUser(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        department=user_data.department,
        phone=user_data.phone,
        status=user_data.status
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return AdminUserResponse.from_orm(admin_user)

@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(user_id: int, user_data: AdminUserUpdate, db: Session = Depends(get_db)):
    """Update an admin user"""
    
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    # Check email uniqueness if email is being updated
    if user_data.email and user_data.email != admin_user.email:
        existing_user = db.query(AdminUser).filter(
            and_(AdminUser.email == user_data.email, AdminUser.id != user_id)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update fields
    for field, value in user_data.dict(exclude_unset=True).items():
        if field == "password" and value:
            # Hash new password
            setattr(admin_user, "password_hash", hash_password(value))
        elif field != "password":
            setattr(admin_user, field, value)
    
    # Validate department assignment
    if admin_user.role == AdminRole.DEPARTMENT_ADMIN and not admin_user.department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department admin must be assigned to a department"
        )
    
    if admin_user.role == AdminRole.MAIN_ADMIN:
        admin_user.department = None  # Main admin should not have department
    
    db.commit()
    db.refresh(admin_user)
    
    return AdminUserResponse.from_orm(admin_user)

@router.delete("/users/{user_id}")
def delete_admin_user(user_id: int, db: Session = Depends(get_db)):
    """Delete an admin user"""
    
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    db.delete(admin_user)
    db.commit()
    
    return {"message": "Admin user deleted successfully"}

@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_admin_password(user_id: int, db: Session = Depends(get_db)):
    """Reset admin user password"""
    
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    # Generate temporary password
    temporary_password = generate_random_password()
    
    # Update password
    admin_user.password_hash = hash_password(temporary_password)
    db.commit()
    
    return PasswordResetResponse(
        message=f"Password reset successfully for {admin_user.name}",
        temporary_password=temporary_password
    )

@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_admin_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific admin user"""
    
    admin_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    return AdminUserResponse.from_orm(admin_user)
