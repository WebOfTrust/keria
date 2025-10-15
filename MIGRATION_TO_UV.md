# KERIA Migration to UV

This document outlines the migration of the KERIA project from setuptools/pip/virtualenv to uv, a fast Python package manager and project manager.

## Migration Summary

### ✅ Completed Changes

1. **Created pyproject.toml**: 
   - Converted all setup.py configuration to modern pyproject.toml format
   - Configured hatchling as the build backend
   - Set up project metadata, dependencies, and entry points
   - Added uv-specific configuration sections

2. **Generated uv.lock**:
   - Created a comprehensive lock file with all dependencies pinned
   - Ensures reproducible builds across environments

3. **Updated Makefile**:
   - Replaced `python setup.py sdist` with `uv build`
   - Added new development targets:
     - `make install` - Install dependencies
     - `make install-dev` - Install with dev dependencies
     - `make test` - Run tests
     - `make test-coverage` - Run tests with coverage
     - `make lint` - Run linting
     - `make lint-fix` - Auto-fix linting issues
     - `make format` - Format code
     - `make clean` - Clean build artifacts

4. **Updated README.md**:
   - Added uv installation instructions
   - Provided both uv (recommended) and traditional pip workflows
   - Updated development command documentation

5. **Updated GitHub Actions**:
   - Modified `.github/workflows/python-app-ci.yml` to use uv
   - Added astral-sh/setup-uv@v3 action
   - Replaced pip commands with uv equivalents

6. **Updated Dockerfile**:
   - Modified `images/keria.dockerfile` to use uv for dependency management
   - Uses official uv Docker image for installation
   - Optimized build process with uv sync

7. **Removed Legacy Files**:
   - Deleted `setup.py`
   - Deleted `requirements.txt`

### New Development Workflow

#### Quick Start
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repository-url>
cd keria
uv sync --all-extras

# Run the application
uv run keria start --config-dir scripts --config-file demo-witness-oobis
```

#### Development Commands
```bash
# Install dependencies
uv sync                  # Production dependencies
uv sync --all-extras     # Include dev/test dependencies

# Run tests
uv run pytest tests/
make test
make test-coverage

# Linting and formatting
uv run ruff check src tests
make lint
make lint-fix
make format

# Build package
uv build
make build-wheel

# Run application
uv run keria --help
```

### Benefits of the Migration

1. **Faster Operations**:
   - uv is significantly faster than pip for package resolution and installation
   - Lock file ensures quick, reproducible environment setup

2. **Better Dependency Management**:
   - Comprehensive lock file with exact versions and hashes
   - Clear separation of production and development dependencies

3. **Modern Python Packaging**:
   - Uses pyproject.toml standard (PEP 518/621)
   - Better integration with modern Python tooling

4. **Improved CI/CD**:
   - Faster GitHub Actions builds
   - More reliable dependency caching

5. **Enhanced Developer Experience**:
   - Simplified commands (`uv sync` vs multiple pip/venv commands)
   - Better error messages and conflict resolution

### Verification

The migration has been tested and verified:
- ✅ Package builds successfully (`uv build`)
- ✅ Application runs correctly (`uv run keria --help`)
- ✅ Tests execute properly (`uv run pytest`)
- ✅ Dependencies resolve without conflicts
- ✅ Docker build process updated

### Backward Compatibility

For users who prefer the traditional pip workflow, the README includes alternative instructions using pip and virtual environments. The pyproject.toml format is fully compatible with pip.

### Next Steps

1. Update any remaining documentation that references setup.py or requirements.txt
2. Consider updating the version in `src/keria/__init__.py` to match pyproject.toml
3. Test the updated Docker build process
4. Consider adding pre-commit hooks for ruff formatting/linting