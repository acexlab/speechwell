"""
File Logic Summary: Database schema definitions for users and analyses. These models determine what data is persisted and returned by the API.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    audio_id = Column(String, unique=True, index=True)
    filename = Column(String)
    transcript = Column(Text, nullable=True)
    
    # Dysarthria Analysis
    dysarthria_probability = Column(Float)
    dysarthria_label = Column(String)
    
    # Stuttering Analysis
    stuttering_probability = Column(Float)
    stuttering_repetitions = Column(Integer, default=0)
    stuttering_prolongations = Column(Integer, default=0)
    stuttering_blocks = Column(Integer, default=0)
    
    # Grammar Analysis
    grammar_score = Column(Float)
    grammar_error_count = Column(Integer, default=0)
    corrected_text = Column(Text, nullable=True)
    
    # Phonological Analysis
    phonological_score = Column(Float)
    phonological_error_count = Column(Integer, default=0)
    
    # Speech Metrics
    speaking_rate_wps = Column(Float)
    average_pause_sec = Column(Float)
    max_pause_sec = Column(Float)
    total_duration_sec = Column(Float)
    
    # File Paths
    pdf_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="completed")  # processing, completed, failed
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

