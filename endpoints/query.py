from fastapi import APIRouter, Depends, HTTPException, status, Query as QueryParam, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from database import get_db
from models.user import User
from models.query import Query, QueryCategory, QueryPriority, QueryStatus
from schemas.query import (
    QueryCreate, QueryUpdate, QueryResponse, QueryListResponse, 
    QueryCreateResponse, QueryStatsResponse, QueryWithUser, QueryUpdateRequest
)
from typing import Optional, List
import os
import uuid
import base64
from pathlib import Path

router = APIRouter(prefix="/queries", tags=["Queries"])

# Directory for file uploads
# Use /tmp for temporary storage on cloud platforms, local 'uploads' otherwise
UPLOAD_DIR = Path("/tmp/uploads") if os.getenv("CLOUD_PLATFORM") else Path("uploads")
# Create directory if we have write permissions
try:
    UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
except (OSError, PermissionError):
    pass  # Directory creation will happen on first upload

def create_query_response(query_obj):
    """Helper function to create QueryResponse from Query object"""
    return QueryResponse(
        id=query_obj.id,
        user_id=query_obj.user_id,
        category=query_obj.category.value if hasattr(query_obj.category, 'value') else query_obj.category,
        subject=query_obj.subject,
        description=query_obj.description,
        priority=query_obj.priority.value if hasattr(query_obj.priority, 'value') else query_obj.priority,
        status=query_obj.status.value if hasattr(query_obj.status, 'value') else query_obj.status,
        attachment_filename=query_obj.attachment_filename,
        attachment_path=query_obj.attachment_path,
        attachment_type=query_obj.attachment_type,
        attachment_size=query_obj.attachment_size,
        created_at=query_obj.created_at,
        updated_at=query_obj.updated_at,
        resolved_at=query_obj.resolved_at,
        assigned_to=query_obj.assigned_to,
        assigned_member_id=getattr(query_obj, 'assigned_member_id', None),
        assigned_user=getattr(query_obj, 'assigned_user', None),
        resolution_notes=query_obj.resolution_notes
    )

def create_query_response_with_user(query_obj):
    """Helper function to create QueryResponse with user info from Query object"""
    response = QueryResponse(
        id=query_obj.id,
        user_id=query_obj.user_id,
        category=query_obj.category.value if hasattr(query_obj.category, 'value') else query_obj.category,
        subject=query_obj.subject,
        description=query_obj.description,
        priority=query_obj.priority.value if hasattr(query_obj.priority, 'value') else query_obj.priority,
        status=query_obj.status.value if hasattr(query_obj.status, 'value') else query_obj.status,
        contact_info=query_obj.contact_info,
        attachment_filename=query_obj.attachment_filename,
        attachment_path=query_obj.attachment_path,
        attachment_type=query_obj.attachment_type,
        attachment_size=query_obj.attachment_size,
        created_at=query_obj.created_at,
        updated_at=query_obj.updated_at,
        resolved_at=query_obj.resolved_at,
        assigned_to=query_obj.assigned_to,
        assigned_member_id=getattr(query_obj, 'assigned_member_id', None),
        assigned_user=getattr(query_obj, 'assigned_user', None),
        resolution_notes=query_obj.resolution_notes
    )
    
    # Add user information to the response
    if hasattr(query_obj, 'user') and query_obj.user:
        response.user = {
            'id': query_obj.user.id,
            'full_name': query_obj.user.full_name,
            'email': query_obj.user.email
        }
    else:
        response.user = {
            'id': query_obj.user_id,
            'full_name': 'Unknown User',
            'email': 'unknown@example.com'
        }
    return response

