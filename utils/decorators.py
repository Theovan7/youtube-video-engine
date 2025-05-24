"""Decorators for error handling and retry logic."""

import time
import logging
from functools import wraps
from typing import Tuple, Type, Callable, Optional, Union

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 1.5,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_delay: float = 60.0
) -> Callable:
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Factor to multiply delay by after each attempt
        exceptions: Tuple of exceptions to catch and retry
        max_delay: Maximum delay between retries in seconds
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = 1.0
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__} - {str(e)}"
                        )
                        raise
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)
                    
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.1f}s due to: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            return None  # Should never reach here
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for handling failing services.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """
    
    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type to monitor
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator implementation."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if circuit should be reset
            if self.state == self.OPEN:
                if self.last_failure_time and \
                   time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info(f"Circuit breaker moving to HALF_OPEN for {func.__name__}")
                    self.state = self.HALF_OPEN
                    self.failure_count = 0
                else:
                    raise Exception(
                        f"Circuit breaker is OPEN for {func.__name__}. "
                        f"Service unavailable."
                    )
            
            try:
                result = func(*args, **kwargs)
                
                # Reset on success
                if self.state == self.HALF_OPEN:
                    logger.info(f"Circuit breaker closing for {func.__name__}")
                    self.state = self.CLOSED
                    self.failure_count = 0
                
                return result
                
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    logger.error(
                        f"Circuit breaker opening for {func.__name__} "
                        f"after {self.failure_count} failures"
                    )
                    self.state = self.OPEN
                
                raise
        
        return wrapper


def rate_limit(calls: int = 10, period: float = 60.0) -> Callable:
    """
    Simple rate limiting decorator.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        call_times = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove old calls outside the period
            call_times[:] = [t for t in call_times if now - t < period]
            
            if len(call_times) >= calls:
                sleep_time = period - (now - call_times[0])
                if sleep_time > 0:
                    logger.warning(
                        f"Rate limit reached for {func.__name__}. "
                        f"Sleeping for {sleep_time:.1f}s"
                    )
                    time.sleep(sleep_time)
                    # Remove the oldest call
                    call_times.pop(0)
            
            call_times.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def timeout(seconds: float) -> Callable:
    """
    Timeout decorator using threading.
    
    Args:
        seconds: Timeout in seconds
    
    Returns:
        Decorated function
    """
    import threading
    import queue
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def target():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                raise TimeoutError(
                    f"{func.__name__} timed out after {seconds} seconds"
                )
            
            if not exception_queue.empty():
                raise exception_queue.get()
            
            return result_queue.get()
        
        return wrapper
    return decorator


def log_errors(logger_instance: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to log exceptions with full context.
    
    Args:
        logger_instance: Logger to use (defaults to module logger)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger_instance or logger
                log.error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'args': str(args)[:200],  # Truncate for safety
                        'kwargs': str(kwargs)[:200]
                    }
                )
                raise
        
        return wrapper
    return decorator
