from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL - update with your PostgreSQL credentials
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yash123@localhost/codementor")

# Create engine
engine = create_engine(DATABASE_URL)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()