@router.post("/", response_model=QueryCreateResponse)
async def create_query(
    query_data: QueryCreate,
    user_id: int,  # In a real app, this would come from authentication
    db: Session = Depends(get_db)
):
    """Create a new query"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create new query
    new_query = Query(
        user_id=user_id,
        category=query_data.category,
        subject=query_data.subject,
        description=query_data.description,
        priority=query_data.priority,
        contact_info=query_data.contact_info,
        attachment_filename=query_data.attachment_filename
    )
    
    # Handle file attachment if provided
    if query_data.attachment_data:
        attachment = query_data.attachment_data
        new_query.attachment_filename = attachment.get('filename')
        new_query.attachment_data = attachment.get('content')  # Base64 string
        new_query.attachment_type = attachment.get('type')
        new_query.attachment_size = attachment.get('size')
        
        # Also save to file system if needed
        if attachment.get('content') and attachment.get('filename'):
            try:
                # Extract base64 data (remove data:image/jpeg;base64, prefix)
                if ',' in attachment.get('content'):
                    file_content = attachment.get('content').split(',')[1]
                else:
                    file_content = attachment.get('content')
                
                # Decode base64 and save file
                import base64
                file_data = base64.b64decode(file_content)
                
                # Create unique filename
                file_extension = Path(attachment.get('filename')).suffix
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = UPLOAD_DIR / unique_filename
                
                with open(file_path, "wb") as f:
                    f.write(file_data)
                
                new_query.attachment_path = str(file_path)
                
            except Exception as e:
                print(f"Error saving file: {e}")
                # Continue without file save - data is still in database
    
    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    
    # Debug: Print the actual values from the database
    print(f"Debug - Query from DB: category={new_query.category}, priority={new_query.priority}, status={new_query.status}")
    print(f"Debug - Types: category={type(new_query.category)}, priority={type(new_query.priority)}, status={type(new_query.status)}")
    
    return QueryCreateResponse(
        message="Query created successfully",
        query=create_query_response(new_query)
    )

@router.get("/", response_model=QueryListResponse)
async def get_queries(
    page: int = QueryParam(1, ge=1, description="Page number"),
    per_page: int = QueryParam(10, ge=1, le=100, description="Items per page"),
    user_id: Optional[int] = QueryParam(None, description="Filter by user ID"),
    category: Optional[QueryCategory] = QueryParam(None, description="Filter by category"),
    status: Optional[QueryStatus] = QueryParam(None, description="Filter by status"),
    priority: Optional[QueryPriority] = QueryParam(None, description="Filter by priority"),
    db: Session = Depends(get_db)
):
    """Get all queries with pagination and filters"""
    query = db.query(Query).options(joinedload(Query.user))
    
    # Apply filters
    if user_id:
        query = query.filter(Query.user_id == user_id)
    if category:
        query = query.filter(Query.category == category)
    if status:
        query = query.filter(Query.status == status)
    if priority:
        query = query.filter(Query.priority == priority)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * per_page
    queries = query.order_by(desc(Query.created_at)).offset(skip).limit(per_page).all()

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return QueryListResponse(
        queries=[create_query_response_with_user(q) for q in queries],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/user/{user_id}", response_model=QueryListResponse)
async def get_user_queries(
    user_id: int,
    page: int = QueryParam(1, ge=1),
    per_page: int = QueryParam(10, ge=1, le=100),
    status: Optional[QueryStatus] = QueryParam(None),
    db: Session = Depends(get_db)
):
    """Get queries for a specific user"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    query = db.query(Query).filter(Query.user_id == user_id)
    
    if status:
        query = query.filter(Query.status == status)
    
    total = query.count()
    skip = (page - 1) * per_page
    queries = query.order_by(desc(Query.created_at)).offset(skip).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    
    return QueryListResponse(
        queries=[create_query_response(q) for q in queries],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{query_id}", response_model=QueryResponse)
async def get_query_by_id(query_id: int, db: Session = Depends(get_db)):
    """Get a specific query by ID"""
    query = db.query(Query).filter(Query.id == query_id).first()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    return create_query_response(query)

@router.put("/{query_id}", response_model=QueryResponse)
async def update_query(
    query_id: int,
    query_update: QueryUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a query with new status, assignment, or other fields"""
    
    # Get the query
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    # Update fields if provided
    update_data = query_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(query, field) and value is not None:
            setattr(query, field, value)
    
    # If assigned_to is being changed, update the category accordingly
    if query_update.assigned_to:
        department_to_category = {
            'IT': 'IT',
            'MAINTENANCE': 'MAINTENANCE', 
            'RECTOR': 'RECTOR',  # Rector office has its own category
            'WARDEN': 'WARDEN',  # Warden office has its own category
            'ADMINISTRATION': 'ADMINISTRATION'
        }
        
        new_category = department_to_category.get(query_update.assigned_to.upper())
        if new_category:
            if new_category == 'IT':
                query.category = QueryCategory.IT
            elif new_category == 'MAINTENANCE':
                query.category = QueryCategory.MAINTENANCE
            elif new_category == 'RECTOR':
                query.category = QueryCategory.RECTOR
            elif new_category == 'WARDEN':
                query.category = QueryCategory.WARDEN
            else:
                query.category = QueryCategory.ADMINISTRATION
            
            print(f"Updated query {query.id} category to {query.category} due to transfer to {query_update.assigned_to}")
    
    # If status is being updated to RESOLVED, set resolved_at
    if query_update.status == QueryStatus.RESOLVED and query.resolved_at is None:
        query.resolved_at = func.now()
    
    # If admin_response is provided, add it to resolution_notes
    if query_update.admin_response:
        if query.resolution_notes:
            query.resolution_notes += f"\n\nAdmin Response: {query_update.admin_response}"
        else:
            query.resolution_notes = f"Admin Response: {query_update.admin_response}"
    
    # Set updated_at
    query.updated_at = func.now()
    
    try:
        db.commit()
        db.refresh(query)
        return create_query_response(query)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update query: {str(e)}"
        )

@router.delete("/{query_id}")
async def delete_query(query_id: int, db: Session = Depends(get_db)):
    """Delete a query"""
    query = db.query(Query).filter(Query.id == query_id).first()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    db.delete(query)
    db.commit()
    
    return {"message": "Query deleted successfully"}

@router.get("/stats/overview", response_model=QueryStatsResponse)
async def get_query_stats(db: Session = Depends(get_db)):
    """Get query statistics"""
    total_queries = db.query(Query).count()
    
    # Count by status
    pending = db.query(Query).filter(Query.status == QueryStatus.PENDING).count()
    in_progress = db.query(Query).filter(Query.status == QueryStatus.IN_PROGRESS).count()
    resolved = db.query(Query).filter(Query.status == QueryStatus.RESOLVED).count()
    closed = db.query(Query).filter(Query.status == QueryStatus.CLOSED).count()
    
    # Count by category
    category_stats = {}
    for category in QueryCategory:
        count = db.query(Query).filter(Query.category == category).count()
        category_stats[category.value] = count
    
    # Count by priority
    priority_stats = {}
    for priority in QueryPriority:
        count = db.query(Query).filter(Query.priority == priority).count()
        priority_stats[priority.value] = count
    
    return QueryStatsResponse(
        total_queries=total_queries,
        pending_queries=pending,
        in_progress_queries=in_progress,
        resolved_queries=resolved,
        closed_queries=closed,
        by_category=category_stats,
        by_priority=priority_stats
    )

@router.post("/{query_id}/upload", response_model=dict)
async def upload_attachment(
    query_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload attachment for a query"""
    query = db.query(Query).filter(Query.id == query_id).first()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    # Validate file type and size
    allowed_types = {"image/jpeg", "image/png", "application/pdf", "text/plain"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Only JPEG, PNG, PDF, and TXT files are supported."
        )
    
    # Check file size (10MB limit)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 10MB."
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update query with attachment info
    query.attachment_filename = file.filename
    query.attachment_path = str(file_path)
    
    db.commit()
    db.refresh(query)
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "unique_filename": unique_filename
    }
