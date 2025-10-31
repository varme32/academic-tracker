from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/team-members/", response_model=List[UserResponse])
async def get_team_members(department: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Get team members, optionally filtered by department"""
    try:
        query = db.query(User)
        
        if department:
            # Filter by specific department
            query = query.filter(User.department == department.upper())
            logger.info(f"Fetching team members for department: {department}")
        else:
            # Default to ADMINISTRATION if no department specified
            query = query.filter(User.department == "ADMINISTRATION")
            logger.info("Fetching team members for ADMINISTRATION department (default)")
        
        team_members = query.all()
        
        logger.info(f"Found {len(team_members)} team members")
        return team_members
    except Exception as e:
        logger.error(f"Error fetching team members: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch team members")

@router.post("/team-members/", response_model=UserResponse)
async def create_team_member(member: UserCreate, db: Session = Depends(get_db)):
    """Create a new team member"""
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == member.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new team member with specified department
        department = getattr(member, 'department', 'ADMINISTRATION')
        db_member = User(
            full_name=member.name,
            email=member.email,
            password_hash=User.hash_password("defaultpassword123"),  # Default password
            department=department.upper() if department else "ADMINISTRATION",
            role=member.role,
            status=member.status if hasattr(member, 'status') else "Active"
        )
        
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        
        logger.info(f"Created team member: {db_member.full_name}")
        return db_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team member: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create team member")

@router.put("/team-members/{member_id}", response_model=UserResponse)
async def update_team_member(member_id: int, member: UserCreate, db: Session = Depends(get_db)):
    """Update an existing team member"""
    try:
        db_member = db.query(User).filter(User.id == member_id).first()
        if not db_member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        # Check if email already exists for other users
        existing_user = db.query(User).filter(
            User.email == member.email,
            User.id != member_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Update team member data
        db_member.full_name = member.name
        db_member.email = member.email
        db_member.role = member.role
        if hasattr(member, 'status'):
            db_member.status = member.status
        if hasattr(member, 'department') and member.department:
            db_member.department = member.department.upper()
        
        db.commit()
        db.refresh(db_member)
        
        logger.info(f"Updated team member: {db_member.full_name}")
        return db_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team member: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update team member")

@router.delete("/team-members/{member_id}")
async def delete_team_member(member_id: int, db: Session = Depends(get_db)):
    """Delete a team member"""
    try:
        db_member = db.query(User).filter(User.id == member_id).first()
        if not db_member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        member_name = db_member.full_name
        db.delete(db_member)
        db.commit()
        
        logger.info(f"Deleted team member: {member_name}")
        return {"message": "Team member deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team member: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete team member")

@router.get("/team-members/{member_id}", response_model=UserResponse)
async def get_team_member(member_id: int, db: Session = Depends(get_db)):
    """Get a specific team member by ID"""
    try:
        member = db.query(User).filter(User.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        return member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team member: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch team member")
