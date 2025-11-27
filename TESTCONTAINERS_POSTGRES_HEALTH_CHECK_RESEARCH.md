# Research: Testcontainers PostgreSQL Health Check Issues on Windows

## Problem Summary

The testcontainers PostgreSQL container hangs indefinitely on Windows with Docker Desktop because it uses `LogMessageWaitStrategy` to look for "database system is ready to accept connections" in container logs. This message appears to never be logged in Docker Desktop on Windows, causing infinite waiting.

**Related Issue**: [testcontainers-python Issue #360](https://github.com/testcontainers/testcontainers-python/issues/360) - "Containers fail to start: mssql/win11, mssql/m1, mssql with different port (not intended to work), postgres/win10, mariadb/win11, oracle"

---

## Configuration Options Available

### 1. **Timeout Configuration (Recommended)**

You can set a **custom startup timeout** instead of waiting indefinitely:

```python
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

# Create container with custom wait strategy and timeout
postgres = PostgresContainer("postgres:15-alpine")
postgres.waiting_for(
    LogMessageWaitStrategy("database system is ready to accept connections")
    .with_startup_timeout(30)  # 30 seconds maximum wait
    .with_poll_interval(0.5)   # Check every 0.5 seconds
)
postgres.start()
```

**Default timeout** from testcontainers config is typically 60 seconds (`testcontainers_config.timeout`).

**Key Methods**:
- `.with_startup_timeout(timeout: Union[int, timedelta])` - Set max wait time in seconds
- `.with_poll_interval(interval: Union[float, timedelta])` - Set how often to check (default: usually 1 second)

---

### 2. **Alternative Wait Strategies (Recommended Solution)**

Instead of waiting for the elusive log message, use **alternative wait strategies** that are more reliable on Windows:

#### Option A: Port Wait Strategy (Most Reliable)
```python
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import PortWaitStrategy

with PostgresContainer("postgres:15-alpine") as postgres:
    postgres.waiting_for(
        PortWaitStrategy(5432)
        .with_startup_timeout(30)
        .with_poll_interval(0.5)
    )
    connection_url = postgres.get_connection_url()
```

This simply checks if PostgreSQL is listening on port 5432 and doesn't depend on specific log messages.

#### Option B: Composite Wait Strategy (Robust)
```python
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import (
    CompositeWaitStrategy,
    PortWaitStrategy,
    LogMessageWaitStrategy
)

with PostgresContainer("postgres:15-alpine") as postgres:
    postgres.waiting_for(
        CompositeWaitStrategy(
            PortWaitStrategy(5432),  # Wait for port first
            LogMessageWaitStrategy("database system is ready")
            .with_startup_timeout(5)  # Short timeout after port is ready
        )
    )
    connection_url = postgres.get_connection_url()
```

---

### 3. **Using DockerContainer Core API (Workaround)**

Based on community solutions in Issue #360, bypass the specialized PostgresContainer and use the core API with manual wait:

```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import time

# Use core container instead of specialized PostgresContainer
container = DockerContainer("postgres:15-alpine")
container.env = {
    "POSTGRES_DB": "testdb",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "password"
}
container.with_exposed_ports(5432)

# Start container without waiting
container.start()

# Use manual wait with fallback timeout
try:
    delay = wait_for_logs(
        container,
        "database system is ready to accept connections",
        timeout=10  # 10 second timeout instead of infinite
    )
    print(f"Container ready after {delay:.2f} seconds")
except TimeoutError:
    print("Log message not found, but container may still be ready...")
    time.sleep(2)  # Additional grace period

# Get connection details
host = container.get_container_host_ip()
port = container.get_exposed_port(5432)
connection_url = f"postgresql://postgres:password@{host}:{port}/testdb"
```

---

### 4. **Environment Variables for Global Configuration**

Set testcontainers configuration via environment variables:

```bash
# Default timeout in seconds (applies to all containers)
TESTCONTAINERS_TIMEOUT=30

# Or in Python before importing testcontainers
import os
os.environ["TESTCONTAINERS_TIMEOUT"] = "30"
```

The config is loaded from `testcontainers.core.config.testcontainers_config`.

---

## Wait Strategy API Reference

All wait strategies inherit from `WaitStrategy` base class and support these methods:

```python
# Timeout configuration
.with_startup_timeout(timeout: Union[int, timedelta]) -> WaitStrategy
    # Default: 60 seconds (configurable via testcontainers_config)
    # Returns: self for method chaining

# Polling interval
.with_poll_interval(interval: Union[float, timedelta]) -> WaitStrategy
    # Default: usually 1 second
    # How frequently to check if condition is met
    # Returns: self for method chaining

# Exception handling
.with_transient_exceptions(*exceptions: type[Exception]) -> WaitStrategy
    # Exceptions to retry on (default: TimeoutError, ConnectionError)
    # Returns: self for method chaining
```

### Available Wait Strategies

| Strategy | Pros | Cons | Reliable on Windows |
|----------|------|------|-------------------|
| `LogMessageWaitStrategy(pattern)` | Specific, fine-grained | Depends on log output | ❌ NO |
| `PortWaitStrategy(port)` | Fast, reliable | Generic | ✅ YES |
| `HttpWaitStrategy(port, path)` | Application-aware | Requires HTTP service | ✅ YES |
| `HealthcheckWaitStrategy()` | Docker native | Requires health check config | ⚠️ Maybe |
| `CompositeWaitStrategy(*strategies)` | Flexible combining | More complex | ✅ YES |

---

## Known Issues on Windows

### Issue #360 Root Causes Identified:

1. **Docker Desktop on Windows (WSL2)**: 
   - Container logs may not be captured correctly
   - Timing issues when pulling images and starting containers
   - Docker log streaming can fail intermittently

2. **Symptoms**:
   - Container prints "Waiting to be ready..." indefinitely
   - No timeout, just hangs
   - Works fine on Linux
   - Sometimes works if adding manual `time.sleep(1-2)` delays

3. **Why LogMessageWaitStrategy Fails**:
   - The wait strategy tails container logs looking for specific text
   - On Windows with Docker Desktop, the "database system is ready to accept connections" message either:
     - Arrives after the strategy has already given up polling
     - Appears in different format than expected
     - Gets buffered and not streamed to the client

---

## Recommended Solutions (In Order of Preference)

### 1. ✅ **Best Practice**: Use `PortWaitStrategy`
```python
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import PortWaitStrategy

with PostgresContainer("postgres:15-alpine") as postgres:
    postgres.waiting_for(
        PortWaitStrategy(5432).with_startup_timeout(30)
    )
    # Use postgres...
```

**Why**: Port listening is more reliable than log message parsing across platforms.

### 2. ✅ **Good Practice**: Use `CompositeWaitStrategy`
```python
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import (
    CompositeWaitStrategy,
    PortWaitStrategy
)

with PostgresContainer("postgres:15-alpine") as postgres:
    postgres.waiting_for(
        CompositeWaitStrategy(
            PortWaitStrategy(5432),
            LogMessageWaitStrategy("ready").with_startup_timeout(5)
        )
    )
    # Use postgres...
```

**Why**: Combines reliability of port checking with log confirmation.

### 3. ✅ **Fallback**: Use Core API with Timeout
```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import time

container = DockerContainer("postgres:15-alpine")
container.env = {"POSTGRES_PASSWORD": "password"}
container.start()

try:
    wait_for_logs(container, "ready", timeout=10)
except TimeoutError:
    time.sleep(2)  # Grace period

# Use container...
container.stop()
```

**Why**: Direct control over timeout prevents infinite hangs.

### 4. ⚠️ **Last Resort**: Increase Timeout and Add Delays
```python
postgres = PostgresContainer("postgres:15-alpine")
postgres.waiting_for(
    LogMessageWaitStrategy("ready")
    .with_startup_timeout(60)
    .with_poll_interval(0.2)
)
postgres.start()
time.sleep(3)  # Additional grace period
```

---

## Environment Variables & Configuration

### testcontainers Configuration
Located in: `testcontainers.core.config.testcontainers_config`

```python
from testcontainers.core.config import testcontainers_config

# Read current settings
print(f"Timeout: {testcontainers_config.timeout} seconds")
print(f"Sleep/poll interval: {testcontainers_config.sleep_time} seconds")

# Set via environment variables BEFORE importing containers
import os
os.environ["TESTCONTAINERS_TIMEOUT"] = "30"
os.environ["TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE"] = "/var/run/docker.sock"
```

### Other Relevant Environment Variables

- `TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE` - Docker socket path (for DinD)
- `TESTCONTAINERS_RYUK_DISABLED` - Disable cleanup (debugging only)
- `DOCKER_AUTH_CONFIG` - Private registry authentication
- `TESTCONTAINERS_HOST_OVERRIDE` - Override host IP detection

---

## Implementation in Your Code

Your current setup in `conftest.py` uses:
```python
with PostgresContainer("postgres:15-alpine") as postgres:
    # This uses default LogMessageWaitStrategy which hangs on Windows
    db_url = postgres.get_connection_url()
```

### Recommended Fix:
```python
from testcontainers.core.wait_strategies import PortWaitStrategy

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        # Add explicit wait strategy
        postgres.waiting_for(
            PortWaitStrategy(5432).with_startup_timeout(30)
        )
        db_url = postgres.get_connection_url()
        # ... rest of initialization ...
        yield postgres
```

---

## Testing Your Fix

```python
# test_wait_strategy.py
from testcontainers.postgres import PostgresContainer
from testcontainers.core.wait_strategies import PortWaitStrategy
import time

def test_postgres_startup_with_port_wait():
    """Test that PortWaitStrategy reliably starts PostgreSQL on Windows"""
    start = time.time()
    
    with PostgresContainer("postgres:15-alpine") as postgres:
        postgres.waiting_for(
            PortWaitStrategy(5432).with_startup_timeout(30)
        )
        
        url = postgres.get_connection_url()
        elapsed = time.time() - start
        
        print(f"Container started in {elapsed:.2f} seconds")
        print(f"Connection URL: {url}")
        
        # Verify connectivity
        import psycopg2
        conn = psycopg2.connect(url)
        conn.close()
        
        assert elapsed < 30, "Should start within 30 seconds"
```

---

## Summary Table

| Approach | Timeout Control | Log Dependent | Windows Reliable | Complexity |
|----------|-----------------|---------------|-----------------|------------|
| Default PostgresContainer | No (infinite) | ✅ Yes | ❌ NO | Low |
| PortWaitStrategy | ✅ Yes | ❌ No | ✅ YES | Low |
| LogMessageWaitStrategy w/ timeout | ✅ Yes | ✅ Yes | ⚠️ Maybe | Low |
| CompositeWaitStrategy | ✅ Yes | Optional | ✅ YES | Medium |
| Core API + Manual Wait | ✅ Yes | Optional | ✅ YES | Medium |

---

## References

- [testcontainers-python GitHub Issue #360](https://github.com/testcontainers/testcontainers-python/issues/360)
- [testcontainers-python Wait Strategies Documentation](https://testcontainers-python.readthedocs.io/en/latest/core/README.html)
- [testcontainers-python Source: waiting_utils.py](https://github.com/testcontainers/testcontainers-python/blob/main/core/testcontainers/core/waiting_utils.py)
- [testcontainers-python Source: wait_strategies.py](https://github.com/testcontainers/testcontainers-python/blob/main/core/testcontainers/core/wait_strategies.py)

