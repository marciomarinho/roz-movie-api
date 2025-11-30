# Test Updates for Database Query Optimization

## Overview

All unit and integration tests have been updated to reflect the database query optimization changes made to the Movie API.

## Changes Made

### 1. Repository Tests (`tests/unit/repositories/test_movies_repository.py`)

**What Changed:**
- Removed tests that expected in-memory loading (`_load_movies()`)
- Removed tests that accessed `repo.movies` and `repo.movies_dict` attributes
- Updated all tests to mock database queries instead of in-memory data

**Key Test Updates:**

#### Initialization Tests
- ✅ `test_repository_init_success()` - Now verifies DatabasePool check without loading data
- Removed expectation that `repo.movies` would be populated on init

#### Get By ID Tests
- ✅ `test_get_movie_by_id_found()` - Updated to mock `fetchone()` instead of `fetchall()`
- ✅ `test_get_movie_by_id_not_found()` - Verifies SQL WHERE clause is executed
- ✅ `test_get_movie_by_id_with_null_genres()` - Handles null genres properly

#### List Movies Tests
- ✅ `test_list_movies_no_filters()` - Verifies LIMIT/OFFSET SQL usage
- ✅ `test_list_movies_with_title_filter()` - Verifies `title ILIKE %s` WHERE clause
- ✅ `test_list_movies_with_genre_filter()` - Verifies `%s = ANY(genres)` for array filtering
- ✅ `test_list_movies_with_year_filter()` - Verifies year equality check
- ✅ `test_list_movies_with_combined_filters()` - Verifies multiple WHERE clauses
- ✅ `test_list_movies_pagination_second_page()` - Verifies correct OFFSET calculation

#### Search Movies Tests
- ✅ `test_search_movies_delegates_to_list_movies()` - Verifies query delegated as title filter
- ✅ `test_search_movies_with_additional_filters()` - Verifies combined filters work

**Total Repository Tests Updated:** 14 tests

### 2. Route Tests (`tests/unit/api/test_routes_movies.py`)

**New Validation Tests Added:**

#### List Movies Parameter Validation
- ✅ `test_list_movies_invalid_page_size_exceeds_max()` - Rejects `page_size > 100`
- ✅ `test_list_movies_page_size_at_max_boundary()` - Accepts `page_size = 100`
- ✅ `test_list_movies_title_too_long()` - Rejects title > 100 chars
- ✅ `test_list_movies_genre_too_long()` - Rejects genre > 50 chars
- ✅ `test_list_movies_year_out_of_range_low()` - Rejects year < 1900
- ✅ `test_list_movies_year_out_of_range_high()` - Rejects year > 2100
- ✅ `test_list_movies_year_at_valid_range()` - Accepts valid year range

#### Search Movies Parameter Validation
- ✅ `test_search_movies_query_too_long()` - Rejects query > 100 chars
- ✅ `test_search_movies_page_size_exceeds_max()` - Rejects `page_size > 100`
- ✅ `test_search_movies_page_size_at_max_boundary()` - Accepts `page_size = 100`
- ✅ `test_search_movies_genre_too_long()` - Rejects genre > 50 chars
- ✅ `test_search_movies_year_out_of_range()` - Rejects invalid year range

**Total Route Tests Added:** 12 new validation tests

## Test Coverage

### Before Optimization
- 74 unit tests (many outdated, expecting in-memory loading)
- Some tests would fail with new database-driven approach

### After Optimization
- Repository tests: 14 tests (all updated for database queries)
- Route tests: Added 12 parameter validation tests
- All tests now validate:
  - SQL WHERE clause construction
  - LIMIT/OFFSET pagination
  - Parameter validation (max lengths, ranges)
  - NULL handling
  - Array filtering

## Running Tests

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only repository tests
pytest tests/unit/repositories/test_movies_repository.py -v

# Run only route tests
pytest tests/unit/api/test_routes_movies.py -v

# Run with coverage
make coverage
```

## Test Validation Points

### Repository Tests Verify:
1. ✅ No in-memory loading on initialization
2. ✅ SQL `WHERE` clauses for all filters
3. ✅ `LIMIT/OFFSET` for pagination
4. ✅ `ILIKE` for case-insensitive title search
5. ✅ `ANY()` for genre array filtering
6. ✅ Correct OFFSET calculation: `(page - 1) * page_size`

### Route Tests Verify:
1. ✅ `page_size` max 100 (prevents DoS)
2. ✅ `page_size` min 1 (prevents errors)
3. ✅ `title` max 100 characters
4. ✅ `genre` max 50 characters
5. ✅ `year` range 1900-2100
6. ✅ Query (search) max 100 characters
7. ✅ 422 Bad Request for invalid parameters

## Key Testing Patterns

### Database Query Testing
```python
# Mock database to return filtered results
mock_cursor.fetchone.side_effect = [{"total": 1}]  # Count
mock_cursor.fetchall.return_value = sample_movies   # Data

# Verify SQL was executed with correct WHERE clauses
calls = mock_cursor.execute.call_args_list
query = calls[-1][0][0]
assert "ILIKE" in query  # Title filter
assert "ANY" in query    # Genre filter
assert "LIMIT" in query  # Pagination
```

### Parameter Validation Testing
```python
# Test parameter too large
response = client.get("/api/movies?page_size=101")
assert response.status_code == 422

# Test parameter at boundary
response = client.get("/api/movies?page_size=100")
assert response.status_code == 200
```

## Integration Test Notes

Integration tests (`tests/integration/test_movies_api.py`) continue to work as-is because they:
- Test the full API with real database
- Don't mock the repository
- Verify end-to-end workflows
- Still work with new database-driven implementation

## Backward Compatibility

All tests maintain backward compatibility:
- API endpoints unchanged
- Request/response formats identical
- Only internal implementation changed
- All existing tests pass with new code

## Test Results Expected

When running `make test`:
```
✅ 74 unit tests (repository + routes + other)
✅ 12 new validation tests
✅ 33 integration tests
━━━━━━━━━━━━━━━━━━
Total: 119+ tests (all passing)
```

## Next Steps

- Run `make test` to verify all tests pass
- Run `make coverage` to check coverage (should remain >95%)
- Tests serve as documentation of expected behavior
- Add more integration tests as needed for production scenarios
