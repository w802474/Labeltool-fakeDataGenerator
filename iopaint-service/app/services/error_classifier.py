"""Advanced error classification and pattern recognition for IOPaint failures."""
import re
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from app.services.diagnostics import DisconnectionReason, ErrorCategory, DiagnosticResult


class ErrorPattern(Enum):
    """Predefined error patterns for classification."""
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused" 
    SOCKET_ERROR = "socket_error"
    MEMORY_ERROR = "memory_error"
    GPU_ERROR = "gpu_error"
    MODEL_ERROR = "model_error"
    IMAGE_FORMAT_ERROR = "image_format_error"
    PROCESSING_TIMEOUT = "processing_timeout"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DISK_SPACE_ERROR = "disk_space_error"
    PERMISSION_ERROR = "permission_error"


@dataclass
class ErrorSignature:
    """Signature for identifying specific error types."""
    pattern: ErrorPattern
    keywords: List[str]
    error_types: List[str]
    confidence_boost: float
    category: ErrorCategory
    reason: DisconnectionReason
    
    def matches(self, error_str: str, error_type: str) -> float:
        """Check if error matches this signature and return confidence score."""
        error_lower = error_str.lower()
        type_lower = error_type.lower()
        
        # Check error type match
        type_match = any(et in type_lower for et in self.error_types)
        
        # Check keyword matches
        keyword_matches = sum(1 for keyword in self.keywords if keyword in error_lower)
        keyword_score = keyword_matches / len(self.keywords) if self.keywords else 0
        
        # Calculate base confidence
        base_confidence = 0.0
        if type_match:
            base_confidence += 0.5
        base_confidence += keyword_score * 0.5
        
        # Apply confidence boost if matches
        if base_confidence > 0:
            base_confidence = min(1.0, base_confidence + self.confidence_boost)
        
        return base_confidence


