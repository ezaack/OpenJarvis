# OpenJarvis — Local Development & Testing Guide

A complete step-by-step guide to setting up, running, and testing OpenJarvis on your local machine. This covers both **end-user setup** (running Jarvis to use it) and **contributor setup** (running tests, making changes).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Install Python Dependencies](#3-install-python-dependencies)
4. [Build the Rust Extension (Optional)](#4-build-the-rust-extension-optional)
5. [Install and Configure Ollama](#5-install-and-configure-ollama)
6. [Pull a Model](#6-pull-a-model)
7. [Initialize OpenJarvis Configuration](#7-initialize-openjarvis-configuration)
8. [Verify Your Setup with `jarvis doctor`](#8-verify-your-setup-with-jarvis-doctor)
9. [Run Your First Query](#9-run-your-first-query)
10. [Start the API Server](#10-start-the-api-server)
11. [Run the Browser App (Frontend)](#11-run-the-browser-app-frontend)
12. [Run the Test Suite](#12-run-the-test-suite)
13. [Running Specific Test Categories](#13-running-specific-test-categories)
14. [Troubleshooting Common Issues](#14-troubleshooting-common-issues)

---

## 1. Prerequisites

| Requirement | Minimum Version | Check Command |
|---|---|---|
| **Python** | 3.10 – 3.13 | `python --version` |
| **Git** | Any modern version | `git --version` |
| **uv** (Python package manager) | Latest | `uv --version` |
| **Rust** (optional, for native extension) | 1.70+ | `rustc --version` |
| **Ollama** (recommended inference engine) | Latest | `ollama --version` |
| **Node.js** (optional, for frontend) | 18+ | `node --version` |
| **npm** (optional, for frontend) | 9+ | `npm --version` |

### Installing `uv`

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installing Rust (if building the native extension)

```bash
# Windows: download from https://rustup.rs/
# macOS / Linux:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Installing Ollama

```bash
# Windows: download from https://ollama.com/download
# macOS: download from https://ollama.com/download
# Linux:
curl -fsSL https://ollama.com/install.sh | sh
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/open-jarvis/OpenJarvis.git
cd OpenJarvis
```

All subsequent commands assume you are in the `OpenJarvis/` root directory.

---

## 3. Install Python Dependencies

The project uses `uv` (not `pip`) for dependency management. The `pyproject.toml` is inside `src/`.

### Minimal install (CLI only)

```bash
cd src
uv sync
cd ..
```

This creates a virtual environment (`.venv`) inside `src/` and installs the core dependencies.

### Full install (with dev, server, and inference extras)

```bash
cd src
uv sync --extra dev --extra server --extra inference-cloud
cd ..
```

| Common extras | What they add |
|---|---|
| `dev` | pytest, pytest-asyncio, pytest-cov, ruff, pre-commit, maturin |
| `server` | FastAPI, uvicorn, pydantic, python-multipart |
| `inference-cloud` | openai, anthropic SDKs |
| `inference-ollama` | (built-in, no extra needed) |
| `memory-faiss` | FAISS vector store + sentence-transformers |
| `desktop` | server extras + faster-whisper |

### Activate the virtual environment

```bash
# macOS / Linux / WSL
source src/.venv/bin/activate

# Windows (PowerShell)
.\src\.venv\Scripts\Activate.ps1

# Windows (cmd)
.\src\.venv\Scripts\activate.bat
```

> **Note:** Every `jarvis ...` command below can also be prefixed with `uv run` from the `src/` directory instead of activating the venv.

---

## 4. Build the Rust Extension (Optional)

The Rust extension (`openjarvis_rust`) provides the `jarvis memory index` and `jarvis memory search` commands. It is **optional** — everything else works without it.

```bash
# From the repo root
cd src
uv run maturin develop -m rust/crates/openjarvis-python/Cargo.toml
cd ..
```

If you're on Python 3.14, set this environment variable first:
```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
```

Verify it installed:
```bash
uv run python -c "import openjarvis_rust; print(openjarvis_rust.__file__)"
```

---

## 5. Install and Configure Ollama

### Start the Ollama service

```bash
# Start in background (macOS / Linux)
ollama serve &

# Windows: Ollama runs as a system service after installation
# Check it's running:
ollama list
```

Ollama listens on `http://localhost:11434` by default.

### Verify connectivity

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response listing available models (may be empty).

---

## 6. Pull a Model

Pick one based on your hardware:

| Hardware | Recommended Model | RAM/VRAM |
|---|---|---|
| Any machine (CPU) | `qwen3.5:0.6b` or `qwen3.5:4b` | ~1-4 GB |
| 8 GB+ GPU | `qwen3.5:9b` | ~6 GB |
| 24 GB+ GPU | `qwen3.5:35b` or `llama3.1:8b` | ~8-20 GB |
| Apple Silicon 16 GB+ | `qwen3.5:9b` | ~6 GB unified |

```bash
# Pull a starter model (lightweight, runs on CPU)
ollama pull qwen3.5:4b

# Or a better model if you have GPU
ollama pull qwen3.5:9b

# List installed models
ollama list
```

---

## 7. Initialize OpenJarvis Configuration

### Auto-detect and generate config

```bash
# Activate venv first, then:
jarvis init
```

This runs hardware detection and writes `~/.openjarvis/config.toml` with sensible defaults.

### Use a preset config (recommended for first-time users)

```bash
# Lightweight chat, no tools (simplest setup)
cp src/configs/openjarvis/examples/chat-simple.toml ~/.openjarvis/config.toml

# Or generate via CLI:
jarvis init --preset chat-simple
```

Other presets available:

```bash
jarvis init --preset code-assistant    # Agent with code execution, file I/O, shell
jarvis init --preset deep-research     # Multi-hop research across indexed docs
jarvis init --preset scheduled-monitor # Persistent agent on a schedule
```

### Manually edit config (optional)

The config is at `~/.openjarvis/config.toml`. Key sections:

```toml
[engine]
default = "ollama"                     # or "vllm", "llamacpp", "mlx", etc.

[intelligence]
default_model = "qwen3.5:4b"           # must match an Ollama model you pulled

[agent]
default_agent = "simple"               # "simple", "orchestrator", "operative", etc.

[server]
host = "0.0.0.0"
port = 8000
```

---

## 8. Verify Your Setup with `jarvis doctor`

```bash
jarvis doctor
```

This runs diagnostic checks and prints a table like:

```
╭──────────────┬──────────┬──────────────────────────────────╮
│ Check        │ Status   │ Message                          │
├──────────────┼──────────┼──────────────────────────────────┤
│ Python ver   │ ok       │ 3.12.4                           │
│ Config file  │ ok       │ C:\Users\you\.openjarvis\config  │
│ Config parse │ ok       │ Config loaded                    │
│ Engine       │ ok       │ ollama – http://localhost:11434  │
│ Rust ext     │ warn     │ Skipped (not built)              │
╰──────────────┴──────────┴──────────────────────────────────╯
```

All checks should be **ok** or **warn** (warnings are acceptable). **fail** means something is wrong.

---

## 9. Run Your First Query

### Via CLI

```bash
# Simple question
jarvis ask "What is the capital of France?"

# With a specific model
jarvis ask -m qwen3.5:4b "Explain quantum computing in simple terms"

# With an agent and tools
jarvis ask --agent orchestrator --tools calculator,web_search "What is 15% of 340?"

# JSON output
jarvis ask --json "What is 2+2?"

# Stream the response token by token
jarvis ask "Write a haiku about AI"

# Interactive chat session
jarvis chat
```

### Via Python SDK

```python
from openjarvis import Jarvis

with Jarvis() as j:
    response = j.ask("Hello! What can you do?")
    print(response)
```

### Via curl (when server is running)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:4b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 10. Start the API Server

The API server provides an OpenAI-compatible REST API.

```bash
# Default port
jarvis serve

# Custom port
jarvis serve --port 9090

# With a specific model
jarvis serve --model qwen3.5:4b

# Enable verbose logging
jarvis serve --verbose
```

The server starts on `http://localhost:8000` (or your custom port) and exposes:

| Endpoint | Description |
|---|---|
| `GET /v1/models` | List available models |
| `POST /v1/chat/completions` | Chat completion (OpenAI-compatible) |
| `POST /v1/chat/completions?stream=true` | Streaming chat completion |
| `GET /health` | Health check |
| `GET /docs` | Swagger UI (if FastAPI extras installed) |

---

## 11. Run the Browser App (Frontend)

### Quickstart (one command)

```bash
./scripts/quickstart.sh
```

This installs all dependencies, starts the backend, and launches the frontend at `http://localhost:5173`.

### Manual frontend setup

```bash
# Step 1 — Start the backend server (in one terminal)
cd src
uv run jarvis serve --port 8000

# Step 2 — Install frontend dependencies (in another terminal)
cd src/frontend
npm install

# Step 3 — Start the frontend dev server
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 12. Run the Test Suite

### Prerequisites

Make sure dev dependencies are installed:

```bash
cd src
uv sync --extra dev
```

### Run all tests

```bash
cd src
uv run pytest tests/ -v
```

### Run with coverage

```bash
uv run pytest tests/ --cov=openjarvis --cov-report=term-missing -v
```

### Run in parallel (faster)

```bash
uv run pytest tests/ -n auto -v
```

### Run a specific test file

```bash
uv run pytest tests/test_query_orchestrator.py -v
uv run pytest tests/test_vision.py -v
uv run pytest tests/test_digest_integration.py -v
```

### Run a specific test function

```bash
uv run pytest tests/test_query_orchestrator.py::test_simple_query -v
```

---

## 13. Running Specific Test Categories

### Core tests (no external dependencies)

```bash
uv run pytest tests/core/ -v
```

### Engine tests (require Ollama or other engine running)

```bash
uv run pytest tests/engine/ -v
```

### Agent tests

```bash
uv run pytest tests/agents/ -v
```

### CLI tests

```bash
uv run pytest tests/cli/ -v
```

### Server / API tests

```bash
uv run pytest tests/server/ -v
```

### Memory / RAG tests

```bash
uv run pytest tests/memory/ -v
```

### Tool tests

```bash
uv run pytest tests/tools/ -v
```

### SDK tests

```bash
uv run pytest tests/sdk/ -v
```

### Integration tests (require full stack)

```bash
uv run pytest tests/integration/ -v
```

### Benchmark tests

```bash
uv run pytest tests/bench/ -v
```

### Run tests with a specific marker

```bash
# View available markers
uv run pytest tests/ --markers

# Run only slow tests
uv run pytest tests/ -m slow -v

# Run only tests that don't require external services
uv run pytest tests/ -m "not external" -v
```

### Run linting / formatting checks

```bash
# Ruff linting
uv run ruff check src/

# Ruff formatting
uv run ruff format --check src/

# Auto-fix lint issues
uv run ruff check --fix src/
```

---

## 14. Troubleshooting Common Issues

### `jarvis: command not found`

The venv is not activated. Either:
```bash
# Option A: activate the venv
source src/.venv/bin/activate    # macOS/Linux
.\src\.venv\Scripts\Activate.ps1 # Windows

# Option B: use uv run
cd src && uv run jarvis --version
```

### `ModuleNotFoundError: No module named 'openjarvis_rust'`

The Rust extension is not built. This is optional — most features work without it. If you need memory indexing:
```bash
cd src && uv run maturin develop -m rust/crates/openjarvis-python/Cargo.toml
```

### Engine connection errors (`EngineConnectionError`)

Ollama is not running or not reachable:
```bash
# Check if Ollama is running
ollama list

# Start it
ollama serve &

# Verify connectivity
curl http://localhost:11434/api/tags
```

### Model not found

The model specified in config hasn't been pulled:
```bash
# Pull the model
ollama pull qwen3.5:4b

# Or check what models you have
ollama list
```

### Config file errors

```bash
# Regenerate config
jarvis init --force

# Or start fresh
rm ~/.openjarvis/config.toml
jarvis init
```

### Port already in use

```bash
# Use a different port
jarvis serve --port 9090

# Or find and kill the process using the port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS / Linux:
lsof -i :8000
kill -9 <PID>
```

### Tests fail with `EngineConnectionError`

Tests that require an engine (Ollama) will fail if it's not running. Either:
- Start Ollama: `ollama serve &`
- Run only non-engine tests: `uv run pytest tests/ -m "not engine" -v`
- Run a specific test module that doesn't need an engine: `uv run pytest tests/core/ -v`

### `uv sync` fails

```bash
# Make sure you're in the `src/` directory
cd src

# Ensure Python 3.10-3.13 is active
python --version

# Try a clean sync
uv sync --reinstall
```

---

## Quick Reference: Common Commands

```bash
# Install everything
cd OpenJarvis/src && uv sync --extra dev --extra server

# Start Ollama (if not running)
ollama serve &

# Pull a model
ollama pull qwen3.5:4b

# Init config
jarvis init --preset chat-simple

# Verify
jarvis doctor

# Ask a question
jarvis ask "Hello!"

# Start the API server
jarvis serve

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check src/
```
