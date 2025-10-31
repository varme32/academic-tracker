from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import (UserSignup, UserResponse, UsersListResponse, UserUpdate, 
                         DepartmentResponse, DepartmentListResponse, SignupResponse)
from typing import Optional

router = APIRouter(prefix="/departments", tags=["Departments"])

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

@router.get("/", response_model=DepartmentListResponse)
async def get_departments(db: Session = Depends(get_db)):
    """Get all departments with their members"""
    departments = []
    
    for dept_id, config in DEPARTMENT_CONFIG.items():
        # Get all users in this department
        members = db.query(User).filter(
            User.department == dept_id,
            User.is_active == True
        ).all()
        
        # Find department head
        head = db.query(User).filter(
            User.department == dept_id,
            User.is_department_head == True,
            User.is_active == True
        ).first()
        
        # If no head, try to get first user in department
        if not head and members:
            head = members[0]
        
        departments.append(DepartmentResponse(
            id=dept_id,
            name=config['name'],
            description=config['description'],
            head=UserResponse.from_orm(head) if head else None,
            members=[UserResponse.from_orm(member) for member in members],
            total_members=len(members),
            active_members=len([m for m in members if m.is_active])
        ))
    
    return DepartmentListResponse(
        departments=departments,
        total=len(departments)
    )

@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: str, db: Session = Depends(get_db)):
    """Get specific department details"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    config = DEPARTMENT_CONFIG[dept_id]
    
    # Get all users in this department
    members = db.query(User).filter(
        User.department == dept_id,
        User.is_active == True
    ).all()
    
    # Find department head
    head = db.query(User).filter(
        User.department == dept_id,
        User.is_department_head == True,
        User.is_active == True
    ).first()
    
    if not head and members:
        head = members[0]
    
    return DepartmentResponse(
        id=dept_id,
        name=config['name'],
        description=config['description'],
        head=UserResponse.from_orm(head) if head else None,
        members=[UserResponse.from_orm(member) for member in members],
        total_members=len(members),
        active_members=len([m for m in members if m.is_active])
    )

@router.get("/{department_id}/members", response_model=UsersListResponse)
async def get_department_members(
    department_id: str,
    include_inactive: bool = Query(False, description="Include inactive members"),
    db: Session = Depends(get_db)
):
    """Get all members of a specific department"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    query = db.query(User).filter(User.department == dept_id)
    
    if not include_inactive:
        query = query.filter(User.is_active == True)
    
    members = query.all()
    
    return UsersListResponse(
        users=[UserResponse.from_orm(member) for member in members],
        total=len(members)
    )

@router.post("/{department_id}/members", response_model=SignupResponse)
async def add_department_member(
    department_id: str,
    user_data: UserSignup,
    db: Session = Depends(get_db)
):
    """Add a new member to a department"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
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
    
    # Create new user with department
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=User.hash_password(user_data.password),
        role=dept_id.lower(),
        department=dept_id,
        phone=user_data.phone,
        position=user_data.position
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return SignupResponse(
        message=f"Member added to {DEPARTMENT_CONFIG[dept_id]['name']} successfully",
        user=UserResponse.from_orm(new_user)
    )

@router.put("/{department_id}/head/{user_id}")
async def set_department_head(
    department_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Set a user as department head"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is in the department
    if user.department != dept_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this department"
        )
    
    # Remove current head status from all users in department
    db.query(User).filter(
        User.department == dept_id
    ).update({"is_department_head": False})
    
    # Set new head
    user.is_department_head = True
    db.commit()
    
    return {"message": f"{user.full_name} is now head of {DEPARTMENT_CONFIG[dept_id]['name']}"}

@router.put("/{department_id}/members/{user_id}", response_model=UserResponse)
async def update_department_member(
    department_id: str,
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update department member information"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.department != dept_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this department"
        )
    
    # Update fields if provided
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "department" and value:
            value = value.upper()
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.delete("/{department_id}/members/{user_id}")
async def remove_department_member(
    department_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Remove a member from department (soft delete)"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.department != dept_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this department"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": f"Member removed from {DEPARTMENT_CONFIG[dept_id]['name']} successfully"}

@router.get("/{department_id}/stats")
async def get_department_stats(
    department_id: str,
    db: Session = Depends(get_db)
):
    """Get department statistics"""
    dept_id = department_id.upper()
    
    if dept_id not in DEPARTMENT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Get all members
    all_members = db.query(User).filter(User.department == dept_id).all()
    active_members = [m for m in all_members if m.is_active]
    inactive_members = [m for m in all_members if not m.is_active]
    
    # Get head
    head = db.query(User).filter(
        User.department == dept_id,
        User.is_department_head == True,
        User.is_active == True
    ).first()
    
    # Get department queries (if needed)
    from models.query import Query
    department_queries = db.query(Query).join(User).filter(
        User.department == dept_id
    ).all()
    
    return {
        "department_id": dept_id,
        "department_name": DEPARTMENT_CONFIG[dept_id]['name'],
        "total_members": len(all_members),
        "active_members": len(active_members),
        "inactive_members": len(inactive_members),
        "has_head": head is not None,
        "head_name": head.full_name if head else None,
        "total_queries": len(department_queries),
        "pending_queries": len([q for q in department_queries if q.status == 'pending']),
        "resolved_queries": len([q for q in department_queries if q.status == 'resolved'])
    }
