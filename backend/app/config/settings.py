"""Application configuration settings."""
import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    api_version: str = Field(default="v1", env="API_VERSION")
    
    # File Upload Configuration
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    processed_dir: str = Field(default="processed", env="PROCESSED_DIR")
    
    
    # PaddleOCR Configuration
    paddleocr_device: str = Field(default="cpu", env="PADDLEOCR_DEVICE")
    paddleocr_det_db_thresh: float = Field(default=0.3, env="PADDLEOCR_DET_DB_THRESH")
    paddleocr_det_db_box_thresh: float = Field(default=0.6, env="PADDLEOCR_DET_DB_BOX_THRESH")
    paddleocr_use_angle_cls: bool = Field(default=True, env="PADDLEOCR_USE_ANGLE_CLS")
    paddleocr_lang: str = Field(default="en", env="PADDLEOCR_LANG")
    paddleocr_det_limit_side_len: int = Field(default=1920, env="PADDLEOCR_DET_LIMIT_SIDE_LEN")
    
    # IOPaint Configuration
    iopaint_port: int = Field(default=8081, env="IOPAINT_PORT")
    iopaint_model: str = Field(default="lama", env="IOPAINT_MODEL") 
    iopaint_device: str = Field(default="cpu", env="IOPAINT_DEVICE")
    
    # Text Inpainting Configuration
    inpainting_method: str = Field(default="iopaint", env="INPAINTING_METHOD")
    
    # Processing Configuration
    processing_timeout: int = Field(default=300, env="PROCESSING_TIMEOUT")  # 5 minutes
    cleanup_interval: int = Field(default=3600, env="CLEANUP_INTERVAL")  # 1 hour
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        env="LOG_FORMAT"
    )
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Frontend Configuration (for development proxy)
    frontend_url: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    
    # Security Configuration
    allowed_mime_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        env="ALLOWED_MIME_TYPES"
    )
    
    @field_validator("paddleocr_device")
    @classmethod
    def validate_device(cls, v):
        """Validate PaddleOCR device setting."""
        valid_devices = ["cpu", "cuda"]
        if v not in valid_devices:
            raise ValueError(f"Invalid device '{v}'. Must be one of: {valid_devices}")
        return v
    
    @field_validator("iopaint_device")
    @classmethod  
    def validate_iopaint_device(cls, v):
        """Validate IOPaint device setting."""
        valid_devices = ["cpu", "cuda", "mps"]
        if v not in valid_devices:
            raise ValueError(f"Invalid IOPaint device '{v}'. Must be one of: {valid_devices}")
        return v
    
    @field_validator("iopaint_model")
    @classmethod
    def validate_iopaint_model(cls, v):
        """Validate IOPaint model setting."""
        valid_models = ["lama", "ldm", "zits", "mat", "fcf", "manga"]
        if v not in valid_models:
            raise ValueError(f"Invalid IOPaint model '{v}'. Must be one of: {valid_models}")
        return v
    
    @field_validator("inpainting_method")
    @classmethod
    def validate_inpainting_method(cls, v):
        """Validate inpainting method setting."""
        valid_methods = ["iopaint", "telea", "ns"]
        if v not in valid_methods:
            raise ValueError(f"Invalid inpainting method '{v}'. Must be one of: {valid_methods}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level setting."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers from string or list."""
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @field_validator("allowed_mime_types", mode="before")
    @classmethod
    def parse_allowed_mime_types(cls, v):
        """Parse allowed MIME types from string or list."""
        if isinstance(v, str):
            return [mime_type.strip() for mime_type in v.split(",")]
        return v
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.upload_dir, 
            self.processed_dir
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_paddleocr_config(self) -> dict:
        """Get PaddleOCR configuration dictionary with new parameter names."""
        config = {
            # Use new parameter names for latest PaddleOCR version
            "text_det_thresh": self.paddleocr_det_db_thresh,
            "text_det_box_thresh": self.paddleocr_det_db_box_thresh,
            "use_textline_orientation": self.paddleocr_use_angle_cls,
            "lang": self.paddleocr_lang,
            "text_det_limit_side_len": self.paddleocr_det_limit_side_len,
            
            # Keep old names for backward compatibility
            "det_db_thresh": self.paddleocr_det_db_thresh,
            "det_db_box_thresh": self.paddleocr_det_db_box_thresh,
            "use_angle_cls": self.paddleocr_use_angle_cls,
            "det_limit_side_len": self.paddleocr_det_limit_side_len,
        }
        
        # Only add use_gpu if CUDA device is requested and available
        if self.paddleocr_device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    config["use_gpu"] = True
            except ImportError:
                pass
        
        return config
    
    def get_cors_config(self) -> dict:
        """Get CORS configuration dictionary."""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers
        }
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Create directories on module import
settings.create_directories()