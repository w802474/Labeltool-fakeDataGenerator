"""SQLAlchemy database models for persistent storage."""
from datetime import datetime
from typing import Optional, List
import json

from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, VARCHAR

Base = declarative_base()


class JSONType(TypeDecorator):
    """Custom SQLAlchemy type for JSON data."""
    
    impl = VARCHAR
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


class SessionModel(Base):
    """Database model for label sessions."""
    
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    original_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_image_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_image_size: Mapped[int] = mapped_column(Integer, nullable=False)
    original_image_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_image_dimensions: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    processed_image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    processed_image_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_image_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    text_regions: Mapped[List["TextRegionModel"]] = relationship(
        "TextRegionModel", 
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<SessionModel(id={self.id}, status={self.status})>"


class TextRegionModel(Base):
    """Database model for text regions."""
    
    __tablename__ = "text_regions"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), ForeignKey("sessions.id"), nullable=False)
    region_type: Mapped[str] = mapped_column(String(50), default="ocr", nullable=False)
    
    # Geometric data stored as JSON
    bounding_box_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    corners_json: Mapped[List[dict]] = mapped_column(JSONType, nullable=False)
    
    # OCR and text data
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    original_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # State flags
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_user_modified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_size_modified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Classification and styling
    text_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_config_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    font_properties_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    original_box_size_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="text_regions")
    
    def __repr__(self):
        return f"<TextRegionModel(id={self.id}, session_id={self.session_id}, text_category={self.text_category})>"


# Index definitions for better query performance
from sqlalchemy import Index

# Create indexes for common query patterns
Index('idx_sessions_status_created', SessionModel.status, SessionModel.created_at.desc())
Index('idx_sessions_created_desc', SessionModel.created_at.desc())
Index('idx_text_regions_session_id', TextRegionModel.session_id)
Index('idx_text_regions_category', TextRegionModel.text_category)
Index('idx_text_regions_type_session', TextRegionModel.region_type, TextRegionModel.session_id)