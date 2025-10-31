from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from models.admin_user import AdminRole, AdminStatus, DepartmentType

class AdminUserBase(BaseModel):
    name: str
    email: EmailStr
    role: AdminRole
    department: Optional[DepartmentType] = None
    phone: Optional[str] = None
    status: AdminStatus = AdminStatus.ACTIVE

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[AdminRole] = None
    department: Optional[DepartmentType] = None
    phone: Optional[str] = None
    status: Optional[AdminStatus] = None
    password: Optional[str] = None

class AdminUserResponse(AdminUserBase):
    id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminUserLogin(BaseModel):
    email: EmailStr
    password: str

class AdminUserLoginResponse(BaseModel):
    user: AdminUserResponse
    dashboard_url: str
    access_token: Optional[str] = None
    
class PasswordResetRequest(BaseModel):
    user_id: int
    
class PasswordResetResponse(BaseModel):
    message: str
    temporary_password: str
