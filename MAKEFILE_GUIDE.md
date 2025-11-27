# Makefile Guide - Cross-Platform Development

This Makefile provides a unified interface for development across **Windows**, **macOS**, and **Linux**.

## Platform Support

### Windows
- **Option 1 (Recommended)**: Use **Git Bash** or **WSL2** (Windows Subsystem for Linux)
  - Git Bash: Included with Git for Windows
  - WSL2: Native Linux experience on Windows

- **Option 2**: Use **GNU Make for Windows**
  - Download from: http://gnuwin32.sourceforge.net/packages/make.htm
  - Or use Chocolatey: `choco install make`

### macOS
- **Included**: macOS comes with `make` pre-installed
- Verify: `make --version`
- If needed: `brew install make`

### Linux
- **Install**: `sudo apt-get install build-essential` (Debian/Ubuntu)
- **Or**: `sudo yum install make` (RHEL/CentOS)
- **Or**: `sudo pacman -S make` (Arch)

---

## Quick Start

### 1. Initial Setup (All Platforms)
```bash
make setup           # Create venv and install dependencies
make info            # Verify environment
```

### 2. Start Docker Services
```bash
make docker-up       # Start all services
make docker-status   # Check status
```

### 3. Run Tests
```bash
make test           # Run all tests
make test-unit      # Run unit tests only
make coverage       # Run tests with coverage report
```

### 4. Run Application
```bash
make run-dev        # Run with hot reload (development)
make run            # Run production mode
```

---

## Available Targets

### Setup & Dependencies
| Target | Description |
|--------|-------------|
| `setup` | Create virtual environment and install dependencies |
| `install` | Install/update dependencies |
| `freeze` | Generate requirements.txt from current environment |
| `clean` | Remove caches, venv, and build artifacts |

### Code Quality
| Target | Description |
|--------|-------------|
| `format` | Format code with black and isort |
| `lint` | Run linting checks (pylint, flake8) |
| `check` | Run all quality checks |

### Testing
| Target | Description |
|--------|-------------|
| `test` | Run all tests (unit + integration) |
| `test-unit` | Run unit tests only |
| `test-integration` | Run integration tests only |
| `coverage` | Generate coverage report (HTML) |

### Docker
| Target | Description |
|--------|-------------|
| `docker-up` | Start all services |
| `docker-down` | Stop all services |
| `docker-restart` | Restart all services |
| `docker-clean` | Remove containers and volumes |
| `docker-logs` | View service logs (follow mode) |
| `docker-status` | Show running containers |
| `docker-rebuild` | Rebuild all images |

### Application
| Target | Description |
|--------|-------------|
| `run` | Run FastAPI (production mode) |
| `run-dev` | Run FastAPI with hot reload |

### Keycloak
| Target | Description |
|--------|-------------|
| `keycloak-setup` | Initial Keycloak configuration |
| `keycloak-verify` | Verify Keycloak setup |
| `keycloak-test-auth` | Test authentication flows |

### Utilities
| Target | Description |
|--------|-------------|
| `info` | Display environment information |
| `check-python` | Verify Python installation |
| `check-docker` | Verify Docker installation |
| `help` | Show help message |

---

## Common Workflows

### Development Setup
```bash
make setup           # Initial setup
make docker-up       # Start services
make keycloak-setup  # Configure Keycloak
make run-dev         # Run with hot reload
```

### Testing Workflow
```bash
make docker-up           # Start services
make test-unit           # Run unit tests
make test-integration    # Run integration tests
make coverage            # Generate coverage report
```

### Before Commit
```bash
make format          # Format code
make lint            # Check code quality
make test            # Run all tests
```

### Troubleshooting
```bash
make info            # Check environment
make docker-status   # Check running services
make docker-logs     # View service logs
make clean           # Clean up and reset
```

---

## Platform-Specific Notes

### Windows + Git Bash
```bash
# Git Bash automatically finds Python and Docker
make setup
make docker-up
```

### Windows + WSL2
```bash
# Inside WSL2 terminal
make setup
make docker-up
# Docker commands work via Docker Desktop
```

### Windows + Native CMD/PowerShell
If using native PowerShell, you need GNU Make:
```powershell
# Install via Chocolatey
choco install make

# Then use in any terminal
make setup
```

### macOS / Linux
```bash
# Make is pre-installed
make setup
make docker-up
```

---

## Environment Variables

You can customize behavior with environment variables:

```bash
# Use custom Python version
PYTHON=python3.11 make setup

# Use custom virtual environment name
VENV=myenv make setup

# Use custom docker-compose command
DOCKER_COMPOSE="docker compose" make docker-up
```

---

## Troubleshooting

### "make: command not found"
**Solution**: Install GNU Make for your platform (see Platform Support above)

### "Python not found"
**Solution**: 
```bash
# Install Python 3.11 or later
# Verify: python --version

# Or specify explicit path:
PYTHON=/usr/bin/python3.11 make setup
```

### "Docker not found"
**Solution**:
```bash
# Install Docker Desktop or Docker CLI
# Verify: docker --version

make check-docker  # Detailed diagnostics
```

### "Virtual environment not activated"
**Solution**: The Makefile handles this automatically
```bash
make install  # Installs into venv automatically
```

### Tests won't run
**Solution**:
```bash
make docker-status   # Verify services are running
make docker-up       # Start if not running
make test            # Retry
```

---

## Tips & Tricks

### Run Make from anywhere
```bash
# Set alias (add to ~/.bashrc or ~/.zshrc)
alias m='make -C /path/to/movie_api'

# Then use:
m setup
m docker-up
```

### Combine targets
```bash
make clean install docker-up keycloak-setup run-dev
```

### View available targets
```bash
make help
make info
```

### Dry run (see what would execute)
```bash
make -n test  # Shows commands without executing
```

### Parallel execution
```bash
make -j4 test  # Run tests in parallel (4 jobs)
```

---

## Integration with IDEs

### VS Code
Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "make",
      "args": ["test"],
      "group": {
        "kind": "test",
        "isDefault": true
      }
    },
    {
      "label": "Run App",
      "type": "shell",
      "command": "make",
      "args": ["run-dev"],
      "isBackground": true
    }
  ]
}
```

Then use `Ctrl+Shift+B` to run tasks.

### PyCharm
1. Go to Settings → Tools → Python Integrated Tools
2. Set default test runner to pytest
3. Add run configuration for `make run-dev`

---

## Next Steps

1. **Setup**: `make setup`
2. **Verify**: `make info`
3. **Start**: `make docker-up`
4. **Test**: `make test`
5. **Run**: `make run-dev`

For help anytime: `make help`
