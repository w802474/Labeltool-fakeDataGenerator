"""Real-time resource monitoring during IOPaint processing."""
import asyncio
import time
import psutil
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    timestamp: float
    memory_used_mb: float
    memory_available_mb: float
    memory_percent: float
    cpu_percent: float
    gpu_memory_mb: Optional[float] = None
    gpu_utilization: Optional[float] = None
    disk_io_read_mb: Optional[float] = None
    disk_io_write_mb: Optional[float] = None


@dataclass
class ProcessingMetrics:
    """Metrics collected during processing."""
    start_time: float
    end_time: Optional[float] = None
    snapshots: List[ResourceSnapshot] = field(default_factory=list)
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    memory_growth_mb: float = 0.0
    processing_phases: Dict[str, Dict[str, float]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Get processing duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def memory_efficiency_score(self) -> float:
        """Calculate memory efficiency score (0-100)."""
        if not self.snapshots:
            return 0.0
        
        total_memory = self.snapshots[0].memory_used_mb + self.snapshots[0].memory_available_mb
        efficiency = max(0, 100 - (self.peak_memory_mb / total_memory * 100))
        return efficiency


class RealTimeResourceMonitor:
    """Real-time monitoring of system resources during IOPaint processing."""
    
    def __init__(self, monitoring_interval: float = 0.5):
        """
        Initialize resource monitor.
        
        Args:
            monitoring_interval: How often to collect resource snapshots (seconds)
        """
        self.monitoring_interval = monitoring_interval
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._current_metrics: Optional[ProcessingMetrics] = None
        self._callbacks: List[Callable[[ResourceSnapshot], None]] = []
        
    def add_callback(self, callback: Callable[[ResourceSnapshot], None]):
        """Add callback to be called when resource snapshot is taken."""
        self._callbacks.append(callback)
    
    def start_monitoring(self, task_id: Optional[str] = None) -> ProcessingMetrics:
        """
        Start resource monitoring for a processing task.
        
        Args:
            task_id: Optional task identifier for logging
            
        Returns:
            ProcessingMetrics object that will be populated during monitoring
        """
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Resource monitoring already running")
            return self._current_metrics
        
        self._current_metrics = ProcessingMetrics(start_time=time.time())
        self._stop_event.clear()
        
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(
            self._monitor_loop(task_id or "unknown")
        )
        
        logger.info(f"Started resource monitoring for task: {task_id}")
        return self._current_metrics
    
    async def stop_monitoring(self) -> ProcessingMetrics:
        """
        Stop resource monitoring and return final metrics.
        
        Returns:
            Final ProcessingMetrics with complete data
        """
        if not self._current_metrics:
            logger.warning("No active monitoring to stop")
            return ProcessingMetrics(start_time=time.time(), end_time=time.time())
        
        # Signal stop and wait for monitoring task to complete
        self._stop_event.set()
        
        if self._monitoring_task:
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Monitoring task didn't stop gracefully")
                self._monitoring_task.cancel()
        
        # Finalize metrics
        self._current_metrics.end_time = time.time()
        self._calculate_final_metrics()
        
        logger.info(f"Resource monitoring stopped. Duration: {self._current_metrics.duration_seconds:.2f}s")
        return self._current_metrics
    
    async def _monitor_loop(self, task_id: str):
        """Main monitoring loop that collects resource snapshots."""
        logger.debug(f"Resource monitoring loop started for task: {task_id}")
        
        try:
            while not self._stop_event.is_set():
                snapshot = self._take_snapshot()
                self._current_metrics.snapshots.append(snapshot)
                
                # Update peak memory
                if snapshot.memory_used_mb > self._current_metrics.peak_memory_mb:
                    self._current_metrics.peak_memory_mb = snapshot.memory_used_mb
                
                # Check for resource warnings
                self._check_resource_warnings(snapshot)
                
                # Call registered callbacks
                for callback in self._callbacks:
                    try:
                        callback(snapshot)
                    except Exception as e:
                        logger.warning(f"Resource monitor callback failed: {e}")
                
                await asyncio.sleep(self.monitoring_interval)
                
        except asyncio.CancelledError:
            logger.debug("Resource monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in resource monitoring loop: {e}")
    
    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current system resources."""
        # Memory information
        memory = psutil.virtual_memory()
        
        # CPU usage (non-blocking)
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Try to get GPU information (if available)
        gpu_memory_mb = None
        gpu_utilization = None
        try:
            import nvidia_ml_py3 as nvml
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)  # First GPU
            gpu_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_util = nvml.nvmlDeviceGetUtilizationRates(handle)
            
            gpu_memory_mb = gpu_info.used / 1024 / 1024
            gpu_utilization = gpu_util.gpu
        except Exception:
            # GPU monitoring not available
            pass
        
        # Disk I/O (simplified)
        disk_io_read_mb = None
        disk_io_write_mb = None
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_io_read_mb = disk_io.read_bytes / 1024 / 1024
                disk_io_write_mb = disk_io.write_bytes / 1024 / 1024
        except Exception:
            pass
        
        return ResourceSnapshot(
            timestamp=time.time(),
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            memory_percent=memory.percent,
            cpu_percent=cpu_percent,
            gpu_memory_mb=gpu_memory_mb,
            gpu_utilization=gpu_utilization,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb
        )
    
    def _check_resource_warnings(self, snapshot: ResourceSnapshot):
        """Check for resource-related warnings and add to metrics."""
        warnings = []
        
        # Memory warnings
        if snapshot.memory_percent > 90:
            warnings.append(f"Critical memory usage: {snapshot.memory_percent:.1f}%")
        elif snapshot.memory_percent > 80:
            warnings.append(f"High memory usage: {snapshot.memory_percent:.1f}%")
        
        # CPU warnings
        if snapshot.cpu_percent > 95:
            warnings.append(f"Very high CPU usage: {snapshot.cpu_percent:.1f}%")
        
        # GPU warnings
        if snapshot.gpu_memory_mb and snapshot.gpu_memory_mb > 8000:  # 8GB threshold
            warnings.append(f"High GPU memory usage: {snapshot.gpu_memory_mb:.0f}MB")
        
        # Memory growth warnings
        if len(self._current_metrics.snapshots) > 1:
            memory_growth = snapshot.memory_used_mb - self._current_metrics.snapshots[0].memory_used_mb
            if memory_growth > 2000:  # 2GB growth
                warnings.append(f"Significant memory growth: +{memory_growth:.0f}MB")
        
        # Add unique warnings
        for warning in warnings:
            if warning not in self._current_metrics.warnings:
                self._current_metrics.warnings.append(warning)
                logger.warning(f"Resource warning: {warning}")
    
    def _calculate_final_metrics(self):
        """Calculate final aggregated metrics from snapshots."""
        if not self._current_metrics.snapshots:
            return
        
        snapshots = self._current_metrics.snapshots
        
        # Calculate average CPU usage
        if snapshots:
            self._current_metrics.avg_cpu_percent = sum(s.cpu_percent for s in snapshots) / len(snapshots)
        
        # Calculate memory growth
        if len(snapshots) > 1:
            self._current_metrics.memory_growth_mb = (
                snapshots[-1].memory_used_mb - snapshots[0].memory_used_mb
            )
        
        logger.info(f"Final metrics: Peak memory: {self._current_metrics.peak_memory_mb:.0f}MB, "
                   f"Avg CPU: {self._current_metrics.avg_cpu_percent:.1f}%, "
                   f"Memory growth: {self._current_metrics.memory_growth_mb:.0f}MB, "
                   f"Efficiency score: {self._current_metrics.memory_efficiency_score:.1f}")
    
    def mark_processing_phase(self, phase_name: str):
        """Mark the start of a processing phase for detailed timing analysis."""
        if not self._current_metrics:
            return
        
        current_time = time.time()
        phase_data = {
            "start_time": current_time,
            "start_memory_mb": self._current_metrics.snapshots[-1].memory_used_mb if self._current_metrics.snapshots else 0
        }
        
        self._current_metrics.processing_phases[phase_name] = phase_data
        logger.debug(f"Started processing phase: {phase_name}")
    
    def end_processing_phase(self, phase_name: str):
        """Mark the end of a processing phase."""
        if not self._current_metrics or phase_name not in self._current_metrics.processing_phases:
            return
        
        current_time = time.time()
        phase_data = self._current_metrics.processing_phases[phase_name]
        
        phase_data["end_time"] = current_time
        phase_data["duration"] = current_time - phase_data["start_time"]
        
        if self._current_metrics.snapshots:
            current_memory = self._current_metrics.snapshots[-1].memory_used_mb
            phase_data["end_memory_mb"] = current_memory
            phase_data["memory_delta_mb"] = current_memory - phase_data.get("start_memory_mb", 0)
        
        logger.debug(f"Completed processing phase: {phase_name} ({phase_data['duration']:.2f}s)")
    
    def get_processing_recommendations(self) -> List[str]:
        """Get recommendations based on current resource usage patterns."""
        if not self._current_metrics or not self._current_metrics.snapshots:
            return []
        
        recommendations = []
        
        # Memory-based recommendations
        if self._current_metrics.peak_memory_mb > 6000:  # 6GB
            recommendations.append("Consider processing smaller images or fewer regions at once")
        
        if self._current_metrics.memory_growth_mb > 1000:  # 1GB growth
            recommendations.append("Significant memory growth detected - may indicate memory leaks")
        
        # CPU-based recommendations
        if self._current_metrics.avg_cpu_percent > 90:
            recommendations.append("High CPU usage - consider reducing concurrent processing")
        
        # Efficiency-based recommendations
        if self._current_metrics.memory_efficiency_score < 50:
            recommendations.append("Low memory efficiency - consider optimizing processing parameters")
        
        # Duration-based recommendations
        if self._current_metrics.duration_seconds > 300:  # 5 minutes
            recommendations.append("Long processing time - consider breaking into smaller tasks")
        
        return recommendations


# Global resource monitor instance
resource_monitor = RealTimeResourceMonitor()