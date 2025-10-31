import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base

# Database URL - use environment variable for production, fallback to SQLite for local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./query_portal.db")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
def create_tables():
    # Import all models to ensure they are registered with Base
    from models import user, query, admin_user
    Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
