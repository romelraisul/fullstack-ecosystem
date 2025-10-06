"""
Comprehensive tests for the resilience framework.
Tests retry/backoff functionality, circuit breakers, and edge cases.
"""

import contextlib
import sqlite3
import subprocess
import time
from unittest.mock import Mock, patch

import pytest
import requests

from utils.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    ResilienceMetrics,
    RetryConfig,
    RetryManager,
    RetryStrategy,
    async_retry_with_backoff,
    get_circuit_breaker,
    health_check_with_circuit_breaker,
    retry_database_operation,
    retry_file_operation,
    retry_http_request,
    retry_subprocess,
    retry_with_backoff,
)


class TestRetryConfig:
    """Test RetryConfig functionality."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_custom_config(self):
        """Test custom configuration."""
        config = RetryConfig(max_attempts=5, base_delay=2.0, strategy=RetryStrategy.LINEAR_BACKOFF)
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.strategy == RetryStrategy.LINEAR_BACKOFF


class TestRetryManager:
    """Test RetryManager functionality."""

    def test_exponential_backoff_delay(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=False,
        )
        manager = RetryManager(config)

        assert manager._calculate_delay(1) == 1.0
        assert manager._calculate_delay(2) == 2.0
        assert manager._calculate_delay(3) == 4.0
        assert manager._calculate_delay(4) == 8.0

    def test_linear_backoff_delay(self):
        """Test linear backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, strategy=RetryStrategy.LINEAR_BACKOFF, jitter=False)
        manager = RetryManager(config)

        assert manager._calculate_delay(1) == 1.0
        assert manager._calculate_delay(2) == 2.0
        assert manager._calculate_delay(3) == 3.0
        assert manager._calculate_delay(4) == 4.0

    def test_fixed_delay(self):
        """Test fixed delay calculation."""
        config = RetryConfig(base_delay=2.0, strategy=RetryStrategy.FIXED_DELAY, jitter=False)
        manager = RetryManager(config)

        assert manager._calculate_delay(1) == 2.0
        assert manager._calculate_delay(2) == 2.0
        assert manager._calculate_delay(3) == 2.0

    def test_max_delay_limit(self):
        """Test max delay limit is respected."""
        config = RetryConfig(
            base_delay=1.0, max_delay=5.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF, jitter=False
        )
        manager = RetryManager(config)

        assert manager._calculate_delay(10) == 5.0  # Should be capped at max_delay

    def test_successful_execution(self):
        """Test successful function execution."""
        config = RetryConfig(max_attempts=3)
        manager = RetryManager(config)

        def success_func():
            return "success"

        result = manager.execute(success_func)
        assert result.success is True
        assert result.attempts == 1
        assert result.last_exception is None

    def test_retry_on_failure(self):
        """Test retry logic on failure."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)  # Fast test
        manager = RetryManager(config)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"

        result = manager.execute(failing_func)
        assert result.success is True
        assert result.attempts == 3
        assert call_count == 3

    def test_max_attempts_exceeded(self):
        """Test behavior when max attempts exceeded."""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        manager = RetryManager(config)

        def always_failing():
            raise ValueError("Always fails")

        result = manager.execute(always_failing)
        assert result.success is False
        assert result.attempts == 2
        assert isinstance(result.last_exception, ValueError)

    def test_callback_functions(self):
        """Test callback functions are called."""
        on_retry_calls = []
        on_failure_calls = []
        on_success_calls = []

        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            on_retry=lambda attempt, exc: on_retry_calls.append((attempt, exc)),
            on_failure=lambda attempts, exc: on_failure_calls.append((attempts, exc)),
            on_success=lambda attempts, time: on_success_calls.append((attempts, time)),
        )
        manager = RetryManager(config)

        call_count = 0

        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Test error")
            return "success"

        result = manager.execute(failing_then_success)

        assert result.success is True
        assert len(on_retry_calls) == 1
        assert len(on_success_calls) == 1
        assert len(on_failure_calls) == 0


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""

    def test_closed_state_initial(self):
        """Test circuit breaker starts in closed state."""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker(config)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_successful_calls(self):
        """Test successful calls keep circuit closed."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        def success_func():
            return "success"

        for _ in range(5):
            result = cb.call(success_func)
            assert result == "success"
            assert cb.state == CircuitState.CLOSED
            assert cb.failure_count == 0

    def test_circuit_opens_on_failures(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3, expected_exception=ValueError)
        cb = CircuitBreaker(config)

        def failing_func():
            raise ValueError("Test error")

        # First 2 failures - circuit stays closed
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)
            assert cb.state == CircuitState.CLOSED

        # Third failure - circuit opens
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError is raised when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1, expected_exception=ValueError)
        cb = CircuitBreaker(config)

        # Cause circuit to open
        with pytest.raises(ValueError):
            cb.call(lambda: exec('raise ValueError("Test")'))

        assert cb.state == CircuitState.OPEN

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

    def test_circuit_recovery(self):
        """Test circuit breaker recovery after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,  # Short timeout for testing
            expected_exception=ValueError,
        )
        cb = CircuitBreaker(config)

        # Cause circuit to open
        with pytest.raises(ValueError):
            cb.call(lambda: exec('raise ValueError("Test")'))
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Next successful call should close circuit
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestRetryDecorators:
    """Test retry decorators."""

    def test_retry_with_backoff_decorator(self):
        """Test basic retry decorator."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"

        result = failing_then_success()
        # The decorator returns the RetryResult, not the function result
        assert result.success is True
        assert call_count == 3

    def test_retry_http_request_decorator(self):
        """Test HTTP request retry decorator."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = [
                requests.ConnectionError("Connection failed"),
                requests.Timeout("Request timeout"),
                Mock(status_code=200, text="success"),
            ]

            @retry_http_request(max_attempts=3, base_delay=0.01)
            def make_request():
                return requests.get("http://example.com")

            # This should succeed after retries
            result = make_request()
            assert result.success is True
            assert mock_get.call_count == 3

    def test_retry_database_operation_decorator(self):
        """Test database operation retry decorator."""
        call_count = 0

        @retry_database_operation(max_attempts=3, base_delay=0.01)
        def db_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("Database is locked")
            return "success"

        result = db_operation()
        assert result.success is True
        assert call_count == 3

    def test_retry_file_operation_decorator(self):
        """Test file operation retry decorator."""
        call_count = 0

        @retry_file_operation(max_attempts=3, base_delay=0.01)
        def file_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise PermissionError("Permission denied")
            return "success"

        result = file_operation()
        assert result.success is True
        assert call_count == 3

    def test_retry_subprocess_decorator(self):
        """Test subprocess retry decorator."""
        call_count = 0

        @retry_subprocess(max_attempts=3, base_delay=0.01)
        def subprocess_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise subprocess.CalledProcessError(1, "test")
            return "success"

        result = subprocess_operation()
        assert result.success is True
        assert call_count == 3


class TestAsyncRetry:
    """Test async retry functionality."""

    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test async retry with successful execution."""

        async def success_func():
            return "async success"

        result = await async_retry_with_backoff(success_func, max_attempts=3)

        assert result.success is True
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_async_retry_with_failures(self):
        """Test async retry with failures then success."""
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Async test error")
            return "async success"

        result = await async_retry_with_backoff(
            failing_then_success, max_attempts=3, base_delay=0.01
        )

        assert result.success is True
        assert result.attempts == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_max_attempts(self):
        """Test async retry when max attempts exceeded."""

        async def always_failing():
            raise ValueError("Always fails")

        result = await async_retry_with_backoff(always_failing, max_attempts=2, base_delay=0.01)

        assert result.success is False
        assert result.attempts == 2
        assert isinstance(result.last_exception, ValueError)


