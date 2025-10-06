# Code Quality Tools

This directory contains scripts and configuration for maintaining code quality in the fullstack-ecosystem project.

## 🛠️ Tools Overview

### Pre-commit Hooks

- **Pre-commit**: Automated code quality checks that run before each commit
- **Git hooks**: Automated triggers for format, lint, type-check, and fast tests

### Type Checking Tools

- **mypy**: Static type checker for Python with gradual typing support

### Linting Tools

- **Ruff**: Modern, fast Python linter with auto-fix capabilities
- **Flake8**: Traditional Python linter for comprehensive style checking

### Formatting Tools

- **Black**: Opinionated Python code formatter
- **Ruff Format**: Built-in formatter that's compatible with Black

## 📁 Configuration Files

### `pyproject.toml`

Main configuration file containing settings for:

- **Pre-commit**: Hook configuration and version management
- **mypy**: Comprehensive type checking configuration with strict settings
- **Black**: Line length, target Python versions, exclusions
- **Ruff**: Comprehensive linting rules, complexity settings, import sorting

### `.pre-commit-config.yaml`

Pre-commit configuration defining automated hooks for:

- Code formatting (black + ruff format)
- Code linting (ruff + flake8 + mypy)
- Type checking (mypy with baseline approach)
- Fast test execution (unit tests)
- File validation (trailing whitespace, yaml, json, etc.)
- Security scanning (bandit)

### `.flake8`

Flake8-specific configuration with:

- Line length and complexity limits
- Ignored error codes for Black compatibility
- File exclusions and per-file ignores

## 🚀 Usage

### Quick Start

```bash
# Run everything (format + lint + type check)
make quality

# Pre-commit hook management
make pre-commit-install  # Install hooks (one-time setup)
make pre-commit-run      # Run hooks on all files
make pre-commit-update   # Update hook versions

# Individual quality commands
make format     # Format code
make lint       # Lint code  
make type-check # Type check code
make type-baseline # Generate mypy baseline
```

### 🎯 Pre-commit Hooks (Recommended)

Pre-commit hooks automatically run quality checks before each commit:

```bash
# One-time setup
make pre-commit-install
# OR
python scripts/setup_pre_commit.py

# Hooks now run automatically on git commit
git add .
git commit -m "Your changes"  # Hooks run automatically

# Manual execution
make pre-commit-run
# OR  
pre-commit run --all-files

# Skip hooks when needed (emergency commits)
git commit --no-verify -m "Emergency fix"
```

### Cross-Platform Scripts

#### Python Scripts (Universal)

```bash
# Format code
python scripts/format.py

# Lint code  
python scripts/lint.py

# Type check code
python scripts/type_check.py

# Generate mypy baseline
python scripts/type_check.py --baseline

# Run comprehensive quality check (format + lint + type)
python scripts/quality.py
```

#### PowerShell Scripts (Windows)

```powershell
# Format code
.\scripts\format.ps1

# Lint code
.\scripts\lint.ps1

# Type check code
.\scripts\type_check.ps1

# Generate mypy baseline
.\scripts\type_check.ps1 -Baseline

# Run comprehensive quality check (format + lint + type)
.\scripts\quality.ps1

# Run with auto-fix
.\scripts\quality.ps1 -Fix

# Get help
.\scripts\quality.ps1 -Help
```

### Advanced Usage

#### Custom Targets

```bash
# Format specific directories
python scripts/format.py autogen tests

# Lint specific files
python scripts/lint.py main.py config.py

# Type check specific modules
python scripts/type_check.py scripts/ tests/
```

#### PowerShell with Options

```powershell
# Format only autogen directory
.\scripts\format.ps1 -Targets autogen

# Lint with auto-fix
.\scripts\lint.ps1 -Fix

# Skip type checking, only format and lint
.\scripts\quality.ps1 -SkipType

# Skip formatting, only lint and type check
.\scripts\quality.ps1 -SkipFormat
```

## 🔧 Tool-Specific Commands

### Pre-commit

```bash
# Install hooks (one-time setup)
pre-commit install
pre-commit install --hook-type pre-push

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run format-code
pre-commit run lint-code
pre-commit run type-check

# Update hook versions  
pre-commit autoupdate
```

### mypy

```bash
# Type check with baseline approach
python scripts/type_check.py

# Generate baseline report
python scripts/type_check.py --baseline

# Direct mypy commands
mypy scripts/
mypy autogen/backend/
mypy --strict src/
```

### Ruff

```bash
# Check all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Show all available rules
ruff linter
```

### Black

```bash
# Format all Python files
black .

# Check without making changes
black --check .

# Show diff of changes
black --diff .
```

### Flake8

```bash
# Lint all files
flake8 .

# Show statistics
flake8 --statistics .

# Count errors by type
flake8 --count .
```

