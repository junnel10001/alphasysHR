from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
import os

# Database URL - replace with your actual connection string or use environment variable
# Use SQLite as a local fallback for development/testing
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./users.db"
)

# For SQLite, we need to set check_same_thread=False to allow connections across threads
if DATABASE_URL.startswith('sqlite://'):
    engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args={'check_same_thread': False})
else:
    engine = create_engine(DATABASE_URL, echo=False, future=True)

# Only create tables once to avoid issues
if not hasattr(Base.metadata, '_tables_created'):
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    Base.metadata._tables_created = True
    print("Database tables created successfully!")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    Dependency that provides a SQLAlchemy Session.
    FastAPI will handle the lifecycle of the session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()