class TestResilienceMetrics:
    """Test resilience metrics functionality."""

    def test_metrics_initialization(self):
        """Test metrics are initialized correctly."""
        metrics = ResilienceMetrics()
        assert metrics.metrics["total_operations"] == 0
        assert metrics.metrics["successful_operations"] == 0
        assert metrics.metrics["failed_operations"] == 0
        assert metrics.get_success_rate() == 0.0

    def test_record_successful_operation(self):
        """Test recording successful operations."""
        metrics = ResilienceMetrics()
        from utils.resilience import RetryResult

        result = RetryResult(success=True, attempts=1, total_time=0.5)
        metrics.record_operation(result, "test_op")

        assert metrics.metrics["total_operations"] == 1
        assert metrics.metrics["successful_operations"] == 1
        assert metrics.metrics["failed_operations"] == 0
        assert metrics.get_success_rate() == 100.0

    def test_record_failed_operation(self):
        """Test recording failed operations."""
        metrics = ResilienceMetrics()
        from utils.resilience import RetryResult

        result = RetryResult(
            success=False, attempts=3, total_time=1.5, last_exception=ValueError("Test error")
        )
        metrics.record_operation(result, "test_op")

        assert metrics.metrics["total_operations"] == 1
        assert metrics.metrics["successful_operations"] == 0
        assert metrics.metrics["failed_operations"] == 1
        assert metrics.get_success_rate() == 0.0

    def test_metrics_with_retries(self):
        """Test metrics tracking with retry operations."""
        metrics = ResilienceMetrics()
        from utils.resilience import RetryResult

        # Operation that succeeded after retries
        result = RetryResult(success=True, attempts=3, total_time=2.0)
        metrics.record_operation(result, "retry_op")

        assert metrics.metrics["retry_operations"] == 1
        assert metrics.metrics["average_retry_attempts"] == 3.0


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple resilience patterns."""

    def test_http_with_circuit_breaker(self):
        """Test HTTP requests with circuit breaker protection."""
        with patch("requests.get") as mock_get:
            # First few calls fail, then circuit breaker should open
            mock_get.side_effect = requests.ConnectionError("Connection failed")

            @retry_http_request(max_attempts=2, base_delay=0.01, circuit_breaker="test_http")
            def make_request():
                return requests.get("http://example.com")

            # First few attempts should fail and eventually open circuit
            for _ in range(6):  # Exceed failure threshold
                with contextlib.suppress(requests.ConnectionError, CircuitBreakerOpenError):
                    make_request()

            # Circuit should be open now
            cb = get_circuit_breaker("test_http")
            assert cb.state == CircuitState.OPEN

    def test_database_resilience_pattern(self):
        """Test database operations with full resilience pattern."""
        call_count = 0

        @retry_database_operation(max_attempts=3, base_delay=0.01)
        def db_query():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("Database is busy")
            return [{"id": 1, "name": "test"}]

        result = db_query()
        assert result.success is True
        assert call_count == 3

    def test_health_check_with_circuit_breaker(self):
        """Test health check functionality with circuit breaker."""

        def failing_health_check():
            raise Exception("Service unhealthy")

        def successful_health_check():
            return True

        # Health check should fail and eventually open circuit
        for _ in range(6):
            health_check_with_circuit_breaker("test_service", failing_health_check)

        cb = get_circuit_breaker("test_service")
        assert cb.state == CircuitState.OPEN

        # Health check should be skipped when circuit is open
        result = health_check_with_circuit_breaker("test_service", successful_health_check)
        assert result is False  # Skipped due to open circuit


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_max_attempts(self):
        """Test behavior with zero max attempts."""
        config = RetryConfig(max_attempts=0)
        manager = RetryManager(config)

        result = manager.execute(lambda: "success")
        assert result.success is False
        assert result.attempts == 0

    def test_negative_delays(self):
        """Test behavior with negative delays."""
        config = RetryConfig(base_delay=-1.0, jitter=False)
        manager = RetryManager(config)

        # Should handle negative delays gracefully
        delay = manager._calculate_delay(1)
        assert delay >= 0  # Should not be negative

    def test_very_large_delays(self):
        """Test behavior with very large delays."""
        config = RetryConfig(
            base_delay=1000.0,
            max_delay=5.0,  # Much smaller than base delay
            jitter=False,
        )
        manager = RetryManager(config)

        delay = manager._calculate_delay(1)
        assert delay == 5.0  # Should be capped at max_delay

    def test_jittered_exponential_strategy(self):
        """Test jittered exponential backoff strategy."""
        config = RetryConfig(base_delay=1.0, strategy=RetryStrategy.JITTERED_EXPONENTIAL)
        manager = RetryManager(config)

        # Test multiple times to check jitter variation
        delays = [manager._calculate_delay(2) for _ in range(10)]

        # All delays should be between 1.0 and 2.0 for attempt 2
        for delay in delays:
            assert 1.0 <= delay <= 2.0

        # Should have some variation due to jitter
        assert len(set(delays)) > 1


if __name__ == "__main__":
    # Run basic tests if executed directly
    pytest.main([__file__, "-v"])
