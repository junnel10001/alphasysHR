from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models import Base
import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database URL - prioritize MySQL for production
# Use MySQL as primary database, SQLite as fallback
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "alpha_hr")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
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