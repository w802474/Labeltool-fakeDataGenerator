"""Intelligent retry mechanism for IOPaint processing failures."""
import asyncio
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from app.services.diagnostics import DisconnectionReason, ErrorCategory, DiagnosticResult


class RetryStrategy(Enum):
    """Different retry strategies based on error type."""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    PARAMETER_REDUCTION = "parameter_reduction"
    NO_RETRY = "no_retry"


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    timestamp: float
    strategy: RetryStrategy
    parameters_used: Dict[str, Any]
    backoff_delay: float
    reason: str
    success: Optional[bool] = None
    error: Optional[str] = None
    duration: Optional[float] = None


@dataclass
class RetryConfiguration:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    enable_parameter_reduction: bool = True
    enable_adaptive_parameters: bool = True
    timeout_per_attempt: float = 300.0  # 5 minutes


class IntelligentRetryManager:
    """Manages intelligent retry logic with adaptive strategies."""
    
    def __init__(self):
        self.retry_configs = self._build_retry_configurations()
        self.retry_history: Dict[str, List[RetryAttempt]] = {}
        self.success_patterns: Dict[str, Dict] = {}
        
    def _build_retry_configurations(self) -> Dict[DisconnectionReason, RetryConfiguration]:
        """Build retry configurations for different error types."""
        configs = {}
        
        # Connection errors - retry with backoff
        for reason in [DisconnectionReason.NETWORK_TIMEOUT, DisconnectionReason.CONNECTION_REFUSED]:
            configs[reason] = RetryConfiguration(
                max_attempts=3,
                base_delay=2.0,
                backoff_multiplier=2.0,
                enable_parameter_reduction=False
            )
        
        # Timeout errors - retry with parameter reduction
        for reason in [DisconnectionReason.PROCESSING_TIMEOUT]:
            configs[reason] = RetryConfiguration(
                max_attempts=3,
                base_delay=1.0,
                backoff_multiplier=1.5,
                enable_parameter_reduction=True
            )
        
        # Resource errors - retry with significant parameter reduction
        for reason in [DisconnectionReason.MEMORY_EXHAUSTION, DisconnectionReason.GPU_MEMORY_EXHAUSTION]:
            configs[reason] = RetryConfiguration(
                max_attempts=2,
                base_delay=5.0,
                backoff_multiplier=1.0,  # No exponential backoff for resource issues
                enable_parameter_reduction=True,
                enable_adaptive_parameters=True
            )
        
        # Input errors - retry with parameter adjustments
        for reason in [DisconnectionReason.IMAGE_TOO_LARGE, DisconnectionReason.TOO_MANY_REGIONS]:
            configs[reason] = RetryConfiguration(
                max_attempts=2,
                base_delay=1.0,
                backoff_multiplier=1.0,
                enable_parameter_reduction=True,
                enable_adaptive_parameters=True
            )
        
        # Service errors - limited retry
        configs[DisconnectionReason.SERVICE_CRASHED] = RetryConfiguration(
            max_attempts=1,
            base_delay=10.0,
            backoff_multiplier=1.0,
            enable_parameter_reduction=False
        )
        
        # Unknown errors - conservative retry
        configs[DisconnectionReason.UNKNOWN_ERROR] = RetryConfiguration(
            max_attempts=2,
            base_delay=3.0,
            backoff_multiplier=1.5,
            enable_parameter_reduction=True
        )
        
        return configs
    
    async def execute_with_retry(
        self,
        task_id: str,
        operation: Callable,
        diagnosis: DiagnosticResult,
        original_params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, Any, List[RetryAttempt]]:
        """
        Execute operation with intelligent retry logic.
        
        Args:
            task_id: Unique task identifier
            operation: Async function to execute
            diagnosis: Diagnostic result from failure analysis
            original_params: Original parameters for the operation
            context: Additional context (image_size, region_count, etc.)
            
        Returns:
            Tuple of (success, result, retry_attempts)
        """
        config = self.retry_configs.get(diagnosis.reason, RetryConfiguration())
        attempts = []
        
        logger.info(f"Task {task_id}: Starting retry with strategy for {diagnosis.reason.value}")
        
        for attempt_num in range(1, config.max_attempts + 1):
            # Determine retry strategy
            strategy = self._select_retry_strategy(diagnosis, attempt_num, config)
            
            # Calculate backoff delay
            backoff_delay = self._calculate_backoff_delay(attempt_num, config, strategy)
            
            # Adjust parameters for this attempt
            adjusted_params = self._adjust_parameters(
                original_params, 
                diagnosis, 
                attempt_num, 
                config, 
                context
            )
            
            # Create retry attempt record
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                timestamp=time.time(),
                strategy=strategy,
                parameters_used=adjusted_params.copy(),
                backoff_delay=backoff_delay,
                reason=f"Retry for {diagnosis.reason.value}"
            )
            attempts.append(attempt)
            
            # Wait before retry (except for first attempt)
            if attempt_num > 1 and backoff_delay > 0:
                logger.info(f"Task {task_id}: Waiting {backoff_delay:.1f}s before retry attempt {attempt_num}")
                await asyncio.sleep(backoff_delay)
            
            # Execute the operation
            logger.info(f"Task {task_id}: Retry attempt {attempt_num}/{config.max_attempts} "
                       f"with strategy {strategy.value}")
            
            start_time = time.time()
            try:
                result = await asyncio.wait_for(
                    operation(**adjusted_params),
                    timeout=config.timeout_per_attempt
                )
                
                # Success!
                attempt.success = True
                attempt.duration = time.time() - start_time
                
                logger.info(f"Task {task_id}: Retry attempt {attempt_num} succeeded "
                           f"({attempt.duration:.2f}s)")
                
                # Record successful pattern
                self._record_success_pattern(diagnosis.reason, attempt_num, adjusted_params, context)
                
                return True, result, attempts
                
            except Exception as e:
                attempt.success = False
                attempt.error = str(e)
                attempt.duration = time.time() - start_time
                
                logger.warning(f"Task {task_id}: Retry attempt {attempt_num} failed: {e}")
                
                # Don't retry if this was the last attempt
                if attempt_num == config.max_attempts:
                    logger.error(f"Task {task_id}: All {config.max_attempts} retry attempts failed")
                    break
                
                # Check if we should abort early
                if self._should_abort_retry(e, diagnosis):
                    logger.error(f"Task {task_id}: Aborting retry due to critical error")
                    break
        
        # All attempts failed
        self.retry_history[task_id] = attempts
        return False, None, attempts
    
    def _select_retry_strategy(
        self,
        diagnosis: DiagnosticResult,
        attempt_num: int,
        config: RetryConfiguration
    ) -> RetryStrategy:
        """Select appropriate retry strategy based on error type and attempt."""
        
        if diagnosis.category == ErrorCategory.CONNECTION:
            return RetryStrategy.EXPONENTIAL_BACKOFF
        
        elif diagnosis.category == ErrorCategory.TIMEOUT:
            if attempt_num == 1:
                return RetryStrategy.IMMEDIATE
            else:
                return RetryStrategy.PARAMETER_REDUCTION
        
        elif diagnosis.category == ErrorCategory.RESOURCE:
            return RetryStrategy.PARAMETER_REDUCTION
        
        elif diagnosis.category == ErrorCategory.INPUT:
            return RetryStrategy.PARAMETER_REDUCTION
        
        elif diagnosis.category == ErrorCategory.SERVICE:
            return RetryStrategy.LINEAR_BACKOFF
        
        else:  # UNKNOWN
            if attempt_num == 1:
                return RetryStrategy.IMMEDIATE
            else:
                return RetryStrategy.EXPONENTIAL_BACKOFF
    
    def _calculate_backoff_delay(
        self,
        attempt_num: int,
        config: RetryConfiguration,
        strategy: RetryStrategy
    ) -> float:
        """Calculate backoff delay for retry attempt."""
        
        if strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(config.base_delay * attempt_num, config.max_delay)
        
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(config.base_delay * (config.backoff_multiplier ** (attempt_num - 1)), config.max_delay)
        
        elif strategy == RetryStrategy.PARAMETER_REDUCTION:
            # Short delay for parameter adjustments
            return config.base_delay * 0.5
        
        else:
            return config.base_delay
    
    def _adjust_parameters(
        self,
        original_params: Dict[str, Any],
        diagnosis: DiagnosticResult,
        attempt_num: int,
        config: RetryConfiguration,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adjust parameters for retry attempt based on error diagnosis."""
        
        params = original_params.copy()
        
        if not config.enable_parameter_reduction:
            return params
        
        # Apply progressive parameter reduction
        reduction_factor = 1.0 - (0.2 * attempt_num)  # Reduce by 20% per attempt
        
        if diagnosis.reason == DisconnectionReason.MEMORY_EXHAUSTION:
            # Aggressive memory reduction
            params.update({
                "sd_steps": max(10, int(params.get("sd_steps", 25) * reduction_factor)),
                "hd_strategy": "Original",  # Force simplest strategy
                "sd_strength": max(0.5, params.get("sd_strength", 1.0) * reduction_factor),
                "low_mem": True,
                "cpu_offload": True
            })
        
        elif diagnosis.reason == DisconnectionReason.PROCESSING_TIMEOUT:
            # Speed optimization
            params.update({
                "sd_steps": max(5, int(params.get("sd_steps", 25) * reduction_factor)),
                "sd_guidance_scale": max(3.0, params.get("sd_guidance_scale", 7.5) * reduction_factor),
                "hd_strategy": "Original"
            })
        
        elif diagnosis.reason == DisconnectionReason.IMAGE_TOO_LARGE:
            # Adjust for large images
            params.update({
                "hd_strategy_crop_trigger_size": max(512, int(params.get("hd_strategy_crop_trigger_size", 1280) * reduction_factor)),
                "sd_steps": max(10, int(params.get("sd_steps", 25) * reduction_factor))
            })
        
        elif diagnosis.reason == DisconnectionReason.TOO_MANY_REGIONS:
            # Optimize for many regions
            params.update({
                "sd_steps": max(8, int(params.get("sd_steps", 25) * reduction_factor)),
                "sd_strength": max(0.6, params.get("sd_strength", 1.0) * reduction_factor)
            })
        
        # Apply adaptive parameters based on successful patterns
        if config.enable_adaptive_parameters:
            adaptive_params = self._get_adaptive_parameters(diagnosis.reason, context)
            params.update(adaptive_params)
        
        logger.debug(f"Parameter adjustment for attempt {attempt_num}: {params}")
        return params
    
    def _get_adaptive_parameters(
        self,
        reason: DisconnectionReason,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get adaptive parameters based on historical success patterns."""
        
        success_pattern = self.success_patterns.get(reason.value, {})
        if not success_pattern:
            return {}
        
        # Use parameters from most successful attempts
        return success_pattern.get("best_parameters", {})
    
    def _should_abort_retry(self, error: Exception, diagnosis: DiagnosticResult) -> bool:
        """Determine if retry should be aborted early."""
        
        error_str = str(error).lower()
        
        # Abort for critical system errors
        if any(keyword in error_str for keyword in [
            "permission denied", "disk full", "no space", "segmentation fault"
        ]):
            return True
        
        # Abort if service has definitely crashed
        if diagnosis.reason == DisconnectionReason.SERVICE_CRASHED:
            if "connection refused" in error_str or "no route to host" in error_str:
                return True
        
        return False
    
    def _record_success_pattern(
        self,
        reason: DisconnectionReason,
        successful_attempt: int,
        successful_params: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Record successful retry pattern for future use."""
        
        reason_key = reason.value
        if reason_key not in self.success_patterns:
            self.success_patterns[reason_key] = {
                "success_count": 0,
                "successful_attempts": [],
                "best_parameters": {},
                "contexts": []
            }
        
        pattern = self.success_patterns[reason_key]
        pattern["success_count"] += 1
        pattern["successful_attempts"].append(successful_attempt)
        pattern["contexts"].append(context)
        
        # Update best parameters based on most frequent success patterns
        if pattern["success_count"] >= 3:  # Need multiple successes to establish pattern
            # Find most common successful parameters
            param_frequency = {}
            for param_key, param_value in successful_params.items():
                if param_key not in param_frequency:
                    param_frequency[param_key] = {}
                if param_value not in param_frequency[param_key]:
                    param_frequency[param_key][param_value] = 0
                param_frequency[param_key][param_value] += 1
            
            # Update best parameters with most frequent values
            best_params = {}
            for param_key, value_counts in param_frequency.items():
                most_common_value = max(value_counts.items(), key=lambda x: x[1])[0]
                best_params[param_key] = most_common_value
            
            pattern["best_parameters"] = best_params
        
        logger.info(f"Recorded success pattern for {reason.value}: attempt {successful_attempt}")
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get statistics about retry patterns and success rates."""
        
        stats = {
            "total_tasks_with_retries": len(self.retry_history),
            "success_patterns": {},
            "common_retry_strategies": {},
            "average_attempts_to_success": {}
        }
        
        # Analyze success patterns
        for reason, pattern in self.success_patterns.items():
            stats["success_patterns"][reason] = {
                "success_count": pattern["success_count"],
                "average_attempts": sum(pattern["successful_attempts"]) / len(pattern["successful_attempts"]),
                "best_parameters": pattern["best_parameters"]
            }
        
        # Analyze retry history
        strategy_counts = {}
        for task_attempts in self.retry_history.values():
            for attempt in task_attempts:
                strategy = attempt.strategy.value
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        stats["common_retry_strategies"] = strategy_counts
        
        return stats
    
    def get_recommendations_for_error(self, reason: DisconnectionReason) -> List[str]:
        """Get specific recommendations for handling a particular error type."""
        
        recommendations = []
        
        # Check if we have success patterns for this error
        if reason.value in self.success_patterns:
            pattern = self.success_patterns[reason.value]
            if pattern["success_count"] > 0:
                avg_attempts = sum(pattern["successful_attempts"]) / len(pattern["successful_attempts"])
                recommendations.append(f"Historical data shows this error typically resolves after {avg_attempts:.1f} attempts")
                
                if pattern["best_parameters"]:
                    recommendations.append("Consider using proven successful parameters:")
                    for param, value in pattern["best_parameters"].items():
                        recommendations.append(f"  - {param}: {value}")
        
        # Generic recommendations based on error type
        if reason in [DisconnectionReason.MEMORY_EXHAUSTION, DisconnectionReason.GPU_MEMORY_EXHAUSTION]:
            recommendations.extend([
                "Reduce sd_steps to 10-15 for faster processing",
                "Use 'Original' HD strategy to minimize memory usage",
                "Enable cpu_offload and low_mem options"
            ])
        
        elif reason == DisconnectionReason.PROCESSING_TIMEOUT:
            recommendations.extend([
                "Reduce sd_steps and sd_guidance_scale",
                "Use simpler HD strategy",
                "Consider processing fewer regions at once"
            ])
        
        elif reason in [DisconnectionReason.IMAGE_TOO_LARGE, DisconnectionReason.TOO_MANY_REGIONS]:
            recommendations.extend([
                "Process image in smaller sections",
                "Reduce region count per batch",
                "Use faster processing parameters"
            ])
        
        return recommendations


# Global retry manager instance
retry_manager = IntelligentRetryManager()