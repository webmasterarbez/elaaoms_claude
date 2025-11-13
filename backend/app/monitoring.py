"""
Performance monitoring and alerting for ELAAOMS.
"""

import logging
import time
from typing import Dict, Any, List
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance metrics."""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Number of recent requests to track
        """
        self.window_size = window_size
        self.latencies: deque = deque(maxlen=window_size)
        self.error_count = 0
        self.request_count = 0
        self.degradation_threshold_p95 = 5.0  # 5 seconds for p95
        self.degradation_threshold_p99 = 10.0  # 10 seconds for p99
    
    def record_request(self, latency: float, success: bool = True):
        """
        Record a request's latency and status.
        
        Args:
            latency: Request latency in seconds
            success: Whether request succeeded
        """
        self.latencies.append(latency)
        self.request_count += 1
        if not success:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary with p50, p95, p99 latencies and error rate
        """
        if not self.latencies:
            return {
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "error_rate": 0.0,
                "request_count": 0
            }
        
        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)
        
        p50 = sorted_latencies[int(n * 0.50)]
        p95 = sorted_latencies[int(n * 0.95)]
        p99 = sorted_latencies[int(n * 0.99)]
        
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0.0
        
        return {
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "p99": round(p99, 3),
            "error_rate": round(error_rate, 4),
            "request_count": self.request_count,
            "error_count": self.error_count
        }
    
    def check_degradation(self) -> List[str]:
        """
        Check for performance degradation.
        
        Returns:
            List of degradation warnings
        """
        warnings = []
        metrics = self.get_metrics()
        
        if metrics["p95"] > self.degradation_threshold_p95:
            warnings.append(
                f"P95 latency ({metrics['p95']}s) exceeds threshold "
                f"({self.degradation_threshold_p95}s)"
            )
        
        if metrics["p99"] > self.degradation_threshold_p99:
            warnings.append(
                f"P99 latency ({metrics['p99']}s) exceeds threshold "
                f"({self.degradation_threshold_p99}s)"
            )
        
        if metrics["error_rate"] > 0.05:  # 5% error rate
            warnings.append(
                f"Error rate ({metrics['error_rate']*100:.1f}%) exceeds threshold (5%)"
            )
        
        return warnings


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

