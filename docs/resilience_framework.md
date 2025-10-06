# Resilience Framework Documentation

## Overview

The Resilience Framework provides comprehensive retry/backoff logic, circuit breakers, and fault tolerance patterns for external operations in the fullstack ecosystem. This framework ensures robust operation when dealing with:

- HTTP requests and API calls
- Database operations
- File operations
- Subprocess calls
- Network-dependent operations

## Key Components

### 1. Retry Strategies

The framework supports multiple retry strategies:

- **Exponential Backoff**: Delays increase exponentially (1s, 2s, 4s, 8s...)
- **Linear Backoff**: Delays increase linearly (1s, 2s, 3s, 4s...)
- **Fixed Delay**: Constant delay between retries
- **Jittered Exponential**: Exponential backoff with randomization to prevent thundering herd

### 2. Circuit Breaker Pattern

Circuit breakers prevent cascading failures by:

- Monitoring failure rates
- Opening circuit after failure threshold
- Allowing recovery after timeout period
- Providing fail-fast behavior when services are down

### 3. Metrics and Monitoring

Built-in metrics collection for:

- Success/failure rates
- Retry attempt statistics
- Circuit breaker state changes
- Operation timing data

## Quick Start

### Basic Retry Decorator

```python
from utils.resilience import retry_with_backoff, RetryStrategy

@retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
)
def unreliable_operation():
    # Your operation here
    return api_call()
```

### HTTP Requests with Resilience

```python
from utils.resilience import retry_http_request

@retry_http_request(max_attempts=3, base_delay=1.0)
def fetch_data():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

### Database Operations

```python
from utils.resilience import retry_database_operation

