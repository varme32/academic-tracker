from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from .base import Base
import enum

class AdminRole(enum.Enum):
    MAIN_ADMIN = "MAIN_ADMIN"
    DEPARTMENT_ADMIN = "DEPARTMENT_ADMIN"

class AdminStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class DepartmentType(enum.Enum):
    IT = "IT"
    MAINTENANCE = "MAINTENANCE"
    RECTOR = "RECTOR"
    WARDEN = "WARDEN"
    ADMINISTRATION = "ADMINISTRATION"

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(AdminRole), nullable=False)
    department = Column(Enum(DepartmentType), nullable=True)  # Null for main admin
    phone = Column(String(20), nullable=True)
    status = Column(Enum(AdminStatus), default=AdminStatus.ACTIVE)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AdminUser(id={self.id}, email='{self.email}', role='{self.role}')>"
