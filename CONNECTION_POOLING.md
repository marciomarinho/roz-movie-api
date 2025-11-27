# Connection Pooling Implementation

## Overview

The `MoviesRepository` now uses **PostgreSQL connection pooling** via `psycopg2.pool.SimpleConnectionPool` for improved performance and resource management.

## What is Connection Pooling?

Connection pooling maintains a set of reusable database connections that are shared across the application. Instead of creating a new connection for every request (which is expensive), connections are borrowed from the pool and returned when done.

### Benefits:

✅ **Better Performance**: Reuse existing connections instead of creating new ones  
✅ **Resource Efficiency**: Limits the total number of connections to PostgreSQL  
✅ **Scalability**: Handles concurrent requests better  
✅ **Production Ready**: Standard practice for production applications  

## Implementation Details

### Pool Configuration

```python
pool.SimpleConnectionPool(
    min_connections=2,    # Minimum idle connections
    max_connections=10,   # Maximum connections allowed
    **connection_params
)
```

**Parameters:**
- `min_connections=2`: At least 2 connections are always available
- `max_connections=10`: At most 10 connections can exist (default, configurable)
- More connections can be created on-demand up to the max limit

### Connection Lifecycle

1. **Initialization** (`__init__`):
   - Pool is created as a class variable (shared across all instances)
   - Created once on first `MoviesRepository` instantiation

2. **Getting Connections** (`_load_movies`):
   ```python
   conn = MoviesRepository._connection_pool.getconn()
   ```
   - Gets a connection from the pool
   - Creates a new one if all are in use (up to max_connections)

3. **Returning Connections** (finally block):
   ```python
   MoviesRepository._connection_pool.putconn(conn)
   ```
   - Returns connection to the pool for reuse
   - Always happens, even if an error occurs

4. **Cleanup** (`close_pool`):
   ```python
   MoviesRepository.close_pool()
   ```
   - Called on application shutdown
   - Closes all connections in the pool

### Key Code Changes

**Before (Individual Connections):**
```python
conn = psycopg2.connect(**self.conn_params)
# use connection...
conn.close()  # connection discarded
```

**After (Connection Pool):**
```python
conn = MoviesRepository._connection_pool.getconn()
try:
    # use connection...
finally:
    MoviesRepository._connection_pool.putconn(conn)  # connection reused
```

## Application Integration

### Startup (`app/main.py`):
```python
repository = MoviesRepository(
    host=settings.db_host,
    port=settings.db_port,
    dbname=settings.db_name,
    user=settings.db_user,
    password=settings.db_password,
)
```
- Pool is created automatically on first instantiation
- Message: `Created connection pool with 2-10 connections`

### Shutdown (`app/main.py`):
```python
MoviesRepository.close_pool()
```
- All connections properly closed
- Resources released back to PostgreSQL
- Message: `Closed connection pool`

## Configuration

To change pool sizes, modify the `MoviesRepository` instantiation in `app/main.py`:

```python
repository = MoviesRepository(
    host=settings.db_host,
    port=settings.db_port,
    dbname=settings.db_name,
    user=settings.db_user,
    password=settings.db_password,
    min_connections=5,     # Increase minimum connections
    max_connections=20,    # Increase maximum connections
)
```

### Recommended Settings:

- **Development**: `min_connections=2, max_connections=5`
- **Production (small)**: `min_connections=5, max_connections=20`
- **Production (large)**: `min_connections=10, max_connections=50`

> **Note**: Don't set max_connections higher than PostgreSQL's `max_connections` setting!

## Monitoring

Watch the startup logs for connection pool creation:

```
INFO: Created connection pool with 2-10 connections
INFO: Loaded 86537 movies from PostgreSQL
INFO: Application started with 86537 movies loaded
```

And shutdown logs for cleanup:

```
INFO: Application shutting down
INFO: Closed connection pool
```

## Error Handling

The implementation includes proper error handling:

1. **Pool Creation Failures**: Logs and raises exception
2. **Connection Errors**: Logs error and raises exception
3. **Connection Return**: Guaranteed in finally block, even on errors

## Performance Impact

For the MovieLens API:

- **First Request**: Slightly slower (creates initial connections)
- **Subsequent Requests**: Much faster (reuses connections)
- **Concurrent Requests**: Better resource utilization
- **Memory Usage**: More predictable (fixed pool size)

## Thread Safety

`SimpleConnectionPool` is thread-safe and can be used safely in multi-threaded/async environments like FastAPI.

## Future Enhancements

Consider upgrading to `psycopg2.pool.ThreadedConnectionPool` for better thread-safety guarantees, or `asyncpg` library for native async support.
