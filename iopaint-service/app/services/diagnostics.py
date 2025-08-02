"""IOPaint service diagnostics and error analysis."""
import asyncio
import time
import psutil
import aiohttp
import socket
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from loguru import logger
import subprocess
import sys


class DisconnectionReason(Enum):
    """Specific reasons for IOPaint disconnection."""
    NETWORK_TIMEOUT = "network_timeout"
    CONNECTION_REFUSED = "connection_refused"
    PROCESSING_TIMEOUT = "processing_timeout"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    GPU_MEMORY_EXHAUSTION = "gpu_memory_exhaustion"
    SERVICE_CRASHED = "service_crashed"
    MODEL_LOADING_FAILED = "model_loading_failed"
    IMAGE_TOO_LARGE = "image_too_large"
    TOO_MANY_REGIONS = "too_many_regions"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN_ERROR = "unknown_error"


class ErrorCategory(Enum):
    """Categories of errors for different handling strategies."""
    CONNECTION = "connection"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    SERVICE = "service"
    INPUT = "input"
    UNKNOWN = "unknown"


@dataclass
class DiagnosticResult:
    """Result of diagnostic analysis."""
    reason: DisconnectionReason
    category: ErrorCategory
    confidence: float  # 0.0 to 1.0
    description: str
    suggestions: List[str]
    retry_recommended: bool
    retry_with_reduced_params: bool
    technical_details: Dict[str, Any]


@dataclass
class ResourceMonitor:
    """Resource usage monitoring data."""
    memory_usage_mb: float
    memory_available_mb: float
    cpu_usage_percent: float
    processing_time_seconds: float
    estimated_peak_memory_mb: Optional[float] = None
    gpu_memory_mb: Optional[float] = None


