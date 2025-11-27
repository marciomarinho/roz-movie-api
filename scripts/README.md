# Scripts

Utility scripts for the Movie API project.

## Overview

This directory contains utility scripts for database management and testing.

## Scripts

### `load_movies.py`
Load MovieLens movies CSV data into PostgreSQL database.

**Prerequisites:**
- PostgreSQL database running
- `psycopg2` installed (`pip install psycopg2-binary`)

**Usage:**
```bash
python scripts/load_movies.py \
  --dbname=postgres \
  --user=postgres \
  --password=mysecretpassword \
  --create-table \
  --csv-path=data/movies.csv
```

**Options:**
- `--csv-path`: Path to movies.csv file (default: `data/movies.csv`)
- `--host`: PostgreSQL host (default: `localhost`)
- `--port`: PostgreSQL port (default: `5432`)
- `--dbname`: PostgreSQL database name (required)
- `--user`: PostgreSQL username (required)
- `--password`: PostgreSQL password (required)
- `--create-table`: Create the movies table if it doesn't exist
- `--drop-table`: Drop the movies table before loading (useful for fresh start)

**Examples:**

Fresh load (create table and load data):
```bash
python scripts/load_movies.py \
  --dbname=postgres --user=postgres --password=mysecretpassword \
  --create-table --csv-path=data/movies.csv
```

Drop and reload:
```bash
python scripts/load_movies.py \
  --dbname=postgres --user=postgres --password=mysecretpassword \
  --drop-table --create-table --csv-path=data/movies.csv
```

### `test_api_key.py`
Test API key validation using Python requests library.

**Prerequisites:**
- Python `requests` package: `pip install requests`
- API server running on `http://127.0.0.1:8000`

**Usage:**
```bash
python scripts/test_api_key.py
```

**What it tests:**
1. Request without X-API-Key header (should fail with 401)
2. Request with invalid X-API-Key (should fail with 401)
3. Request with valid X-API-Key (should succeed with 200)
4. Search endpoint with valid X-API-Key (should succeed)

### `test_api_key.bat`
Test API key validation using curl commands (Windows batch script).

**Prerequisites:**
- `curl` command available (comes with Windows 10+)
- API server running on `http://127.0.0.1:8000`

**Usage:**
```bash
scripts\test_api_key.bat
```

**What it tests:**
1. Request without X-API-Key header (should return 401)
2. Request with invalid X-API-Key (should return 401)
3. Request with valid X-API-Key (should return 200)
4. Health endpoint (no API key required, should return 200)

## Running Scripts from Project Root

All scripts assume they're executed from the project root directory:

```bash
# From project root
python scripts/load_movies.py ...
python scripts/test_api_key.py
scripts/test_api_key.bat
```

## Notes

- The default API key for testing is: `test-api-key-12345`
- This can be changed in the `.env` file: `API_KEY=your-secret-key`
- Scripts should be run from the project root directory for relative paths to work correctly
