from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from typing import Optional, List

from database import get_db, engine
from models import Base, User, Problem, Hint, UserProgress
from schemas import (
    UserCreate, UserLogin, UserResponse,
    ProblemCreate, ProblemResponse,
    HintRequest, HintResponse
)
from hint_generator import HintGenerator

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CodeMentor API", version="1.0.0")
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://leetcode.com", "chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize hint generator
hint_generator = HintGenerator()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"user_id": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/")
async def root():
    return {"message": "CodeMentor API is running!"}

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password.decode('utf-8')
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }

@app.post("/api/auth/login", response_model=UserResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not bcrypt.checkpw(credentials.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }

@app.post("/api/problems/detect", response_model=ProblemResponse)
async def detect_problem(
    problem_data: ProblemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if problem already exists
    existing_problem = db.query(Problem).filter(
        Problem.platform_id == problem_data.id,
        Problem.platform == problem_data.platform
    ).first()
    
    if existing_problem:
        return existing_problem
    
    # Create new problem
    problem = Problem(
        platform_id=problem_data.id,
        title=problem_data.title,
        difficulty=problem_data.difficulty,
        description=problem_data.description,
        platform=problem_data.platform,
        url=problem_data.url,
        examples=problem_data.examples,
        constraints=problem_data.constraints
    )
    
    db.add(problem)
    db.commit()
    db.refresh(problem)
    
    return problem

@app.post("/api/hints/generate", response_model=HintResponse)
async def generate_hint(
    hint_request: HintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get problem
    problem = db.query(Problem).filter(
        Problem.platform_id == hint_request.problem_id
    ).first()
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Check if user has already received this hint level
    existing_hint = db.query(Hint).filter(
        Hint.user_id == current_user.id,
        Hint.problem_id == problem.id,
        Hint.level == hint_request.level
    ).first()
    
    if existing_hint:
        return {"hint": existing_hint.content}
    
    # Generate hint
    hint_content = hint_generator.generate_hint(
        problem=problem,
        level=hint_request.level,
        user_progress=hint_request.user_progress
    )
    
    # Save hint
    hint = Hint(
        user_id=current_user.id,
        problem_id=problem.id,
        level=hint_request.level,
        content=hint_content
    )
    
    db.add(hint)
    db.commit()
    
    return {"hint": hint_content}

@app.post("/api/analytics/track")
async def track_event(
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Store analytics data (implement based on your needs)
    print(f"Analytics event from user {current_user.id}: {event_data}")
    return {"status": "tracked"}
@app.get("/api/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username
        }
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)