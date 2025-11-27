# Quick Make Recipes

## Copy & Paste Commands

### Setup
```bash
make setup                  # Do this first!
make info                   # Verify setup
```

### Daily Development
```bash
make docker-up              # Start services
make run-dev                # Run with live reload
```

### Testing
```bash
make test                   # Run all tests
make test-unit              # Unit only
make test-integration       # Integration only
make coverage               # With coverage report
```

### Code Quality
```bash
make format                 # Auto-format code
make lint                   # Check style
make check                  # Format + lint
```

### Keycloak / Authentication
```bash
make keycloak-setup         # Configure Keycloak
make keycloak-verify        # Check setup
make keycloak-test-auth     # Test token generation
```

### Docker Management
```bash
make docker-up              # Start
make docker-down            # Stop
make docker-restart         # Restart
make docker-status          # Check status
make docker-logs            # View logs
make docker-clean           # Reset everything
make docker-rebuild         # Rebuild images
```

### Production
```bash
make run                    # Production mode
```

### Cleanup
```bash
make clean                  # Remove caches
make docker-clean           # Remove containers/volumes
```

## Combined Workflows

### Full Setup
```bash
make setup && make docker-up && make keycloak-setup && make info
```

### Test Before Commit
```bash
make format && make lint && make test && make coverage
```

### Development Session
```bash
make docker-up && make run-dev
```

### Reset Everything
```bash
make docker-clean && make clean && make setup && make docker-up
```

### Quick Auth Test
```bash
make docker-up && make keycloak-test-auth
```

## Useful Combinations

### Run specific test file
```bash
make docker-up
python -m pytest tests/unit/api/test_routes_movies.py -v
```

### Run with output
```bash
make docker-logs -f         # Follow logs
make docker-status          # Current status
```

### Dry run (preview commands)
```bash
make -n test                # Preview test commands
make -n docker-up           # Preview docker startup
```

### Parallel execution
```bash
make -j4 test               # Run tests in 4 parallel jobs
```

## Environment Variables

```bash
# Custom Python version
PYTHON=python3.11 make setup

# Custom venv name
VENV=env make setup

# Custom docker-compose
DOCKER_COMPOSE="docker compose" make docker-up
```

## Tips

- `make help` - Always show available targets
- `make info` - Check your environment
- `make -n TARGET` - Dry run (show what would run)
- `make clean install docker-up` - Chain targets
- Add to shell alias: `alias m=make`

---

**For full documentation, see: MAKEFILE_GUIDE.md**
