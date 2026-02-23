"""
File Logic Summary: API request/response schema contracts. It defines typed payload shapes for auth and analysis endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# ============ AUTH SCHEMAS ============
class UserRegister(BaseModel):
    email: str
    password: str
    password_confirm: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    primary_goal: Optional[str] = None
    bio: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    primary_goal: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ ANALYSIS SCHEMAS ============
class AnalysisResponse(BaseModel):
    id: int
    audio_id: str
    filename: str
    
    # Results
    dysarthria_probability: float
    dysarthria_label: str
    stuttering_probability: float
    grammar_score: float
    phonological_score: float
    
    # Details
    transcript: Optional[str]
    speaking_rate_wps: float
    average_pause_sec: float
    max_pause_sec: float
    
    # Files
    pdf_path: Optional[str]
    
    # Metadata
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisDetailResponse(AnalysisResponse):
    stuttering_repetitions: int
    stuttering_prolongations: int
    stuttering_blocks: int
    grammar_error_count: int
    phonological_error_count: int
    corrected_text: Optional[str]
    total_duration_sec: float


class HistoryResponse(BaseModel):
    id: int
    audio_id: str
    filename: str
    dysarthria_probability: float
    stuttering_probability: float
    grammar_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============ CHAT SCHEMAS ============
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str

