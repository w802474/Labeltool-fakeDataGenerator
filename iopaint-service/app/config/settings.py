"""IOPaint service configuration settings."""
import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class IOPaintSettings(BaseSettings):
    """IOPaint service settings with environment variable support."""
    
    # Service Configuration
    host: str = Field(default="0.0.0.0", env="IOPAINT_HOST")
    port: int = Field(default=8081, env="IOPAINT_PORT")
    
    # IOPaint Model Configuration
    model: str = Field(default="lama", env="IOPAINT_MODEL") 
    device: str = Field(default="cpu", env="IOPAINT_DEVICE")
    
    # Processing Configuration
    low_mem: bool = Field(default=True, env="IOPAINT_LOW_MEM")
    cpu_offload: bool = Field(default=True, env="IOPAINT_CPU_OFFLOAD")
    no_gui: bool = Field(default=True, env="IOPAINT_NO_GUI")
    
    # API Configuration
    max_image_size: int = Field(default=2048, env="MAX_IMAGE_SIZE")  # Max dimension
    max_file_size: int = Field(default=52428800, env="MAX_FILE_SIZE")  # 50MB
    
    # Performance Configuration
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    @field_validator("device")
    @classmethod
    def validate_device(cls, v):
        """Validate device setting."""
        valid_devices = ["cpu", "cuda", "mps"]
        if v not in valid_devices:
            raise ValueError(f"Invalid device '{v}'. Must be one of: {valid_devices}")
        return v
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model setting."""
        valid_models = ["lama", "ldm", "zits", "mat", "fcf", "manga"]
        if v not in valid_models:
            raise ValueError(f"Invalid model '{v}'. Must be one of: {valid_models}")
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
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = IOPaintSettings()