@retry_database_operation(max_attempts=3, base_delay=0.5)
def get_user(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
```

### Async Operations

```python
from utils.resilience import async_retry_with_backoff

async def fetch_async_data():
    result = await async_retry_with_backoff(
        make_async_request,
        max_attempts=3,
        base_delay=1.0,
        exceptions=(httpx.RequestError, httpx.TimeoutException)
    )
    
    if not result.success:
        raise result.last_exception
    
    return await make_async_request()
```

## Configuration

### Retry Configuration

```python
from utils.resilience import RetryConfig, RetryStrategy

config = RetryConfig(
    max_attempts=5,           # Maximum retry attempts
    base_delay=1.0,          # Base delay in seconds
    max_delay=60.0,          # Maximum delay cap
    exponential_base=2.0,    # Exponential multiplier
    strategy=RetryStrategy.JITTERED_EXPONENTIAL,
    jitter=True,             # Add randomization
    exceptions=(Exception,)   # Exceptions to retry on
)
```

### Circuit Breaker Configuration

```python
from utils.resilience import CircuitBreakerConfig, get_circuit_breaker

config = CircuitBreakerConfig(
    failure_threshold=5,      # Failures before opening
    recovery_timeout=60.0,    # Seconds before attempting recovery
    name="external_api"       # Circuit breaker name
)

circuit_breaker = get_circuit_breaker("external_api", config)
```

## Advanced Usage

### Custom Callbacks

```python
def on_retry(attempt, exception):
    logger.warning(f"Retry attempt {attempt}: {exception}")

def on_failure(attempts, exception):
    logger.error(f"Operation failed after {attempts} attempts: {exception}")

def on_success(attempts, duration):
    logger.info(f"Operation succeeded after {attempts} attempts in {duration}s")

@retry_with_backoff(
    max_attempts=3,
    on_retry=on_retry,
    on_failure=on_failure,
    on_success=on_success
)
def monitored_operation():
    return risky_operation()
```

### Metrics Collection

```python
from utils.resilience import with_metrics, resilience_metrics

@with_metrics("user_api_calls")
@retry_http_request(max_attempts=3)
def get_user_data(user_id):
    return requests.get(f"/api/users/{user_id}")

# Get metrics
metrics = resilience_metrics.get_metrics()
success_rate = resilience_metrics.get_success_rate()

# Export metrics to file
resilience_metrics.export_metrics("resilience_metrics.json")
```

### Health Checks with Circuit Breakers

```python
from utils.resilience import health_check_with_circuit_breaker

def database_health_check():
    with get_db_connection() as conn:
        conn.execute("SELECT 1")
    return True

# Health check that respects circuit breaker state
is_healthy = health_check_with_circuit_breaker("database", database_health_check)
```

## Best Practices

### 1. Choose Appropriate Retry Strategies

- **HTTP APIs**: Use jittered exponential backoff to prevent thundering herd
- **Database operations**: Use exponential backoff with shorter delays
- **File operations**: Use linear backoff with minimal delays
- **Subprocess calls**: Use exponential backoff with moderate delays

### 2. Set Reasonable Timeouts

```python
# Good: Reasonable timeouts
@retry_http_request(max_attempts=3, base_delay=1.0, max_delay=30.0)

# Avoid: Too many attempts or too long delays
@retry_with_backoff(max_attempts=20, max_delay=300.0)  # Don't do this
```

### 3. Handle Specific Exceptions

```python
# Good: Specific exceptions
@retry_with_backoff(
    exceptions=(requests.ConnectionError, requests.Timeout)
)

# Avoid: Catching all exceptions
@retry_with_backoff(exceptions=(Exception,))  # Too broad
```

### 4. Use Circuit Breakers for External Dependencies

```python
@retry_http_request(circuit_breaker="payment_api")
def process_payment(amount):
    return payment_api.charge(amount)
```

### 5. Monitor and Alert on Circuit Breaker States

```python
from utils.resilience import get_resilience_status

status = get_resilience_status()
for name, cb_status in status['circuit_breakers'].items():
    if cb_status['state'] == 'open':
        send_alert(f"Circuit breaker {name} is open!")
```

## Configuration Files

### Loading Configuration from JSON

```python
from utils.resilience import resilience_config

# Load from file
resilience_config.load_from_file("resilience_config.json")

# Save current config
resilience_config.save_to_file("resilience_config.json")
```

### Example Configuration File

```json
{
  "retry_configs": {
    "http_requests": {
      "max_attempts": 3,
      "base_delay": 1.0,
      "max_delay": 30.0,
      "exponential_base": 2.0,
      "strategy": "jittered_exponential"
    },
    "database": {
      "max_attempts": 3,
      "base_delay": 0.5,
      "max_delay": 10.0,
      "exponential_base": 2.0,
      "strategy": "exponential_backoff"
    }
  },
  "circuit_breaker_configs": {
    "external_apis": {
      "failure_threshold": 5,
      "recovery_timeout": 60.0,
      "name": "external_apis"
    },
    "database": {
      "failure_threshold": 3,
      "recovery_timeout": 30.0,
      "name": "database"
    }
  }
}
```

## Testing

The framework includes comprehensive tests covering:

- All retry strategies
- Circuit breaker functionality
- Edge cases and error conditions
- Async operations
- Metrics collection
- Integration scenarios

Run tests with:

```bash
python -m pytest tests/test_resilience.py -v
```

## Monitoring and Observability

### Real-time Status

```python
from utils.resilience import get_resilience_status

status = get_resilience_status()
print(f"Overall success rate: {status['success_rate']:.2f}%")
print(f"Total operations: {status['metrics']['total_operations']}")

for name, cb in status['circuit_breakers'].items():
    print(f"Circuit breaker {name}: {cb['state']}")
```

### Metrics Export

```python
# Export detailed metrics
resilience_metrics.export_metrics("daily_resilience_report.json")

# Get operation history
history = resilience_metrics.operation_history[-10:]  # Last 10 operations
```

## Integration Examples

### GitHub API Client

```python
class GitHubClient:
    @retry_http_request(circuit_breaker="github_api")
    async def get_repository(self, owner, repo):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            response.raise_for_status()
            return response.json()
```

### Database Layer

```python
class DatabaseLayer:
    @retry_database_operation()
    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
```

## Troubleshooting

### Common Issues

1. **Too Many Retries**: Reduce max_attempts or increase delays
2. **Circuit Breaker Always Open**: Check failure_threshold and recovery_timeout
3. **Performance Issues**: Use shorter delays or fewer attempts for non-critical operations
4. **Memory Leaks**: Ensure proper cleanup in callback functions

### Debugging

Enable detailed logging:

```python
import logging
logging.getLogger('utils.resilience').setLevel(logging.DEBUG)
```

### Performance Tuning

- Use jittered strategies for high-concurrency scenarios
- Implement custom delay functions for specific needs
- Monitor metrics to optimize configuration

## Migration Guide

### From Basic Requests

```python
# Before
response = requests.get("https://api.example.com")

# After
@retry_http_request()
def fetch_data():
    response = requests.get("https://api.example.com")
    response.raise_for_status()
    return response

result = fetch_data()
```

### From Manual Retry Logic

```python
# Before
for attempt in range(3):
    try:
        return risky_operation()
    except Exception as e:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)

# After
@retry_with_backoff(max_attempts=3)
def safe_operation():
    return risky_operation()

result = safe_operation()
```

## Contributing

When adding new resilience patterns:

1. Add comprehensive tests
2. Update documentation
3. Consider backward compatibility
4. Add metrics collection
5. Include configuration options

## License

This resilience framework is part of the fullstack ecosystem and follows the same licensing terms.
