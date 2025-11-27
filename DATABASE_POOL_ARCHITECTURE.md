# Centralized Database Connection Pool Architecture

## Overview

The application now uses a **centralized, shared database connection pool** managed by `DatabasePool` singleton. This allows multiple repositories to efficiently share a single connection pool, reducing resource consumption and improving scalability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Application (app/main.py)                           │
│                                                             │
│ Startup: DatabasePool.initialize()                          │
│ Shutdown: DatabasePool.close()                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   DatabasePool        │
         │   (Singleton)         │
         │                       │
         │  ┌─────────────────┐  │
         │  │ Connection Pool │  │
         │  │ (2-10 conns)    │  │
         │  └─────────────────┘  │
         │                       │
         └──────┬────────┬───────┘
                │        │
     ┌──────────▼─┐   ┌──┴──────────┐
     │ Movies     │   │ (Future)    │
     │ Repository │   │ User Repo   │
     │            │   │ Orders Repo │
     └────────────┘   └─────────────┘
```

## Key Components

### 1. `DatabasePool` (app/core/database.py)

**Singleton pattern** for application-wide pool management:

```python
# Initialize pool (once at startup)
DatabasePool.initialize(
    host="localhost",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="mysecretpassword",
)

# Use pool in any repository
conn = DatabasePool.get_connection()
try:
    # use connection...
finally:
    DatabasePool.return_connection(conn)

# Close pool (at shutdown)
DatabasePool.close()
```

**Features:**
- ✅ Singleton pattern (only one instance application-wide)
- ✅ Thread-safe
- ✅ Simple initialization
- ✅ Configurable pool size
- ✅ Proper cleanup on shutdown

### 2. `MoviesRepository` (app/repositories/movies_repository.py)

**Simplified to use the shared pool:**

```python
# Before: Repository created its own pool
repository = MoviesRepository(
    host="localhost",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="mysecretpassword",
)

# After: Repository is simple, pool is shared
repository = MoviesRepository()
```

**Changes:**
- Removed pool creation from constructor
- Now just uses `DatabasePool.get_connection()`
- No pool cleanup needed (handled by DatabasePool)

### 3. `app/main.py` (Application Startup/Shutdown)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared pool
    DatabasePool.initialize(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    
    # Create repositories (they use the shared pool)
    repository = MoviesRepository()
    movies_service = MoviesService(repository)
    
    yield
    
    # Shutdown: Close shared pool
    DatabasePool.close()
```

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Pool Management** | In each repository | Centralized in DatabasePool |
| **Pool Instances** | One per repository | Single application-wide |
| **Scalability** | Hard to add repos | Easy - just use DatabasePool |
| **Resource Control** | Multiple pools | Single pool, bounded |
| **Code Clarity** | Mixed concerns | Separation of concerns |

## Adding New Repositories

Now it's trivial to add more repositories that share the same pool:

### Example: UserRepository

```python
# app/repositories/user_repository.py
from app.core.database import DatabasePool
from psycopg2.extras import RealDictCursor

class UserRepository:
    def __init__(self):
        if not DatabasePool.is_initialized():
            raise RuntimeError("DatabasePool not initialized")
        self.users = []
        self._load_users()
    
    def _load_users(self):
        conn = None
        try:
            conn = DatabasePool.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users")
                # ... load users ...
        finally:
            if conn:
                DatabasePool.return_connection(conn)
```

**That's it!** No pool management needed.

## Configuration

### Default Behavior

```python
DatabasePool.initialize()  # Uses all defaults
```

Pool config:
- Host: `localhost`
- Port: `5432`
- Database: `postgres`
- User: `postgres`
- Password: `mysecretpassword`
- Min connections: `2`
- Max connections: `10`

### Custom Configuration

```python
DatabasePool.initialize(
    host="db.example.com",
    port=5432,
    dbname="myapp",
    user="appuser",
    password="secure_password",
    min_connections=5,
    max_connections=20,
)
```

### Environment-Based Configuration

