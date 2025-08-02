"""Preprocessing validation and failure prediction for IOPaint processing."""
import asyncio
import psutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import numpy as np
from PIL import Image
import io
import base64

from app.services.diagnostics import DisconnectionReason


class RiskLevel(Enum):
    """Risk levels for processing failure."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    RESOURCE = "resource"
    IMAGE = "image"
    COMPLEXITY = "complexity"
    SYSTEM = "system"
    CONFIGURATION = "configuration"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    category: ValidationCategory
    risk_level: RiskLevel
    confidence: float
    description: str
    potential_failures: List[DisconnectionReason]
    recommendations: List[str]
    estimated_processing_time: Optional[float] = None
    estimated_memory_usage: Optional[float] = None


@dataclass
class PreprocessingReport:
    """Comprehensive preprocessing validation report."""
    overall_risk: RiskLevel
    total_score: float  # 0-100, higher is better
    validations: List[ValidationResult]
    processing_recommendations: List[str]
    parameter_adjustments: Dict[str, Any]
    should_proceed: bool
    warnings: List[str]
    estimated_resources: Dict[str, float]


class PreprocessingValidator:
    """Validates processing requests and predicts potential failures."""
    
    def __init__(self):
        self.validation_thresholds = {
            "max_safe_megapixels": 10.0,
            "max_safe_regions": 30,
            "min_memory_mb": 2000,
            "max_processing_time_s": 300,
            "max_cpu_usage_percent": 80,
            "min_disk_space_mb": 1000
        }
    
    async def validate_processing_request(
        self,
        image_b64: str,
        regions: List[Dict],
        processing_params: Optional[Dict] = None
    ) -> PreprocessingReport:
        """
        Perform comprehensive validation of processing request.
        
        Args:
            image_b64: Base64 encoded image
            regions: List of text regions to process
            processing_params: Optional processing parameters
            
        Returns:
            Comprehensive preprocessing validation report
        """
        logger.info(f"Validating processing request: {len(regions)} regions")
        
        validations = []
        warnings = []
        recommendations = []
        parameter_adjustments = {}
        estimated_resources = {}
        
        # Decode and analyze image
        try:
            image_data = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)
            image_size = image_np.shape
        except Exception as e:
            logger.error(f"Failed to decode image for validation: {e}")
            return PreprocessingReport(
                overall_risk=RiskLevel.CRITICAL,
                total_score=0.0,
                validations=[],
                processing_recommendations=["Fix image format issues"],
                parameter_adjustments={},
                should_proceed=False,
                warnings=[f"Image decoding failed: {e}"],
                estimated_resources={}
            )
        
        # Perform validation checks
        validations.extend(await self._validate_image_properties(image_size, image_data))
        validations.extend(await self._validate_region_complexity(regions, image_size))
        validations.extend(await self._validate_system_resources(image_size, regions))
        validations.extend(await self._validate_processing_parameters(processing_params))
        validations.extend(await self._validate_system_state())
        
        # Calculate overall risk and score
        overall_risk, total_score = self._calculate_overall_assessment(validations)
        
        # Generate recommendations and parameter adjustments
        recommendations = self._generate_processing_recommendations(validations, image_size, regions)
        parameter_adjustments = self._suggest_parameter_adjustments(validations, processing_params)
        
        # Estimate resource requirements
        estimated_resources = self._estimate_resource_requirements(image_size, regions, processing_params)
        
        # Determine if processing should proceed
        should_proceed = overall_risk != RiskLevel.CRITICAL and total_score >= 50.0
        
        # Collect warnings
        warnings = [v.description for v in validations if v.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        report = PreprocessingReport(
            overall_risk=overall_risk,
            total_score=total_score,
            validations=validations,
            processing_recommendations=recommendations,
            parameter_adjustments=parameter_adjustments,
            should_proceed=should_proceed,
            warnings=warnings,
            estimated_resources=estimated_resources
        )
        
        logger.info(f"Validation complete: {overall_risk.value} risk, score: {total_score:.1f}, proceed: {should_proceed}")
        return report
    
    async def _validate_image_properties(self, image_size: Tuple[int, int, int], image_data: bytes) -> List[ValidationResult]:
        """Validate image properties and characteristics."""
        validations = []
        
        height, width, channels = image_size
        megapixels = (height * width) / 1000000
        image_size_mb = len(image_data) / 1024 / 1024
        
        # Image size validation
        if megapixels > 25:  # Very large image
            validations.append(ValidationResult(
                category=ValidationCategory.IMAGE,
                risk_level=RiskLevel.CRITICAL,
                confidence=0.9,
                description=f"Image is extremely large ({megapixels:.1f}MP)",
                potential_failures=[DisconnectionReason.IMAGE_TOO_LARGE, DisconnectionReason.MEMORY_EXHAUSTION],
                recommendations=[
                    "Resize image to maximum 10MP before processing",
                    "Consider processing in smaller sections"
                ],
                estimated_processing_time=megapixels * 2.0,  # ~2 seconds per MP
                estimated_memory_usage=megapixels * 400     # ~400MB per MP
            ))
        elif megapixels > self.validation_thresholds["max_safe_megapixels"]:
            validations.append(ValidationResult(
                category=ValidationCategory.IMAGE,
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                description=f"Image is large ({megapixels:.1f}MP)",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT, DisconnectionReason.MEMORY_EXHAUSTION],
                recommendations=[
                    "Consider reducing image resolution",
                    "Monitor memory usage during processing"
                ],
                estimated_processing_time=megapixels * 1.5,
                estimated_memory_usage=megapixels * 300
            ))
        elif megapixels > 5:
            validations.append(ValidationResult(
                category=ValidationCategory.IMAGE,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                description=f"Image is moderately large ({megapixels:.1f}MP)",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=["Processing may take longer than usual"],
                estimated_processing_time=megapixels * 1.0,
                estimated_memory_usage=megapixels * 200
            ))
        else:
            validations.append(ValidationResult(
                category=ValidationCategory.IMAGE,
                risk_level=RiskLevel.LOW,
                confidence=0.9,
                description=f"Image size is acceptable ({megapixels:.1f}MP)",
                potential_failures=[],
                recommendations=[],
                estimated_processing_time=megapixels * 0.8,
                estimated_memory_usage=megapixels * 150
            ))
        
        # Image aspect ratio validation
        aspect_ratio = width / height
        if aspect_ratio > 5 or aspect_ratio < 0.2:  # Very wide or very tall
            validations.append(ValidationResult(
                category=ValidationCategory.IMAGE,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.6,
                description=f"Unusual aspect ratio ({aspect_ratio:.2f})",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=["Unusual aspect ratios may require more processing time"]
            ))
        
        # File size validation
        if image_size_mb > 50:  # Very large file
            validations.append(ValidationResult(
                category=ValidationCategory.IMAGE,
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                description=f"Large file size ({image_size_mb:.1f}MB)",
                potential_failures=[DisconnectionReason.MEMORY_EXHAUSTION],
                recommendations=["Large files require more memory for processing"]
            ))
        
        return validations
    
    async def _validate_region_complexity(self, regions: List[Dict], image_size: Tuple[int, int, int]) -> List[ValidationResult]:
        """Validate region count and complexity."""
        validations = []
        
        region_count = len(regions)
        height, width = image_size[0], image_size[1]
        
        # Region count validation
        if region_count > 100:
            validations.append(ValidationResult(
                category=ValidationCategory.COMPLEXITY,
                risk_level=RiskLevel.CRITICAL,
                confidence=0.9,
                description=f"Extremely high region count ({region_count})",
                potential_failures=[DisconnectionReason.TOO_MANY_REGIONS, DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=[
                    "Process regions in smaller batches (max 20 per batch)",
                    "Filter out low-confidence regions",
                    "Consider merging overlapping regions"
                ]
            ))
        elif region_count > self.validation_thresholds["max_safe_regions"]:
            validations.append(ValidationResult(
                category=ValidationCategory.COMPLEXITY,
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                description=f"High region count ({region_count})",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=[
                    "Consider processing in batches",
                    "Remove low-confidence detections"
                ]
            ))
        elif region_count > 15:
            validations.append(ValidationResult(
                category=ValidationCategory.COMPLEXITY,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                description=f"Moderate region count ({region_count})",
                potential_failures=[],
                recommendations=["Monitor processing time"]
            ))
        else:
            validations.append(ValidationResult(
                category=ValidationCategory.COMPLEXITY,
                risk_level=RiskLevel.LOW,
                confidence=0.9,
                description=f"Acceptable region count ({region_count})",
                potential_failures=[],
                recommendations=[]
            ))
        
        # Region coverage analysis
        if regions:
            total_region_area = 0
            for region in regions:
                bbox = region.get("bounding_box", {})
                if bbox:
                    w = bbox.get("width", 0)
                    h = bbox.get("height", 0)
                    total_region_area += w * h
            
            image_area = width * height
            coverage_percent = (total_region_area / image_area) * 100 if image_area > 0 else 0
            
            if coverage_percent > 50:
                validations.append(ValidationResult(
                    category=ValidationCategory.COMPLEXITY,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                    description=f"High text coverage ({coverage_percent:.1f}% of image)",
                    potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT, DisconnectionReason.MEMORY_EXHAUSTION],
                    recommendations=["High text coverage requires more processing resources"]
                ))
            elif coverage_percent > 25:
                validations.append(ValidationResult(
                    category=ValidationCategory.COMPLEXITY,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=0.7,
                    description=f"Moderate text coverage ({coverage_percent:.1f}% of image)",
                    potential_failures=[],
                    recommendations=["Monitor processing performance"]
                ))
        
        return validations
    
    async def _validate_system_resources(self, image_size: Tuple[int, int, int], regions: List[Dict]) -> List[ValidationResult]:
        """Validate current system resource availability."""
        validations = []
        
        # Memory validation
        memory = psutil.virtual_memory()
        available_mb = memory.available / 1024 / 1024
        
        # Estimate memory requirements
        height, width = image_size[0], image_size[1]
        megapixels = (height * width) / 1000000
        estimated_memory_mb = self._estimate_memory_usage(image_size, len(regions))
        
        if available_mb < self.validation_thresholds["min_memory_mb"]:
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.CRITICAL,
                confidence=0.9,
                description=f"Very low memory available ({available_mb:.0f}MB)",
                potential_failures=[DisconnectionReason.MEMORY_EXHAUSTION],
                recommendations=[
                    "Free up system memory before processing",
                    "Close unnecessary applications",
                    "Consider reducing image size"
                ]
            ))
        elif available_mb < estimated_memory_mb * 1.5:  # Not enough buffer
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                description=f"Limited memory for processing ({available_mb:.0f}MB available, ~{estimated_memory_mb:.0f}MB needed)",
                potential_failures=[DisconnectionReason.MEMORY_EXHAUSTION],
                recommendations=[
                    "Processing may fail due to insufficient memory",
                    "Consider reducing image resolution or region count"
                ]
            ))
        elif available_mb < estimated_memory_mb * 2:  # Tight memory
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                description=f"Adequate memory but limited buffer ({available_mb:.0f}MB available)",
                potential_failures=[],
                recommendations=["Monitor memory usage during processing"]
            ))
        else:
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.LOW,
                confidence=0.9,
                description=f"Sufficient memory available ({available_mb:.0f}MB)",
                potential_failures=[],
                recommendations=[]
            ))
        
        # CPU validation
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                description=f"Very high CPU usage ({cpu_percent:.1f}%)",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=["Wait for CPU usage to decrease before processing"]
            ))
        elif cpu_percent > self.validation_thresholds["max_cpu_usage_percent"]:
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                description=f"High CPU usage ({cpu_percent:.1f}%)",
                potential_failures=[],
                recommendations=["Processing may be slower due to high CPU load"]
            ))
        
        # Disk space validation
        disk_usage = psutil.disk_usage('/')
        free_mb = disk_usage.free / 1024 / 1024
        if free_mb < self.validation_thresholds["min_disk_space_mb"]:
            validations.append(ValidationResult(
                category=ValidationCategory.RESOURCE,
                risk_level=RiskLevel.HIGH,
                confidence=0.9,
                description=f"Low disk space ({free_mb:.0f}MB free)",
                potential_failures=[DisconnectionReason.UNKNOWN_ERROR],
                recommendations=["Free up disk space before processing"]
            ))
        
        return validations
    
    async def _validate_processing_parameters(self, processing_params: Optional[Dict]) -> List[ValidationResult]:
        """Validate processing parameters for potential issues."""
        validations = []
        
        if not processing_params:
            return validations
        
        # Validate SD steps
        sd_steps = processing_params.get("sd_steps", 25)
        if sd_steps > 50:
            validations.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                description=f"High SD steps ({sd_steps}) will increase processing time",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=["Consider reducing SD steps for faster processing"]
            ))
        
        # Validate HD strategy
        hd_strategy = processing_params.get("hd_strategy", "Original")
        if hd_strategy != "Original":
            validations.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION,
                risk_level=RiskLevel.MEDIUM,
                confidence=0.6,
                description=f"HD strategy '{hd_strategy}' may increase processing complexity",
                potential_failures=[DisconnectionReason.PROCESSING_TIMEOUT],
                recommendations=["HD strategies can significantly increase processing time"]
            ))
        
        return validations
    
    async def _validate_system_state(self) -> List[ValidationResult]:
        """Validate current system state and IOPaint service health."""
        validations = []
        
        # This could be expanded to check IOPaint service health,
        # but we'll keep it simple for now to avoid circular dependencies
        
        return validations
    
    def _calculate_overall_assessment(self, validations: List[ValidationResult]) -> Tuple[RiskLevel, float]:
        """Calculate overall risk level and score from validations."""
        if not validations:
            return RiskLevel.MEDIUM, 50.0
        
        # Count risk levels
        risk_counts = {
            RiskLevel.CRITICAL: 0,
            RiskLevel.HIGH: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.LOW: 0
        }
        
        total_confidence = 0.0
        for validation in validations:
            risk_counts[validation.risk_level] += 1
            total_confidence += validation.confidence
        
        # Determine overall risk
        if risk_counts[RiskLevel.CRITICAL] > 0:
            overall_risk = RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] > 1:
            overall_risk = RiskLevel.HIGH
        elif risk_counts[RiskLevel.HIGH] > 0 or risk_counts[RiskLevel.MEDIUM] > 2:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Calculate score (0-100)
        base_score = 100.0
        base_score -= risk_counts[RiskLevel.CRITICAL] * 40
        base_score -= risk_counts[RiskLevel.HIGH] * 20
        base_score -= risk_counts[RiskLevel.MEDIUM] * 10
        base_score += risk_counts[RiskLevel.LOW] * 5
        
        # Adjust by average confidence
        avg_confidence = total_confidence / len(validations)
        score = max(0.0, min(100.0, base_score * avg_confidence))
        
        return overall_risk, score
    
    def _generate_processing_recommendations(
        self,
        validations: List[ValidationResult],
        image_size: Tuple[int, int, int],
        regions: List[Dict]
    ) -> List[str]:
        """Generate processing recommendations based on validations."""
        recommendations = []
        
        # Collect all recommendations from validations
        for validation in validations:
            recommendations.extend(validation.recommendations)
        
        # Add general recommendations based on analysis
        height, width = image_size[0], image_size[1]
        megapixels = (height * width) / 1000000
        region_count = len(regions)
        
        if megapixels > 5 and region_count > 20:
            recommendations.append("Consider processing in smaller batches due to high complexity")
        
        if megapixels > 15:
            recommendations.append("Large image detected - ensure sufficient system resources")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _suggest_parameter_adjustments(
        self,
        validations: List[ValidationResult],
        current_params: Optional[Dict]
    ) -> Dict[str, Any]:
        """Suggest parameter adjustments to reduce failure risk."""
        adjustments = {}
        
        # Check for high-risk validations
        has_memory_risk = any(
            DisconnectionReason.MEMORY_EXHAUSTION in v.potential_failures
            for v in validations
        )
        
        has_timeout_risk = any(
            DisconnectionReason.PROCESSING_TIMEOUT in v.potential_failures
            for v in validations
        )
        
        if has_memory_risk or has_timeout_risk:
            # Suggest faster/lighter parameters
            adjustments.update({
                "sd_steps": 15,  # Reduce from default 25
                "hd_strategy": "Original",  # Use simplest strategy
                "sd_strength": 0.8,  # Reduce from default 1.0
            })
        
        if has_memory_risk:
            # Additional memory-saving parameters
            adjustments.update({
                "low_mem": True,
                "cpu_offload": True
            })
        
        return adjustments
    
    def _estimate_resource_requirements(
        self,
        image_size: Tuple[int, int, int],
        regions: List[Dict],
        processing_params: Optional[Dict]
    ) -> Dict[str, float]:
        """Estimate resource requirements for processing."""
        height, width = image_size[0], image_size[1]
        megapixels = (height * width) / 1000000
        region_count = len(regions)
        
        # Base estimates
        base_memory_mb = self._estimate_memory_usage(image_size, region_count)
        base_time_s = megapixels * 1.2 + region_count * 0.3
        
        # Adjust for parameters
        if processing_params:
            sd_steps = processing_params.get("sd_steps", 25)
            time_multiplier = sd_steps / 25.0
            base_time_s *= time_multiplier
            
            if processing_params.get("hd_strategy") != "Original":
                base_time_s *= 1.5  # HD strategies take longer
                base_memory_mb *= 1.3
        
        return {
            "estimated_memory_mb": base_memory_mb,
            "estimated_time_seconds": base_time_s,
            "estimated_cpu_percent": min(100, 30 + megapixels * 5),
            "estimated_disk_usage_mb": megapixels * 10  # Temporary files
        }
    
    def _estimate_memory_usage(self, image_size: Tuple[int, int, int], region_count: int) -> float:
        """Estimate memory usage for processing given image and regions."""
        height, width, channels = image_size
        
        # Base image memory (multiple copies during processing)
        base_memory = height * width * channels * 4 * 3  # 4 bytes per pixel, 3 copies
        
        # Mask memory
        mask_memory = height * width * 1  # 1 byte per pixel
        
        # Model memory (rough estimate)
        model_memory = 1024 * 1024 * 1024  # ~1GB for LAMA model
        
        # Region processing overhead
        region_overhead = region_count * 1024 * 100  # ~100KB per region
        
        total_bytes = base_memory + mask_memory + model_memory + region_overhead
        return total_bytes / 1024 / 1024  # Convert to MB


# Global preprocessing validator instance
preprocessing_validator = PreprocessingValidator()