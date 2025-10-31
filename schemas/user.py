from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserSignup(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str
    role: Optional[str] = "student"
    department: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str
    status: Optional[str] = "Active"
    department: Optional[str] = "ADMINISTRATION"

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    department: Optional[str] = None
    is_department_head: bool
    is_active: bool
    phone: Optional[str] = None
    position: Optional[str] = None
    created_at: datetime
    status: Optional[str] = "Active"
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    is_department_head: Optional[bool] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None
    position: Optional[str] = None

class LoginResponse(BaseModel):
    message: str
    user: UserResponse

class SignupResponse(BaseModel):
    message: str
    user: UserResponse

class UsersListResponse(BaseModel):
    users: list[UserResponse]
    total: int

class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: str
    head: Optional[UserResponse] = None
    members: list[UserResponse]
    total_members: int
    active_members: int

class DepartmentListResponse(BaseModel):
    departments: list[DepartmentResponse]
    total: int
