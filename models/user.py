from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import hashlib

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)  # student, it, maintenance, rector, warden, administration, admin
    department = Column(String, nullable=True)  # Same as role for department members
    is_department_head = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    phone = Column(String, nullable=True)
    position = Column(String, nullable=True)
    status = Column(String, default="Active", nullable=False)  # Active, On Leave, Inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with Query model
    queries = relationship("Query", back_populates="user")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return self.password_hash == self.hash_password(password)