class IOPaintDiagnosticsService:
    """Service for diagnosing IOPaint connection issues and providing specific error analysis."""
    
    def __init__(self, iopaint_port: int = 8082):
        self.iopaint_port = iopaint_port
        self.base_url = f"http://localhost:{iopaint_port}"
        self._last_health_check = None
        self._last_health_status = None
        
    async def diagnose_disconnection(
        self, 
        error: Exception,
        image_size: Optional[Tuple[int, int, int]] = None,
        region_count: Optional[int] = None,
        processing_duration: Optional[float] = None
    ) -> DiagnosticResult:
        """
        Analyze a disconnection error and provide specific diagnosis.
        
        Args:
            error: The exception that occurred
            image_size: Tuple of (height, width, channels) if available
            region_count: Number of text regions being processed
            processing_duration: How long processing took before failure
            
        Returns:
            Detailed diagnostic result with specific reason and suggestions
        """
        logger.info(f"Diagnosing IOPaint disconnection: {type(error).__name__}: {error}")
        
        # Get current system state
        resource_monitor = await self._get_current_resources()
        service_status = await self._check_service_status()
        connectivity = await self._check_connectivity()
        
        # Analyze the error
        diagnosis = await self._analyze_error(
            error, image_size, region_count, processing_duration,
            resource_monitor, service_status, connectivity
        )
        
        logger.error(f"IOPaint disconnection diagnosis: {diagnosis.reason.value} - {diagnosis.description}")
        for suggestion in diagnosis.suggestions:
            logger.info(f"Suggestion: {suggestion}")
            
        return diagnosis
    
    async def _analyze_error(
        self,
        error: Exception,
        image_size: Optional[Tuple[int, int, int]],
        region_count: Optional[int],
        processing_duration: Optional[float],
        resources: ResourceMonitor,
        service_status: Dict[str, Any],
        connectivity: Dict[str, Any]
    ) -> DiagnosticResult:
        """Analyze error with context to determine specific cause."""
        
        # Import error classifier here to avoid circular imports
        from app.services.error_classifier import error_classifier
        
        # Prepare context for advanced classification
        context = {
            "image_size": image_size,
            "region_count": region_count,
            "processing_duration": processing_duration,
            "memory_usage_mb": resources.memory_usage_mb,
            "memory_available_mb": resources.memory_available_mb,
            "cpu_usage_percent": resources.cpu_usage_percent,
            "service_status": service_status,
            "connectivity": connectivity
        }
        
        # Use advanced error classifier
        reason, category, confidence, analysis = error_classifier.classify_error(error, context)
        
        # Generate detailed suggestions based on classification
        suggestions = self._generate_suggestions(reason, category, context, analysis)
        
        # Determine retry recommendations
        retry_recommended, retry_with_reduced_params = self._determine_retry_strategy(reason, category, context)
        
        return DiagnosticResult(
            reason=reason,
            category=category,
            confidence=confidence,
            description=self._generate_description(reason, error, context),
            suggestions=suggestions,
            retry_recommended=retry_recommended,
            retry_with_reduced_params=retry_with_reduced_params,
            technical_details={
                "error_analysis": analysis,
                "context": context,
                "classification_confidence": confidence
            }
        )
    
    def _generate_suggestions(
        self,
        reason: DisconnectionReason,
        category: ErrorCategory,
        context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate specific suggestions based on error classification."""
        suggestions = []
        
        # Base suggestions from error classifier
        from app.services.error_classifier import error_classifier
        classifier_suggestions = error_classifier.suggest_preventive_measures([{
            "reason": reason.value,
            "category": category.value,
            "context": context
        }])
        suggestions.extend(classifier_suggestions)
        
        # Context-specific suggestions
        image_size = context.get("image_size")
        region_count = context.get("region_count", 0)
        memory_available = context.get("memory_available_mb", 0)
        processing_duration = context.get("processing_duration", 0)
        
        if reason == DisconnectionReason.MEMORY_EXHAUSTION:
            suggestions.extend([
                f"Available memory: {memory_available:.0f}MB",
                "Consider reducing image resolution",
                "Process fewer text regions at once"
            ])
            if image_size:
                estimated_memory = self._estimate_memory_usage(image_size, region_count)
                suggestions.append(f"Estimated memory needed: {estimated_memory:.0f}MB")
        
        elif reason == DisconnectionReason.PROCESSING_TIMEOUT:
            suggestions.extend([
                f"Processing took {processing_duration:.1f}s before timeout",
                "Try reducing image complexity or region count",
                "Consider using faster processing parameters"
            ])
        
        elif reason == DisconnectionReason.CONNECTION_REFUSED:
            suggestions.extend([
                "Check if IOPaint service is running",
                "Verify port 8082 is accessible",
                "Restart IOPaint service if needed"
            ])
        
        elif reason == DisconnectionReason.IMAGE_TOO_LARGE:
            if image_size:
                megapixels = (image_size[0] * image_size[1]) / 1000000
                suggestions.extend([
                    f"Current image: {megapixels:.1f}MP",
                    "Resize image to maximum 5MP",
                    "Consider processing in sections"
                ])
        
        elif reason == DisconnectionReason.TOO_MANY_REGIONS:
            suggestions.extend([
                f"Processing {region_count} regions",
                "Try batching in groups of 10-20 regions",
                "Filter out low-confidence detections"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    def _determine_retry_strategy(
        self,
        reason: DisconnectionReason,
        category: ErrorCategory,
        context: Dict[str, Any]
    ) -> Tuple[bool, bool]:
        """Determine retry recommendations based on error type."""
        # Should retry, should retry with reduced parameters
        
        if category == ErrorCategory.CONNECTION:
            return True, False  # Retry connection issues without parameter changes
        
        elif category == ErrorCategory.TIMEOUT:
            return True, True   # Retry timeouts with reduced parameters
        
        elif category == ErrorCategory.RESOURCE:
            return True, True   # Retry resource issues with reduced parameters
        
        elif category == ErrorCategory.SERVICE:
            if reason == DisconnectionReason.SERVICE_CRASHED:
                return False, False  # Don't retry crashes - need manual intervention
            return True, False      # Other service issues can be retried
        
        elif category == ErrorCategory.INPUT:
            return True, True   # Retry input issues with parameter adjustments
        
        else:  # UNKNOWN
            return True, True   # Conservative approach for unknown errors
    
    def _generate_description(
        self,
        reason: DisconnectionReason,
        error: Exception,
        context: Dict[str, Any]
    ) -> str:
        """Generate a human-readable description of the error."""
        base_descriptions = {
            DisconnectionReason.NETWORK_TIMEOUT: "Network timeout while connecting to IOPaint service",
            DisconnectionReason.CONNECTION_REFUSED: "IOPaint service is not accepting connections",
            DisconnectionReason.PROCESSING_TIMEOUT: "Processing operation timed out",
            DisconnectionReason.MEMORY_EXHAUSTION: "Insufficient memory for processing",
            DisconnectionReason.GPU_MEMORY_EXHAUSTION: "GPU memory exhausted during processing",
            DisconnectionReason.SERVICE_CRASHED: "IOPaint service has crashed or stopped responding",
            DisconnectionReason.MODEL_LOADING_FAILED: "Failed to load AI model",
            DisconnectionReason.IMAGE_TOO_LARGE: "Image is too large for processing",
            DisconnectionReason.TOO_MANY_REGIONS: "Too many text regions to process efficiently",
            DisconnectionReason.INVALID_REQUEST: "Invalid request or corrupted data",
            DisconnectionReason.UNKNOWN_ERROR: f"Unknown error occurred: {type(error).__name__}"
        }
        
        description = base_descriptions.get(reason, f"Error: {error}")
        
        # Add context details
        processing_duration = context.get("processing_duration", 0)
        if processing_duration > 0:
            description += f" (after {processing_duration:.1f}s)"
        
        memory_available = context.get("memory_available_mb", 0)
        if reason in [DisconnectionReason.MEMORY_EXHAUSTION, DisconnectionReason.GPU_MEMORY_EXHAUSTION]:
            description += f" - {memory_available:.0f}MB available"
        
        return description
    
    async def _get_current_resources(self) -> ResourceMonitor:
        """Get current system resource usage."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return ResourceMonitor(
            memory_usage_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            cpu_usage_percent=cpu_percent,
            processing_time_seconds=0.0  # Will be set by caller
        )
    
    async def _check_service_status(self) -> Dict[str, Any]:
        """Check if IOPaint service process is running."""
        try:
            # Check if any process is listening on the IOPaint port
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and any('iopaint' in cmd.lower() for cmd in proc.info['cmdline']):
                        return {
                            "process_running": True,
                            "pid": proc.info['pid'],
                            "process_name": proc.info['name']
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "process_running": False,
                "pid": None,
                "process_name": None
            }
        except Exception as e:
            logger.warning(f"Failed to check service status: {e}")
            return {
                "process_running": None,
                "error": str(e)
            }
    
    async def _check_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to IOPaint service."""
        try:
            # Check if port is accessible
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', self.iopaint_port))
            sock.close()
            port_accessible = result == 0
            
            # Try HTTP health check if port is accessible
            health_status = None
            if port_accessible:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.base_url}/api/v1/model",
                            timeout=aiohttp.ClientTimeout(total=3)
                        ) as response:
                            health_status = response.status == 200
                except Exception:
                    health_status = False
            
            return {
                "port_accessible": port_accessible,
                "health_check_passed": health_status,
                "last_check_time": time.time()
            }
        except Exception as e:
            logger.warning(f"Failed to check connectivity: {e}")
            return {
                "port_accessible": False,
                "health_check_passed": False,
                "error": str(e)
            }
    
    def _estimate_memory_usage(self, image_size: Tuple[int, int, int], region_count: int) -> float:
        """Estimate memory usage for processing given image and regions."""
        height, width, channels = image_size
        
        # Base image memory (in memory multiple times during processing)
        base_memory = height * width * channels * 4 * 3  # 4 bytes per pixel, 3 copies
        
        # Mask memory
        mask_memory = height * width * 1  # 1 byte per pixel
        
        # Model memory (rough estimate)
        model_memory = 1024 * 1024 * 1024  # ~1GB for LAMA model
        
        # Region processing overhead
        region_overhead = region_count * 1024 * 100  # ~100KB per region
        
        total_bytes = base_memory + mask_memory + model_memory + region_overhead
        return total_bytes / 1024 / 1024  # Convert to MB


# Global diagnostics instance
iopaint_diagnostics = IOPaintDiagnosticsService()