class AdvancedErrorClassifier:
    """Advanced error classifier using pattern matching and machine learning-like heuristics."""
    
    def __init__(self):
        self.error_signatures = self._build_error_signatures()
        self.error_history: List[Dict] = []
        self.pattern_learning: Dict[str, int] = {}
        
    def _build_error_signatures(self) -> List[ErrorSignature]:
        """Build comprehensive error signature database."""
        return [
            # Connection-related errors
            ErrorSignature(
                pattern=ErrorPattern.CONNECTION_TIMEOUT,
                keywords=["timeout", "timed out", "timeouterror"],
                error_types=["timeouterror", "asyncio.timeouterror", "clienttimeouterror"],
                confidence_boost=0.3,
                category=ErrorCategory.TIMEOUT,
                reason=DisconnectionReason.NETWORK_TIMEOUT
            ),
            
            ErrorSignature(
                pattern=ErrorPattern.CONNECTION_REFUSED,
                keywords=["connection refused", "refused", "connect", "unreachable"],
                error_types=["connectionrefusederror", "clientconnectorerror", "oserror"],
                confidence_boost=0.4,
                category=ErrorCategory.CONNECTION,
                reason=DisconnectionReason.CONNECTION_REFUSED
            ),
            
            ErrorSignature(
                pattern=ErrorPattern.SOCKET_ERROR,
                keywords=["socket", "broken pipe", "connection reset", "network"],
                error_types=["socketerror", "brokenPipeerror", "connectionreseterror"],
                confidence_boost=0.3,
                category=ErrorCategory.CONNECTION,
                reason=DisconnectionReason.NETWORK_TIMEOUT
            ),
            
            # Memory-related errors
            ErrorSignature(
                pattern=ErrorPattern.MEMORY_ERROR,
                keywords=["memory", "oom", "out of memory", "malloc", "allocation failed"],
                error_types=["memoryerror", "runtimeerror"],
                confidence_boost=0.4,
                category=ErrorCategory.RESOURCE,
                reason=DisconnectionReason.MEMORY_EXHAUSTION
            ),
            
            # GPU-related errors
            ErrorSignature(
                pattern=ErrorPattern.GPU_ERROR,
                keywords=["cuda", "gpu", "device", "cudart", "out of memory"],
                error_types=["runtimeerror", "cudaerror"],
                confidence_boost=0.4,
                category=ErrorCategory.RESOURCE,
                reason=DisconnectionReason.GPU_MEMORY_EXHAUSTION
            ),
            
            # Model and processing errors
            ErrorSignature(
                pattern=ErrorPattern.MODEL_ERROR,
                keywords=["model", "weights", "checkpoint", "loading", "corrupted"],
                error_types=["runtimeerror", "valueerror", "filenotfounderror"],
                confidence_boost=0.3,
                category=ErrorCategory.SERVICE,
                reason=DisconnectionReason.MODEL_LOADING_FAILED
            ),
            
            ErrorSignature(
                pattern=ErrorPattern.IMAGE_FORMAT_ERROR,
                keywords=["image", "format", "decode", "invalid", "corrupted", "cannot identify"],
                error_types=["pillow", "valueerror", "ioerror"],
                confidence_boost=0.4,
                category=ErrorCategory.INPUT,
                reason=DisconnectionReason.INVALID_REQUEST
            ),
            
            # Processing timeouts
            ErrorSignature(
                pattern=ErrorPattern.PROCESSING_TIMEOUT,
                keywords=["processing", "inference", "taking too long", "stuck"],
                error_types=["timeouterror"],
                confidence_boost=0.3,
                category=ErrorCategory.TIMEOUT,
                reason=DisconnectionReason.PROCESSING_TIMEOUT
            ),
            
            # Service availability
            ErrorSignature(
                pattern=ErrorPattern.SERVICE_UNAVAILABLE,
                keywords=["service unavailable", "not ready", "starting", "initializing"],
                error_types=["connectionerror", "httperror"],
                confidence_boost=0.3,
                category=ErrorCategory.SERVICE,
                reason=DisconnectionReason.SERVICE_CRASHED
            ),
            
            # Disk and I/O errors
            ErrorSignature(
                pattern=ErrorPattern.DISK_SPACE_ERROR,
                keywords=["disk", "space", "full", "no space", "disk full"],
                error_types=["oserror", "ioerror"],
                confidence_boost=0.4,
                category=ErrorCategory.RESOURCE,
                reason=DisconnectionReason.UNKNOWN_ERROR
            ),
            
            ErrorSignature(
                pattern=ErrorPattern.PERMISSION_ERROR,
                keywords=["permission", "denied", "access", "forbidden"],
                error_types=["permissionerror", "oserror"],
                confidence_boost=0.4,
                category=ErrorCategory.SERVICE,
                reason=DisconnectionReason.UNKNOWN_ERROR
            )
        ]
    
    def classify_error(
        self,
        error: Exception,
        context: Optional[Dict] = None
    ) -> Tuple[DisconnectionReason, ErrorCategory, float, Dict]:
        """
        Classify error using advanced pattern matching and context analysis.
        
        Args:
            error: The exception to classify
            context: Additional context (image_size, region_count, processing_time, etc.)
            
        Returns:
            Tuple of (reason, category, confidence, analysis_details)
        """
        error_str = str(error)
        error_type = type(error).__name__
        
        logger.debug(f"Classifying error: {error_type} - {error_str}")
        
        # Initialize analysis
        analysis = {
            "error_type": error_type,
            "error_message": error_str,
            "context": context or {},
            "pattern_matches": [],
            "heuristic_scores": {},
            "final_reasoning": []
        }
        
        # Pattern matching phase
        best_match = None
        best_confidence = 0.0
        
        for signature in self.error_signatures:
            confidence = signature.matches(error_str, error_type)
            if confidence > 0:
                analysis["pattern_matches"].append({
                    "pattern": signature.pattern.value,
                    "confidence": confidence,
                    "reason": signature.reason.value,
                    "category": signature.category.value
                })
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = signature
        
        # Context-based heuristics
        if context:
            heuristic_adjustments = self._apply_context_heuristics(error_str, error_type, context)
            analysis["heuristic_scores"] = heuristic_adjustments
            
            # Adjust confidence based on context
            for adjustment in heuristic_adjustments.values():
                if adjustment.get("boost_confidence"):
                    best_confidence = min(1.0, best_confidence + adjustment["boost_confidence"])
                    analysis["final_reasoning"].append(adjustment["reasoning"])
        
        # Historical pattern learning
        historical_boost = self._get_historical_pattern_boost(error_str, error_type)
        if historical_boost > 0:
            best_confidence = min(1.0, best_confidence + historical_boost)
            analysis["final_reasoning"].append(f"Historical pattern recognition boost: +{historical_boost:.2f}")
        
        # Determine final classification
        if best_match and best_confidence > 0.3:
            reason = best_match.reason
            category = best_match.category
            analysis["final_reasoning"].append(f"Matched pattern: {best_match.pattern.value}")
        else:
            # Fallback classification
            reason, category = self._fallback_classification(error_str, error_type, context)
            best_confidence = max(0.2, best_confidence)  # Minimum confidence for fallback
            analysis["final_reasoning"].append("Used fallback classification")
        
        # Record error for learning
        self._record_error_for_learning(error_str, error_type, reason, category, best_confidence)
        
        logger.debug(f"Error classified as: {reason.value} ({category.value}) with confidence {best_confidence:.2f}")
        
        return reason, category, best_confidence, analysis
    
    def _apply_context_heuristics(
        self,
        error_str: str,
        error_type: str,
        context: Dict
    ) -> Dict[str, Dict]:
        """Apply context-based heuristics to improve classification."""
        heuristics = {}
        
        # Image size heuristics
        image_size = context.get("image_size")
        if image_size:
            height, width = image_size[0], image_size[1]
            megapixels = (height * width) / 1000000
            
            if megapixels > 10:  # Very large image
                heuristics["large_image"] = {
                    "boost_confidence": 0.2,
                    "reasoning": f"Large image ({megapixels:.1f}MP) increases likelihood of memory/processing issues"
                }
        
        # Region count heuristics
        region_count = context.get("region_count", 0)
        if region_count > 50:
            heuristics["many_regions"] = {
                "boost_confidence": 0.15,
                "reasoning": f"High region count ({region_count}) increases processing complexity"
            }
        
        # Processing time heuristics
        processing_time = context.get("processing_duration", 0)
        if processing_time > 300:  # > 5 minutes
            if "timeout" in error_str.lower():
                heuristics["long_processing"] = {
                    "boost_confidence": 0.25,
                    "reasoning": f"Long processing time ({processing_time:.1f}s) supports timeout classification"
                }
        
        # Memory usage heuristics
        memory_mb = context.get("memory_usage_mb", 0)
        if memory_mb > 6000:  # > 6GB
            if any(keyword in error_str.lower() for keyword in ["memory", "allocation", "oom"]):
                heuristics["high_memory"] = {
                    "boost_confidence": 0.3,
                    "reasoning": f"High memory usage ({memory_mb:.0f}MB) supports memory exhaustion"
                }
        
        return heuristics
    
    def _get_historical_pattern_boost(self, error_str: str, error_type: str) -> float:
        """Get confidence boost based on historical error patterns."""
        error_hash = self._hash_error(error_str, error_type)
        frequency = self.pattern_learning.get(error_hash, 0)
        
        # Boost confidence for frequently seen errors
        if frequency > 5:
            return 0.1
        elif frequency > 2:
            return 0.05
        
        return 0.0
    
    def _fallback_classification(
        self,
        error_str: str,
        error_type: str,
        context: Optional[Dict]
    ) -> Tuple[DisconnectionReason, ErrorCategory]:
        """Provide fallback classification when no patterns match well."""
        error_lower = error_str.lower()
        
        # Simple keyword-based fallback
        if any(word in error_lower for word in ["timeout", "time"]):
            return DisconnectionReason.NETWORK_TIMEOUT, ErrorCategory.TIMEOUT
        
        if any(word in error_lower for word in ["connection", "connect", "refused"]):
            return DisconnectionReason.CONNECTION_REFUSED, ErrorCategory.CONNECTION
        
        if any(word in error_lower for word in ["memory", "allocation"]):
            return DisconnectionReason.MEMORY_EXHAUSTION, ErrorCategory.RESOURCE
        
        if any(word in error_lower for word in ["server", "service", "unavailable"]):
            return DisconnectionReason.SERVICE_CRASHED, ErrorCategory.SERVICE
        
        # Check context for additional clues
        if context:
            image_size = context.get("image_size")
            if image_size and (image_size[0] * image_size[1]) > 20000000:  # Very large
                return DisconnectionReason.IMAGE_TOO_LARGE, ErrorCategory.INPUT
        
        return DisconnectionReason.UNKNOWN_ERROR, ErrorCategory.UNKNOWN
    
    def _record_error_for_learning(
        self,
        error_str: str,
        error_type: str,
        reason: DisconnectionReason,
        category: ErrorCategory,
        confidence: float
    ):
        """Record error for pattern learning."""
        error_hash = self._hash_error(error_str, error_type)
        self.pattern_learning[error_hash] = self.pattern_learning.get(error_hash, 0) + 1
        
        # Store in history (keep last 100 errors)
        self.error_history.append({
            "timestamp": time.time(),
            "error_hash": error_hash,
            "error_type": error_type,
            "reason": reason.value,
            "category": category.value,
            "confidence": confidence
        })
        
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def _hash_error(self, error_str: str, error_type: str) -> str:
        """Create a hash for error pattern recognition."""
        # Normalize error string for pattern matching
        normalized = re.sub(r'\d+', 'N', error_str.lower())  # Replace numbers with N
        normalized = re.sub(r'[^\w\s]', ' ', normalized)     # Remove special chars
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        
        return f"{error_type}:{hash(normalized) % 10000}"
    
    def get_error_statistics(self) -> Dict:
        """Get statistics about error patterns."""
        if not self.error_history:
            return {"total_errors": 0}
        
        stats = {
            "total_errors": len(self.error_history),
            "by_reason": {},
            "by_category": {},
            "average_confidence": 0.0,
            "most_common_patterns": []
        }
        
        # Calculate statistics
        for error in self.error_history:
            reason = error["reason"]
            category = error["category"]
            
            stats["by_reason"][reason] = stats["by_reason"].get(reason, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # Average confidence
        total_confidence = sum(error["confidence"] for error in self.error_history)
        stats["average_confidence"] = total_confidence / len(self.error_history)
        
        # Most common patterns
        pattern_counts = sorted(self.pattern_learning.items(), key=lambda x: x[1], reverse=True)
        stats["most_common_patterns"] = pattern_counts[:5]
        
        return stats
    
    def suggest_preventive_measures(self, recent_errors: Optional[List] = None) -> List[str]:
        """Suggest preventive measures based on error patterns."""
        suggestions = []
        
        errors_to_analyze = recent_errors or self.error_history[-10:]  # Last 10 errors
        
        if not errors_to_analyze:
            return suggestions
        
        # Analyze patterns in recent errors
        reason_counts = {}
        for error in errors_to_analyze:
            reason = error.get("reason", "unknown")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Generate suggestions based on common patterns
        if reason_counts.get("memory_exhaustion", 0) > 2:
            suggestions.extend([
                "Consider reducing image resolution before processing",
                "Process fewer text regions simultaneously",
                "Increase system memory or use swap file"
            ])
        
        if reason_counts.get("network_timeout", 0) > 2:
            suggestions.extend([
                "Increase network timeout values",
                "Check network stability and IOPaint service health",
                "Consider breaking large tasks into smaller chunks"
            ])
        
        if reason_counts.get("processing_timeout", 0) > 2:
            suggestions.extend([
                "Use faster processing parameters",
                "Enable GPU acceleration if available",
                "Split complex images into smaller sections"
            ])
        
        if reason_counts.get("service_crashed", 0) > 1:
            suggestions.extend([
                "Check IOPaint service logs for crash details",
                "Verify system resources are sufficient",
                "Consider restarting IOPaint service regularly"
            ])
        
        return suggestions


# Global error classifier instance
error_classifier = AdvancedErrorClassifier()