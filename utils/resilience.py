"""
Comprehensive retry/backoff framework for resilient external operations.

This module provides decorators and utilities for implementing retry logic with exponential backoff,
circuit breakers, and other resilience patterns for HTTP requests, database operations,
file operations, and subprocess calls.
"""

import asyncio
import functools
import json
import logging
import random
import sqlite3
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import requests

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Different retry strategies available."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    JITTERED_EXPONENTIAL = "jittered_exponential"


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    exceptions: tuple[type[Exception], ...] = (Exception,)
    on_retry: Callable | None = None
    on_failure: Callable | None = None
    on_success: Callable | None = None


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type[Exception] = Exception
    name: str = "default"


@dataclass
class RetryResult:
    """Result of a retry operation."""

    success: bool
    attempts: int
    total_time: float
    last_exception: Exception | None = None
    circuit_state: CircuitState | None = None


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.state != CircuitState.OPEN:
            return False
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(
            seconds=self.config.recovery_timeout
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.config.name}' is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.config.name}' opened after {self.failure_count} failures"
            )


class RetryManager:
    """Manages retry operations with different strategies."""

    def __init__(self, config: RetryConfig):
        self.config = config

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt based on strategy."""
        if self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.JITTERED_EXPONENTIAL:
            base_delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
            delay = base_delay * (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        else:
            delay = self.config.base_delay

        # Apply jitter if enabled
        if self.config.jitter and self.config.strategy != RetryStrategy.JITTERED_EXPONENTIAL:
            delay *= 0.8 + random.random() * 0.4  # 80-120% of calculated delay

        return min(delay, self.config.max_delay)

    def execute(self, func: Callable, *args, **kwargs) -> RetryResult:
        """Execute function with retry logic."""
        start_time = time.time()
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                func(*args, **kwargs)

                if self.config.on_success:
                    self.config.on_success(attempt, time.time() - start_time)

                return RetryResult(
                    success=True, attempts=attempt, total_time=time.time() - start_time
                )

            except self.config.exceptions as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{self.config.max_attempts} failed: {e}")

                if self.config.on_retry:
                    self.config.on_retry(attempt, e)

                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)

        if self.config.on_failure:
            self.config.on_failure(self.config.max_attempts, last_exception)

        return RetryResult(
            success=False,
            attempts=self.config.max_attempts,
            total_time=time.time() - start_time,
            last_exception=last_exception,
        )


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig(name=name)
        _circuit_breakers[name] = CircuitBreaker(config)
    return _circuit_breakers[name]


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    circuit_breaker: str | None = None,
    on_retry: Callable | None = None,
    on_failure: Callable | None = None,
    on_success: Callable | None = None,
):
    """Decorator for adding retry logic with exponential backoff."""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                strategy=strategy,
                exceptions=exceptions,
                on_retry=on_retry,
                on_failure=on_failure,
                on_success=on_success,
            )

            retry_manager = RetryManager(config)

            if circuit_breaker:
                cb = get_circuit_breaker(circuit_breaker)
                result = retry_manager.execute(cb.call, func, *args, **kwargs)
            else:
                result = retry_manager.execute(func, *args, **kwargs)

            if not result.success:
                raise result.last_exception

            return result

        return wrapper

    return decorator


# Specialized decorators for common operations
def retry_http_request(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    circuit_breaker: str = "http_requests",
):
    """Decorator specifically for HTTP requests."""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=RetryStrategy.JITTERED_EXPONENTIAL,
        exceptions=(requests.RequestException, requests.Timeout, requests.ConnectionError),
        circuit_breaker=circuit_breaker,
    )


def retry_database_operation(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    circuit_breaker: str = "database",
):
    """Decorator specifically for database operations."""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=(sqlite3.Error, sqlite3.OperationalError, sqlite3.DatabaseError),
        circuit_breaker=circuit_breaker,
    )


def retry_file_operation(max_attempts: int = 3, base_delay: float = 0.1, max_delay: float = 5.0):
    """Decorator specifically for file operations."""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        exceptions=(IOError, OSError, FileNotFoundError, PermissionError),
    )


def retry_subprocess(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 15.0):
    """Decorator specifically for subprocess operations."""
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        exceptions=(subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError),
    )


# Async versions for async operations
async def async_retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    *args,
    **kwargs,
) -> RetryResult:
    """Async version of retry with backoff."""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=strategy,
        exceptions=exceptions,
    )

    retry_manager = RetryManager(config)
    start_time = time.time()
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)

            return RetryResult(success=True, attempts=attempt, total_time=time.time() - start_time)

        except exceptions as e:
            last_exception = e
            logger.warning(f"Async attempt {attempt}/{max_attempts} failed: {e}")

            if attempt < max_attempts:
                delay = retry_manager._calculate_delay(attempt)
                logger.info(f"Async retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

    return RetryResult(
        success=False,
        attempts=max_attempts,
        total_time=time.time() - start_time,
        last_exception=last_exception,
    )


# Utility functions for common resilience patterns
class ResilienceMetrics:
    """Collect and track resilience metrics."""

    def __init__(self):
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "retry_operations": 0,
            "circuit_breaker_trips": 0,
            "average_retry_attempts": 0.0,
            "total_retry_time": 0.0,
        }
        self.operation_history: list[dict] = []

    def record_operation(self, result: RetryResult, operation_type: str = "unknown"):
        """Record the result of an operation."""
        self.metrics["total_operations"] += 1

        if result.success:
            self.metrics["successful_operations"] += 1
        else:
            self.metrics["failed_operations"] += 1

        if result.attempts > 1:
            self.metrics["retry_operations"] += 1

        # Update averages
        total_ops = self.metrics["total_operations"]
        self.metrics["average_retry_attempts"] = (
            self.metrics["average_retry_attempts"] * (total_ops - 1) + result.attempts
        ) / total_ops

        self.metrics["total_retry_time"] += result.total_time

        # Store operation history
        self.operation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "operation_type": operation_type,
                "success": result.success,
                "attempts": result.attempts,
                "total_time": result.total_time,
                "exception": str(result.last_exception) if result.last_exception else None,
            }
        )

        # Keep only last 1000 operations
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-1000:]

    def get_metrics(self) -> dict:
        """Get current metrics."""
        return self.metrics.copy()

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.metrics["total_operations"] == 0:
            return 0.0
        return (self.metrics["successful_operations"] / self.metrics["total_operations"]) * 100

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        metrics_data = {
            "metrics": self.metrics,
            "success_rate": self.get_success_rate(),
            "operation_history": self.operation_history[-100:],  # Last 100 operations
        }

        with open(filepath, "w") as f:
            json.dump(metrics_data, f, indent=2)


# Global metrics instance
resilience_metrics = ResilienceMetrics()


def with_metrics(operation_type: str = "unknown"):
    """Decorator to automatically track metrics for operations."""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # If the function returns a RetryResult, use it
                if isinstance(result, RetryResult):
                    resilience_metrics.record_operation(result, operation_type)
                else:
                    # Create a synthetic RetryResult for successful operation
                    synthetic_result = RetryResult(
                        success=True, attempts=1, total_time=time.time() - start_time
                    )
                    resilience_metrics.record_operation(synthetic_result, operation_type)

                return result

            except Exception as e:
                # Create a synthetic RetryResult for failed operation
                synthetic_result = RetryResult(
                    success=False, attempts=1, total_time=time.time() - start_time, last_exception=e
                )
                resilience_metrics.record_operation(synthetic_result, operation_type)
                raise

        return wrapper

    return decorator


# Configuration management
class ResilienceConfig:
    """Global configuration for resilience patterns."""

    def __init__(self):
        self.configs = {
            "http_requests": RetryConfig(
                max_attempts=3, base_delay=1.0, strategy=RetryStrategy.JITTERED_EXPONENTIAL
            ),
            "database": RetryConfig(
                max_attempts=3, base_delay=0.5, strategy=RetryStrategy.EXPONENTIAL_BACKOFF
            ),
            "file_operations": RetryConfig(
                max_attempts=3, base_delay=0.1, strategy=RetryStrategy.LINEAR_BACKOFF
            ),
            "subprocess": RetryConfig(
                max_attempts=3, base_delay=1.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF
            ),
        }

        self.circuit_breaker_configs = {
            "http_requests": CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0),
            "database": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0),
            "external_apis": CircuitBreakerConfig(failure_threshold=10, recovery_timeout=120.0),
        }

    def get_retry_config(self, operation_type: str) -> RetryConfig:
        """Get retry configuration for operation type."""
        return self.configs.get(operation_type, RetryConfig())

    def get_circuit_breaker_config(self, operation_type: str) -> CircuitBreakerConfig:
        """Get circuit breaker configuration for operation type."""
        return self.circuit_breaker_configs.get(operation_type, CircuitBreakerConfig())

    def update_config(self, operation_type: str, config: RetryConfig):
        """Update configuration for operation type."""
        self.configs[operation_type] = config

    def load_from_file(self, filepath: str):
        """Load configuration from JSON file."""
        try:
            with open(filepath) as f:
                data = json.load(f)

            for op_type, config_data in data.get("retry_configs", {}).items():
                config = RetryConfig(**config_data)
                self.configs[op_type] = config

            for op_type, cb_config_data in data.get("circuit_breaker_configs", {}).items():
                cb_config = CircuitBreakerConfig(**cb_config_data)
                self.circuit_breaker_configs[op_type] = cb_config

        except Exception as e:
            logger.error(f"Failed to load resilience config from {filepath}: {e}")

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        try:
            data = {
                "retry_configs": {
                    op_type: {
                        "max_attempts": config.max_attempts,
                        "base_delay": config.base_delay,
                        "max_delay": config.max_delay,
                        "exponential_base": config.exponential_base,
                        "strategy": config.strategy.value,
                    }
                    for op_type, config in self.configs.items()
                },
                "circuit_breaker_configs": {
                    op_type: {
                        "failure_threshold": config.failure_threshold,
                        "recovery_timeout": config.recovery_timeout,
                        "name": config.name,
                    }
                    for op_type, config in self.circuit_breaker_configs.items()
                },
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save resilience config to {filepath}: {e}")


# Global configuration instance
resilience_config = ResilienceConfig()


# Health check and monitoring utilities
def health_check_with_circuit_breaker(name: str, health_func: Callable) -> bool:
    """Perform health check with circuit breaker protection."""
    try:
        cb = get_circuit_breaker(name)
        cb.call(health_func)
        return True
    except CircuitBreakerOpenError:
        logger.warning(f"Health check skipped - circuit breaker '{name}' is open")
        return False
    except Exception as e:
        logger.error(f"Health check failed for '{name}': {e}")
        return False


def get_resilience_status() -> dict:
    """Get overall resilience status and metrics."""
    status = {
        "metrics": resilience_metrics.get_metrics(),
        "success_rate": resilience_metrics.get_success_rate(),
        "circuit_breakers": {},
    }

    for name, cb in _circuit_breakers.items():
        status["circuit_breakers"][name] = {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
            "last_failure_time": cb.last_failure_time.isoformat() if cb.last_failure_time else None,
        }

    return status