## 📋 Configuration Details

### Ruff Rules

- **E, W**: pycodestyle errors and warnings
- **F**: pyflakes (unused imports, undefined names)
- **I**: isort (import sorting)
- **B**: flake8-bugbear (likely bugs)
- **C4**: flake8-comprehensions (list/dict comprehensions)
- **UP**: pyupgrade (modern Python syntax)
- **ARG**: flake8-unused-arguments
- **C90**: mccabe complexity
- **T20**: flake8-print (print statements)
- **SIM**: flake8-simplify
- **ICN**: flake8-import-conventions

### mypy Configuration

- **Python target**: 3.10+ with comprehensive type checking
- **Strict mode**: Enabled for most modules with gradual strictness
- **Per-module overrides**: Different strictness levels for different areas
  - `scripts/*`: Allows untyped calls and definitions (gradual adoption)
  - `tests/*`: Relaxed strictness for test files
  - Core modules: Full strict typing enabled
- **Baseline approach**: Uses `mypy-baseline.txt` for gradual improvement

### Ignored mypy Issues

- Issues documented in `mypy-baseline.txt` are temporarily ignored
- New code must pass strict type checking
- Baseline can be regenerated with `make type-baseline`

### Ignored Ruff Rules

- **E501**: Line too long (handled by Black)
- **B008**: Function calls in argument defaults
- **C901**: Too complex (McCabe)
- **T201**: Print found (allowed in some contexts)

### File Exclusions

- `.venv`, `venv`: Virtual environments
- `__pycache__`: Python cache directories
- `.git`: Version control
- `build`, `dist`: Build artifacts
- `migrations`: Database migrations
- `node_modules`: Node.js dependencies

## 🎯 Best Practices

### Pre-commit Workflow (Recommended)

**Automated Approach:**

1. **Install hooks** (one-time): `make pre-commit-install`
2. **Work normally**: Make your changes
3. **Commit**: `git commit` (hooks run automatically)
4. **Fix issues**: If hooks fail, fix the reported issues and commit again

**Manual Approach:**

1. **Format** your code: `make format`
2. **Lint** your code: `make lint`  
3. **Type check** your code: `make type-check`
4. **Fix** any remaining issues manually
5. **Commit** your changes

### Pre-commit Hook Details

**On every commit (pre-commit stage):**

- Code formatting (black + ruff format) - auto-fixes
- Code linting (ruff + flake8) - reports issues
- Type checking (mypy) - reports type issues  
- Fast tests (unit tests only) - validates core functionality
- File validation (whitespace, yaml, json) - auto-fixes

**On git push (pre-push stage):**

- Full quality check (format + lint + type + all tests)
- Documentation linting (markdownlint)

### IDE Integration

#### VS Code

Add to `.vscode/settings.json`:

```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm

1. Install Black plugin
2. Configure Ruff as external tool
3. Configure mypy as external tool
4. Set up file watchers for auto-formatting

### CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Code Quality
  run: |
    python scripts/quality.py
```

## 🐛 Troubleshooting

### Common Issues

#### Pre-commit hooks not running

```bash
# Reinstall hooks
make pre-commit-install

# Check hook installation
pre-commit install --help
```

#### "Command not found"

```bash
# Install missing tools
pip install ruff black flake8 mypy types-requests types-PyYAML pre-commit
```

#### Pre-commit fails with encoding errors

```bash
# Set UTF-8 encoding (Windows)
set PYTHONIOENCODING=utf-8
git commit

# Or use our wrapper script which handles this
python scripts/setup_pre_commit.py
```

#### "Permission denied" (PowerShell)

```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### "Module not found"

```bash
# Ensure you're in the project root
cd /path/to/fullstack-ecosystem

# Check Python path
python -c "import sys; print(sys.path)"
```

### Performance Tips

- **Ruff** is significantly faster than Flake8 for large codebases
- Use **Ruff format** instead of Black for better performance
- Configure IDE to run formatters on save for immediate feedback

### Debugging

```bash
# Verbose output
ruff check --verbose .

# Show all violations
flake8 --show-source .

# Black diff without changes
black --diff --check .

# mypy with verbose output
mypy --verbose scripts/

# Show mypy configuration
mypy --config-file pyproject.toml --show-config scripts/
```

## 📊 Quality Metrics

The scripts provide detailed feedback including:

- **Success/failure status** for each tool
- **Error counts** and types  
- **Type checking results** with baseline tracking
- **Suggestions** for fixing issues
- **Performance information**

## 🔄 Updating Configuration

When updating linting rules:

1. **Test changes** on a small subset first
2. **Run full quality check**: `make quality`
3. **Update documentation** if needed
4. **Inform team** of any breaking changes

## 📚 Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [Python Code Quality Tools Comparison](https://github.com/life4/awesome-python-code-formatters)
