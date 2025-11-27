# Creating a New Repository

Quick guide for developers adding new repositories to the Movie API.

## Template

```python
"""[Feature] repository for PostgreSQL data access."""
import logging
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.database import DatabasePool
from app.models.[feature] import [FeatureModel]

logger = logging.getLogger(__name__)


class [Feature]Repository:
    """Repository for managing [feature] data from PostgreSQL database.
    
    Uses the shared connection pool managed by DatabasePool.
    """

    def __init__(self) -> None:
        """Initialize the repository.

        Raises:
            RuntimeError: If DatabasePool is not initialized.
        """
        if not DatabasePool.is_initialized():
            raise RuntimeError(
                "DatabasePool not initialized. Call DatabasePool.initialize() first."
            )
        
        self.[features]: List[[FeatureModel]] = []
        self.[feature]_dict: dict[int, [FeatureModel]] = {}

        self._load_[features]()

    def _load_[features](self) -> None:
        """Load all [features] from PostgreSQL database.

        Gets a connection from the shared pool and fetches all [features]
        from the [features] table.
        """
        conn = None
        try:
            # Get connection from shared pool
            conn = DatabasePool.get_connection()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM [features]")
                rows = cur.fetchall()

                for row in rows:
                    [feature] = [FeatureModel](...)
                    self.[features].append([feature])
                    self.[feature]_dict[row["id"]] = [feature]

            logger.info(f"Loaded {len(self.[features])} [features] from PostgreSQL")
        except psycopg2.Error as e:
            logger.error(f"Error loading [features] from PostgreSQL: {e}")
            raise
        finally:
            # Return connection to shared pool
            if conn:
                DatabasePool.return_connection(conn)

    def get_[feature]_by_id(self, id: int) -> Optional[[FeatureModel]]:
        """Get a [feature] by its ID.

        Args:
            id: The [feature] ID to retrieve.

        Returns:
            Optional[[FeatureModel]]: The [feature] if found, None otherwise.
        """
        return self.[feature]_dict.get(id)

    def list_[features](self, page: int = 1, page_size: int = 20) -> Tuple[List[[FeatureModel]], int]:
        """List all [features] with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            Tuple[List[[FeatureModel]], int]: [Features] for page and total count.
        """
        total = len(self.[features])
        start = (page - 1) * page_size
        end = start + page_size
        
        return self.[features][start:end], total
```

## Key Points

### 1. ✅ Import DatabasePool

```python
from app.core.database import DatabasePool
```

### 2. ✅ Check Pool is Initialized

```python
def __init__(self):
    if not DatabasePool.is_initialized():
        raise RuntimeError("DatabasePool not initialized.")
```

### 3. ✅ Use get_connection() and return_connection()

```python
conn = None
try:
    conn = DatabasePool.get_connection()
    # Use connection...
finally:
    if conn:
        DatabasePool.return_connection(conn)
```

### 4. ✅ Handle Exceptions

```python
except psycopg2.Error as e:
    logger.error(f"Error: {e}")
    raise
```

## Common Patterns

### Pattern 1: Load and Cache

```python
def _load_items(self):
    conn = None
    try:
        conn = DatabasePool.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM items")
            for row in cur.fetchall():
                self.items.append(Item(id=row["id"], name=row["name"]))
    finally:
        if conn:
            DatabasePool.return_connection(conn)
```

### Pattern 2: Filter In-Memory

```python
def search_items(self, query: str) -> List[Item]:
    query_lower = query.lower()
    return [i for i in self.items if query_lower in i.name.lower()]
```

### Pattern 3: Paginate

```python
def paginate(self, items: List[Item], page: int, page_size: int) -> Tuple[List[Item], int]:
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], len(items)
```

## Do's and Don'ts

### ✅ DO

- Use `DatabasePool.get_connection()` in try block
- Return connection in finally block
- Check `DatabasePool.is_initialized()` in `__init__`
- Cache data after loading if frequently accessed
- Use `RealDictCursor` for easy dict-like access

### ❌ DON'T

- Create your own connection pool
- Forget to return connection to pool
- Create new `psycopg2.connect()` directly
- Hold connections for long periods
- Create database connections outside try/finally

## Example: User Repository

```python
from app.core.database import DatabasePool
from app.models.user import User

class UserRepository:
    def __init__(self):
        if not DatabasePool.is_initialized():
            raise RuntimeError("DatabasePool not initialized")
        self.users: List[User] = []
        self._load_users()

    def _load_users(self):
        conn = None
        try:
            conn = DatabasePool.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, email, name FROM users")
                for row in cur.fetchall():
                    user = User(
                        id=row["id"],
                        email=row["email"],
                        name=row["name"]
                    )
                    self.users.append(user)
        finally:
            if conn:
                DatabasePool.return_connection(conn)

    def get_user(self, user_id: int) -> Optional[User]:
        return next((u for u in self.users if u.id == user_id), None)
```

## Integration in main.py

```python
from app.repositories.user_repository import UserRepository

# In lifespan startup:
DatabasePool.initialize(...)

user_repo = UserRepository()
movies_repo = MoviesRepository()

# Both use the same pool!

# In lifespan shutdown:
DatabasePool.close()
```

## Testing

With the centralized pool, testing is easier:

```python
import pytest
from app.core.database import DatabasePool
from app.repositories.user_repository import UserRepository

@pytest.fixture
def db_pool():
    """Initialize test database pool."""
    DatabasePool.initialize(
        dbname="test_db",
        user="test_user",
        password="test_pass"
    )
    yield
    DatabasePool.close()

@pytest.fixture
def user_repo(db_pool):
    """Create user repository for testing."""
    return UserRepository()

def test_get_user(user_repo):
    user = user_repo.get_user(1)
    assert user is not None
```

## See Also

- [DATABASE_POOL_ARCHITECTURE.md](DATABASE_POOL_ARCHITECTURE.md) - Detailed architecture guide
- [CONNECTION_POOLING.md](CONNECTION_POOLING.md) - Original connection pooling implementation
- `app/repositories/movies_repository.py` - Real example
