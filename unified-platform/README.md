# Unified Multi-Agent Platform

A unified backend for managing 81+ configurable agents using FastAPI.

## Project Structure
- `src/`: Backend source code.
- `config/`: Agent and system configurations (YAML).
- `scripts/`: Utility scripts (launcher, generator).
- `tests/`: Automated test suite.
- `logs/`: Service logs.
- `data/`: SQLite persistence storage.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate agent configuration:
   ```bash
   python scripts/generate_agents.py
   ```
3. Configure environment:
   Create a `.env` file based on the template.

## Running the Platform
Use the launcher to start the backend with auto-restart:
```bash
python scripts/launcher.py
```

## API Endpoints
- `GET /health`: System health status.
- `GET /api/v1/agents`: List all 81 agents.
- `GET /api/v1/agents/{id}`: Get specific agent details.