In `app/main.py`:

```python
from app.core.config import get_settings

settings = get_settings()
DatabasePool.initialize(
    host=settings.db_host,
    port=settings.db_port,
    dbname=settings.db_name,
    user=settings.db_user,
    password=settings.db_password,
)
```

## Startup/Shutdown Logs

### Startup
```
INFO - Connecting to PostgreSQL at localhost:5432/postgres
INFO - Initialized database connection pool (2-10 connections)
INFO - Loaded 86537 movies from PostgreSQL
INFO - Application started with 86537 movies loaded
INFO - Application startup complete
```

### Shutdown
```
INFO - Application shutting down
INFO - Closed database connection pool
INFO - Database connection pool closed
INFO - Application shutdown complete
```

## Thread Safety

`psycopg2.pool.SimpleConnectionPool` is thread-safe:
- ✅ Safe for FastAPI async requests
- ✅ Safe for concurrent access
- ✅ Safe for multiple workers (with caution)

> For multi-process workers, each process gets its own pool (which is correct behavior).

## Monitoring & Debugging

### Check if Pool is Initialized

```python
if DatabasePool.is_initialized():
    print("Pool is ready")
```

### Pool Status

Monitor connection availability:
- Min connections: Always available
- Max connections: Upper limit
- Current available: Varies based on load

Track in logs:
```
Created connection pool with 2-10 connections
```

## Migration Guide

If you have existing repositories with their own pools:

1. **Remove pool creation from repository `__init__`**
   ```python
   # Remove: self.pool = create_pool(...)
   ```

2. **Add import**
   ```python
   from app.core.database import DatabasePool
   ```

3. **Update connection usage**
   ```python
   # Before
   conn = self.pool.getconn()
   
   # After
   conn = DatabasePool.get_connection()
   ```

4. **Add pool check**
   ```python
   def __init__(self):
       if not DatabasePool.is_initialized():
           raise RuntimeError("DatabasePool not initialized")
   ```

5. **Initialize DatabasePool in main.py**
   ```python
   DatabasePool.initialize(...)
   ```

## Performance Characteristics

- **First Connection**: ~100ms (connection creation)
- **Pooled Connections**: ~1ms (reuse)
- **Max Overhead**: Minimal (just getting/returning connection)
- **Memory**: Fixed (bounded by max_connections)

## Future Enhancements

1. **ThreadedConnectionPool**: For explicit thread safety
   ```python
   from psycopg2.pool import ThreadedConnectionPool
   # Use ThreadedConnectionPool instead of SimpleConnectionPool
   ```

2. **Async Support**: Use `asyncpg` for native async
   ```python
   import asyncpg
   # Replace psycopg2 with asyncpg
   ```

3. **Connection Pooling Metrics**: Monitor pool usage
   ```python
   # Track getconn/putconn calls
   # Log pool saturation warnings
   ```

4. **Retry Logic**: Handle connection failures gracefully
   ```python
   # Retry getting connection if pool is exhausted
   ```

## Troubleshooting

### "DatabasePool not initialized"

**Error**: RuntimeError when creating repository before pool initialization

**Solution**: Ensure `DatabasePool.initialize()` is called in `app/main.py` before creating any repositories

### "No connections available"

**Error**: Pool exhausted, no connections available within timeout

**Solution**: Increase `max_connections` or check for connection leaks (not returning connections)

### Connection Leaks

**Symptom**: Connections gradually become unavailable

**Debug**: Ensure all `DatabasePool.get_connection()` calls have matching `DatabasePool.return_connection()` in finally block

## Example: Multiple Repositories Sharing One Pool

```python
# app/main.py
DatabasePool.initialize(...)

# Create multiple repositories - they share the same pool!
movies_repo = MoviesRepository()      # Uses pool
users_repo = UserRepository()          # Uses same pool
orders_repo = OrdersRepository()       # Uses same pool

# All three repositories share the 2-10 connections efficiently
```

This is the key improvement - **scalable, centralized resource management** for your entire application!
