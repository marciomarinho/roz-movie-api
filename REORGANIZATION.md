# Project Structure Reorganization

## What was moved

The following utility scripts have been moved to the `/scripts` folder to keep the project root clean and well-organized:

### Moved Files
- ✅ `load_movies.py` → `scripts/load_movies.py`
- ✅ `test_api_key.py` → `scripts/test_api_key.py`
- ✅ `test_api_key.bat` → `scripts/test_api_key.bat`

### Current Root Structure (Cleaned)

```
movie_api/
├── app/                      # Main application code
│   ├── api/                  # FastAPI routes
│   ├── core/                 # Configuration & security
│   ├── deps/                 # Dependencies (auth, etc.)
│   ├── models/               # Pydantic schemas
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic
│   └── main.py              # Application factory
│
├── scripts/                  # Utility scripts (NEW)
│   ├── load_movies.py       # Load data into PostgreSQL
│   ├── test_api_key.py      # Test API key validation (Python)
│   ├── test_api_key.bat     # Test API key validation (Batch)
│   └── README.md            # Scripts documentation
│
├── tests/                    # Test suite
├── data/                     # Data files (CSV)
├── .env                      # Environment configuration
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── README.md                # Main documentation
└── ...other files...
```

## Benefits

1. **Cleaner Root Directory**: Only core project files and configuration at root level
2. **Better Organization**: Scripts and utilities clearly separated from application code
3. **Easier Maintenance**: Clear distinction between production code and development/utility scripts
4. **Better Documentation**: Scripts folder has its own README with usage examples
5. **Scalability**: Easy to add more scripts in the future (e.g., `deploy.py`, `backup.py`, etc.)

## Usage

All scripts are run from the project root directory:

```bash
# Load movies
python scripts/load_movies.py --dbname=postgres --user=postgres --password=mysecretpassword --create-table

# Test API key (Python)
python scripts/test_api_key.py

# Test API key (Batch/Windows)
scripts\test_api_key.bat
```

See `scripts/README.md` for detailed documentation on each script.
