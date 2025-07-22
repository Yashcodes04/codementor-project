from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class ProblemCreate(BaseModel):
    id: str
    title: str
    difficulty: str
    description: str
    platform: str
    url: str
    examples: List[Dict[str, Any]] = []
    constraints: List[str] = []

class ProblemResponse(BaseModel):
    id: int
    platform_id: str
    title: str
    difficulty: str
    platform: str
    
    class Config:
        from_attributes = True

class UserProgressData(BaseModel):
    lines_of_code: int = 0
    has_function: bool = False
    has_loop: bool = False
    time_spent: int = 0

class HintRequest(BaseModel):
    problem_id: str
    level: int
    user_progress: Optional[UserProgressData] = None

class HintResponse(BaseModel):
    hint: str