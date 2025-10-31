from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class QueryCategory(enum.Enum):
    IT = "IT"
    MAINTENANCE = "MAINTENANCE"
    RECTOR = "RECTOR" 
    WARDEN = "WARDEN"
    ADMINISTRATION = "ADMINISTRATION"

class QueryPriority(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class QueryStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(QueryCategory), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum(QueryPriority), nullable=False, default=QueryPriority.MEDIUM)
    status = Column(Enum(QueryStatus), nullable=False, default=QueryStatus.PENDING)
    attachment_filename = Column(String(255), nullable=True)
    attachment_path = Column(String(500), nullable=True)
    attachment_data = Column(Text, nullable=True)  # Store base64 encoded file data
    attachment_type = Column(String(100), nullable=True)  # Store file MIME type
    attachment_size = Column(Integer, nullable=True)  # Store file size
    contact_info = Column(String(255), nullable=True)  # Store contact information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(String(100), nullable=True)  # Department or staff member
    assigned_member_id = Column(Integer, nullable=True)  # Team member ID assignment
    assigned_user = Column(String(255), nullable=True)  # Team member name
    resolution_notes = Column(Text, nullable=True)
    
    # Relationship with User model
    user = relationship("User", back_populates="queries")
