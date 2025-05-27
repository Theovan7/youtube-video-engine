"""
Metrics collection utility for YouTube Video Engine.

This module provides comprehensive metrics collection for monitoring
application performance, usage patterns, and system health.
"""

import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates application metrics."""
    
    def __init__(self, retention_hours: int = 24):
        """Initialize metrics collector.
        
        Args:
            retention_hours: How long to keep detailed metrics data
        """
        self.retention_hours = retention_hours
        self.lock = threading.Lock()
        
        # Request metrics
        self.requests_total = 0
        self.requests_success = 0
        self.requests_error = 0
        self.response_times = deque(maxlen=10000)  # Keep last 10k response times
        
        # Job metrics
        self.jobs_active = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        
        # Service health metrics
        self.service_status = {
            'airtable': {'status': 'unknown', 'last_check': None},
            'elevenlabs': {'status': 'unknown', 'last_check': None},
            'nca_toolkit': {'status': 'unknown', 'last_check': None},
            'goapi': {'status': 'unknown', 'last_check': None}
        }
        
        # Endpoint-specific metrics
        self.endpoint_metrics = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'error_count': 0,
            'response_times': deque(maxlen=1000),
            'last_accessed': None
        })
        
        # Time-series data for trends
        self.hourly_metrics = deque(maxlen=retention_hours)
        
        # Error tracking
        self.error_details = deque(maxlen=1000)
        
        # Performance alerts
        self.alert_thresholds = {
            'response_time_p95': 10.0,  # seconds
            'error_rate': 0.05,  # 5%
            'service_health': 0.8  # 80% services healthy
        }
        
        # Initialize first hourly metric
        self._initialize_hourly_metrics()
        
        logger.info("MetricsCollector initialized")
    
    def _initialize_hourly_metrics(self):
        """Initialize hourly metrics structure."""
        now = datetime.now()
        hourly_metric = {
            'timestamp': now,
            'requests': {'total': 0, 'success': 0, 'error': 0},
            'response_times': [],
            'jobs': {'active': 0, 'completed': 0, 'failed': 0},
            'services_healthy': 0,
            'errors': []
        }
        self.hourly_metrics.append(hourly_metric)
    
    def record_request(self, success: bool = True, response_time: Optional[float] = None, 
                      endpoint: Optional[str] = None):
        """Record request metrics.
        
        Args:
            success: Whether the request was successful
            response_time: Request processing time in seconds
            endpoint: API endpoint that was called
        """
        with self.lock:
            self.requests_total += 1
            
            if success:
                self.requests_success += 1
            else:
                self.requests_error += 1
            
            if response_time is not None:
                self.response_times.append(response_time)
            
            # Record endpoint-specific metrics
            if endpoint:
                endpoint_data = self.endpoint_metrics[endpoint]
                endpoint_data['count'] += 1
                endpoint_data['last_accessed'] = datetime.now()
                
                if success:
                    endpoint_data['success_count'] += 1
                else:
                    endpoint_data['error_count'] += 1
                
                if response_time is not None:
                    endpoint_data['response_times'].append(response_time)
            
            # Update current hourly metrics
            if self.hourly_metrics:
                current_hour = self.hourly_metrics[-1]
                current_hour['requests']['total'] += 1
                
                if success:
                    current_hour['requests']['success'] += 1
                else:
                    current_hour['requests']['error'] += 1
                
                if response_time is not None:
                    current_hour['response_times'].append(response_time)
    
    def record_job_event(self, event_type: str, job_id: str = None, 
                        job_type: str = None, details: Dict = None):
        """Record job-related events.
        
        Args:
            event_type: 'started', 'completed', 'failed'
            job_id: Unique job identifier
            job_type: Type of job (voiceover, combine, etc.)
            details: Additional job details
        """
        with self.lock:
            if event_type == 'started':
                self.jobs_active += 1
            elif event_type == 'completed':
                self.jobs_active = max(0, self.jobs_active - 1)
                self.jobs_completed += 1
            elif event_type == 'failed':
                self.jobs_active = max(0, self.jobs_active - 1)
                self.jobs_failed += 1
            
            # Update current hourly metrics
            if self.hourly_metrics:
                current_hour = self.hourly_metrics[-1]
                
                if event_type in current_hour['jobs']:
                    current_hour['jobs'][event_type] += 1
                
                current_hour['jobs']['active'] = self.jobs_active
    
    def record_service_health(self, service: str, healthy: bool, details: str = None):
        """Record service health status.
        
        Args:
            service: Service name (airtable, elevenlabs, etc.)
            healthy: Whether the service is healthy
            details: Additional health details
        """
        with self.lock:
            if service in self.service_status:
                self.service_status[service].update({
                    'status': 'healthy' if healthy else 'unhealthy',
                    'last_check': datetime.now(),
                    'details': details
                })
            
            # Update services healthy count
            healthy_count = sum(
                1 for status in self.service_status.values()
                if status['status'] == 'healthy'
            )
            
            if self.hourly_metrics:
                self.hourly_metrics[-1]['services_healthy'] = healthy_count
    
    def record_error(self, error_type: str, message: str, context: Dict = None):
        """Record error details for analysis.
        
        Args:
            error_type: Type of error (api_error, service_error, etc.)
            message: Error message
            context: Additional error context
        """
        with self.lock:
            error_record = {
                'timestamp': datetime.now(),
                'type': error_type,
                'message': message,
                'context': context or {}
            }
            
            self.error_details.append(error_record)
            
            # Add to current hourly metrics
            if self.hourly_metrics:
                self.hourly_metrics[-1]['errors'].append(error_record)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary.
        
        Returns:
            Dictionary containing all metrics
        """
        with self.lock:
            response_times_list = list(self.response_times)
            
            # Calculate percentiles
            def percentile(data, p):
                if not data:
                    return 0
                sorted_data = sorted(data)
                k = (len(sorted_data) - 1) * p
                f = int(k)
                c = k - f
                if f + 1 < len(sorted_data):
                    return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
                else:
                    return sorted_data[f]
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'requests': {
                    'total': self.requests_total,
                    'success': self.requests_success,
                    'error': self.requests_error,
                    'error_rate': (
                        self.requests_error / max(self.requests_total, 1)
                    ),
                    'success_rate': (
                        self.requests_success / max(self.requests_total, 1)
                    )
                },
                'performance': {
                    'avg_response_time': (
                        sum(response_times_list) / len(response_times_list)
                        if response_times_list else 0
                    ),
                    'min_response_time': min(response_times_list) if response_times_list else 0,
                    'max_response_time': max(response_times_list) if response_times_list else 0,
                    'p50_response_time': percentile(response_times_list, 0.5),
                    'p95_response_time': percentile(response_times_list, 0.95),
                    'p99_response_time': percentile(response_times_list, 0.99)
                },
                'jobs': {
                    'active': self.jobs_active,
                    'completed': self.jobs_completed,
                    'failed': self.jobs_failed,
                    'total_processed': self.jobs_completed + self.jobs_failed,
                    'failure_rate': (
                        self.jobs_failed / max(self.jobs_completed + self.jobs_failed, 1)
                    )
                },
                'services': {
                    service: {
                        'status': data['status'],
                        'last_check': data['last_check'].isoformat() if data['last_check'] else None
                    }
                    for service, data in self.service_status.items()
                },
                'health_indicators': self._get_health_indicators(),
                'alerts': self._check_alerts()
            }
            
            return summary
    
    def get_endpoint_metrics(self) -> Dict[str, Any]:
        """Get detailed endpoint-specific metrics.
        
        Returns:
            Dictionary containing endpoint metrics
        """
        with self.lock:
            endpoint_data = {}
            
            for endpoint, metrics in self.endpoint_metrics.items():
                response_times = list(metrics['response_times'])
                
                endpoint_data[endpoint] = {
                    'total_requests': metrics['count'],
                    'success_requests': metrics['success_count'],
                    'error_requests': metrics['error_count'],
                    'error_rate': (
                        metrics['error_count'] / max(metrics['count'], 1)
                    ),
                    'avg_response_time': (
                        sum(response_times) / len(response_times) if response_times else 0
                    ),
                    'last_accessed': (
                        metrics['last_accessed'].isoformat() 
                        if metrics['last_accessed'] else None
                    )
                }
            
            return endpoint_data
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error analysis summary.
        
        Returns:
            Dictionary containing error analysis
        """
        with self.lock:
            errors = list(self.error_details)
            
            # Group errors by type
            error_counts = defaultdict(int)
            recent_errors = []
            
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            for error in errors:
                error_counts[error['type']] += 1
                
                if error['timestamp'] >= cutoff_time:
                    recent_errors.append({
                        'timestamp': error['timestamp'].isoformat(),
                        'type': error['type'],
                        'message': error['message']
                    })
            
            return {
                'total_errors': len(errors),
                'error_types': dict(error_counts),
                'recent_errors': recent_errors[-10:],  # Last 10 errors
                'error_rate_last_hour': len(recent_errors)
            }
    
    def _get_health_indicators(self) -> Dict[str, Any]:
        """Calculate health indicators.
        
        Returns:
            Dictionary containing health scores
        """
        # Service health score
        healthy_services = sum(
            1 for status in self.service_status.values()
            if status['status'] == 'healthy'
        )
        total_services = len(self.service_status)
        service_health_score = healthy_services / max(total_services, 1)
        
        # Performance health score
        response_times = list(self.response_times)
        if response_times:
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            performance_score = min(1.0, self.alert_thresholds['response_time_p95'] / max(p95_response_time, 0.1))
        else:
            performance_score = 1.0
        
        # Error rate health score
        error_rate = self.requests_error / max(self.requests_total, 1)
        error_score = max(0.0, 1.0 - (error_rate / self.alert_thresholds['error_rate']))
        
        # Overall health score
        overall_score = (service_health_score + performance_score + error_score) / 3
        
        return {
            'overall_health': overall_score,
            'service_health': service_health_score,
            'performance_health': performance_score,
            'error_rate_health': error_score,
            'status': self._health_status_from_score(overall_score)
        }
    
    def _health_status_from_score(self, score: float) -> str:
        """Convert health score to status string."""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.5:
            return 'fair'
        elif score >= 0.3:
            return 'poor'
        else:
            return 'critical'
    
    def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions.
        
        Returns:
            List of active alerts
        """
        alerts = []
        
        # Check response time alert
        response_times = list(self.response_times)
        if response_times:
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
            if p95_time > self.alert_thresholds['response_time_p95']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f'95th percentile response time ({p95_time:.2f}s) exceeds threshold ({self.alert_thresholds["response_time_p95"]}s)',
                    'metric': 'response_time_p95',
                    'current_value': p95_time,
                    'threshold': self.alert_thresholds['response_time_p95']
                })
        
        # Check error rate alert
        error_rate = self.requests_error / max(self.requests_total, 1)
        if error_rate > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'reliability',
                'severity': 'warning',
                'message': f'Error rate ({error_rate:.1%}) exceeds threshold ({self.alert_thresholds["error_rate"]:.1%})',
                'metric': 'error_rate',
                'current_value': error_rate,
                'threshold': self.alert_thresholds['error_rate']
            })
        
        # Check service health alert
        healthy_services = sum(
            1 for status in self.service_status.values()
            if status['status'] == 'healthy'
        )
        service_health_ratio = healthy_services / max(len(self.service_status), 1)
        
        if service_health_ratio < self.alert_thresholds['service_health']:
            alerts.append({
                'type': 'service_health',
                'severity': 'critical',
                'message': f'Service health ({service_health_ratio:.1%}) below threshold ({self.alert_thresholds["service_health"]:.1%})',
                'metric': 'service_health',
                'current_value': service_health_ratio,
                'threshold': self.alert_thresholds['service_health']
            })
        
        return alerts
    
    def reset_metrics(self):
        """Reset all metrics (use with caution)."""
        with self.lock:
            self.requests_total = 0
            self.requests_success = 0
            self.requests_error = 0
            self.response_times.clear()
            self.jobs_active = 0
            self.jobs_completed = 0
            self.jobs_failed = 0
            self.endpoint_metrics.clear()
            self.error_details.clear()
            
            logger.info("All metrics have been reset")
    
    def cleanup_old_data(self):
        """Clean up old metrics data beyond retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self.lock:
            # Clean up hourly metrics
            while self.hourly_metrics and self.hourly_metrics[0]['timestamp'] < cutoff_time:
                self.hourly_metrics.popleft()
            
            # Clean up error details
            self.error_details = deque(
                [error for error in self.error_details if error['timestamp'] >= cutoff_time],
                maxlen=1000
            )
            
            logger.debug(f"Cleaned up metrics data older than {self.retention_hours} hours")
