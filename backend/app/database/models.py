"""
File Logic Summary: Database schema definitions for users and analyses. These models determine what data is persisted and returned by the API.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .db import Base
from backend.app.services.score_service import calculate_overall_score


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    location = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    primary_goal = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
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
    report_filename = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="completed")  # processing, completed, failed
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def overall_score(self) -> int:
        return calculate_overall_score(
            self.dysarthria_probability,
            self.stuttering_probability,
            self.grammar_score,
        )


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module_key = Column(String, index=True)
    exercise_key = Column(String, index=True)
    prompt_text = Column(Text, nullable=True)
    expected_text = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    input_mode = Column(String, default="mic")
    accuracy_score = Column(Float, default=0.0)
    fluency_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    long_pause_count = Column(Integer, default=0)
    repeated_word_count = Column(Integer, default=0)
    duration_sec = Column(Float, default=0.0)
    feedback_summary = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    status = Column(String, default="started")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TrainingProgress(Base):
    __tablename__ = "training_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module_key = Column(String, index=True)
    sessions_completed = Column(Integer, default=0)
    avg_accuracy = Column(Float, default=0.0)
    avg_fluency = Column(Float, default=0.0)
    best_score = Column(Float, default=0.0)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)

