from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import (UserSignup, UserLogin, LoginResponse, SignupResponse, 
                         UserResponse, UsersListResponse, UserUpdate, DepartmentResponse, DepartmentListResponse)
from pydantic import BaseModel
from typing import Optional, List

# Password change schema
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordChangeResponse(BaseModel):
    message: str

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Department configuration
DEPARTMENT_CONFIG = {
    'IT': {
        'name': 'IT Department',
        'description': 'Information Technology Support'
    },
    'MAINTENANCE': {
        'name': 'Maintenance Department', 
        'description': 'Facility Maintenance & Infrastructure'
    },
    'RECTOR': {
        'name': 'Rector Office',
        'description': 'Academic Affairs & Administration'
    },
    'WARDEN': {
        'name': 'Warden Office',
        'description': 'Student Housing & Accommodation'
    },
    'ADMINISTRATION': {
        'name': 'Administration',
        'description': 'General Administrative Services'
    }
}

@router.post("/signup", response_model=SignupResponse)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    # Check if passwords match
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate department role
    if user_data.role and user_data.role.upper() in DEPARTMENT_CONFIG:
        department = user_data.role.upper()
    else:
        department = user_data.department.upper() if user_data.department else None
    
    # Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=User.hash_password(user_data.password),
        role=user_data.role or "student",
        department=department,
        phone=user_data.phone,
        position=user_data.position
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return SignupResponse(
        message="Account created successfully",
        user=UserResponse.from_orm(new_user)
    )

@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return LoginResponse(
        message="Login successful",
        user=UserResponse.from_orm(user)
    )

@router.get("/users", response_model=UsersListResponse)
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    db: Session = Depends(get_db)
):
    """Get all users with pagination"""
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    
    return UsersListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total
    )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.get("/users/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """Get a specific user by email"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.post("/users/{user_id}/change-password", response_model=PasswordChangeResponse)
async def change_user_password(
    user_id: int, 
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db)
):
    """Change password for a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.password_hash = User.hash_password(password_data.new_password)
    db.commit()
    
    return PasswordChangeResponse(message="Password updated successfully")

@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password_by_email(
    password_data: PasswordChangeRequest,
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    """Change password using email (alternative endpoint)"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.password_hash = User.hash_password(password_data.new_password)
    db.commit()
    
    return PasswordChangeResponse(message="Password updated successfully")
