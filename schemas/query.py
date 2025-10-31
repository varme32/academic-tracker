from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class QueryCategory(str, Enum):
    IT = "IT"
    MAINTENANCE = "MAINTENANCE"
    RECTOR = "RECTOR"
    WARDEN = "WARDEN"
    ADMINISTRATION = "ADMINISTRATION"

class QueryPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class QueryStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class QueryCreate(BaseModel):
    category: QueryCategory
    subject: str
    description: str
    priority: QueryPriority = QueryPriority.MEDIUM
    contact_info: Optional[str] = None
    attachment_filename: Optional[str] = None
    attachment_data: Optional[dict] = None  # File data with filename, content, size, type
    
    @validator('subject')
    def subject_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Subject cannot be empty')
        return v.strip()
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

class QueryUpdateRequest(BaseModel):
    status: Optional[QueryStatus] = None
    category: Optional[QueryCategory] = None
    assigned_to: Optional[str] = None
    assigned_member_id: Optional[int] = None
    assigned_user: Optional[str] = None
    admin_response: Optional[str] = None
    resolution_notes: Optional[str] = None

class QueryUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[QueryPriority] = None
    status: Optional[QueryStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

class QueryResponse(BaseModel):
    id: int
    user_id: int
    category: QueryCategory
    subject: str
    description: str
    priority: QueryPriority
    status: QueryStatus
    contact_info: Optional[str]
    attachment_filename: Optional[str]
    attachment_path: Optional[str]
    attachment_type: Optional[str]
    attachment_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    assigned_to: Optional[str]
    assigned_member_id: Optional[int] = None
    assigned_user: Optional[str] = None
    resolution_notes: Optional[str]
    user: Optional[dict] = None  # Add user field
    
    class Config:
        from_attributes = True

class QueryWithUser(QueryResponse):
    user_name: str
    user_email: str

class QueryListResponse(BaseModel):
    queries: List[QueryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class QueryCreateResponse(BaseModel):
    message: str
    query: QueryResponse

class QueryStatsResponse(BaseModel):
    total_queries: int
    pending_queries: int
    in_progress_queries: int
    resolved_queries: int
    closed_queries: int
    by_category: dict
    by_priority: dict
