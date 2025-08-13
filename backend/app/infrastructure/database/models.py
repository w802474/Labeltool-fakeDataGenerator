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
    """Custom SQLAlchemy type for JSON data compatible with MySQL and SQLite."""
    
    impl = VARCHAR(4000)  # Explicitly set length for MySQL compatibility
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            # Use TEXT for MySQL with aiomysql driver since JSON type is not available
            from sqlalchemy import TEXT
            return dialect.type_descriptor(TEXT())
        else:
            return dialect.type_descriptor(VARCHAR(4000))
    
    def process_bind_param(self, value, dialect):
        # Always serialize to JSON string for storage
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return None
    
    def process_result_value(self, value, dialect):
        # Always parse JSON string from storage
        if value is not None:
            return json.loads(value)
        return None


class SessionModel(Base):
    """Database model for label sessions."""
    
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    original_image_path: Mapped[str] = mapped_column(String(1000), nullable=False)  # Increased for longer paths
    original_image_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_image_size: Mapped[int] = mapped_column(Integer, nullable=False)
    original_image_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_image_dimensions: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    processed_image_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # Increased for longer paths
    processed_image_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_image_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Add index for queries
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)  # Add index for queries
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
    session_id: Mapped[str] = mapped_column(String(255), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)  # Add index and cascade delete
    region_type: Mapped[str] = mapped_column(String(50), default="ocr", nullable=False, index=True)  # Add index for queries
    
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
    text_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # Add index for classification queries
    category_config_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    font_properties_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    original_box_size_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    original_region_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For processed regions: original OCR region ID
    
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