# AgentForge

Production-oriented AI agent framework built with Python, FastAPI, Ollama, and SQLite.

AgentForge demonstrates a practical agent architecture where an LLM plans actions, selects registered tools, executes them, and maintains persistent conversation memory.

## Architecture

```text
Client
  |
  v
FastAPI API
  |
  v
Agent
  +--> Planner --> Ollama / Qwen3
  |
  +--> Tool Registry
  |      +--> Calculator
  |      +--> Current Datetime
  |
  +--> Executor
  |
  +--> SQLite Memory
```

## Features

- LLM-driven agent planning
- Tool selection and execution
- Extensible tool registry
- Calculator tool
- Current datetime tool
- Persistent SQLite conversation memory
- FastAPI API
- Local Ollama LLM integration
- Qwen3:4b support
- Bounded agent execution
- Runtime safety limits
- Configuration management
- Automated testing
- Ruff linting
- Python compilation verification

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| FastAPI | API layer |
| Pydantic | Data validation and configuration |
| Ollama | Local LLM inference |
| Qwen3:4b | Verified development model |
| SQLite | Persistent memory |
| pytest | Automated testing |
| Ruff | Linting and code quality |

## Project Structure

```text
AgentForge/
├── app/
│   ├── agent/
│   │   ├── agent.py
│   │   └── planner.py
│   ├── api/
│   ├── core/
│   ├── llm/
│   ├── memory/
│   └── tools/
│       ├── calculator.py
│       ├── datetime.py
│       └── registry.py
├── tests/
├── live_test.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## How It Works

AgentForge follows a simple agent execution loop:

```text
1. User sends a request
        |
        v
2. Agent receives the request
        |
        v
3. Planner asks the LLM what action is required
        |
        v
4. Planner selects a registered tool when necessary
        |
        v
5. Executor runs the selected tool
        |
        v
6. Result is returned to the agent
        |
        v
7. Agent produces the final response
        |
        v
8. Conversation is persisted in SQLite memory
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/syed-ashar-raza/AgentForge.git
cd AgentForge
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -e .
```

### 5. Configure Environment Variables

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

Review `.env` and adjust configuration if required.

## Ollama

AgentForge uses Ollama for local LLM inference.

The verified development model is:

```text
qwen3:4b
```

Make sure Ollama is installed and running, then make the model available locally.

The application communicates with the local Ollama service rather than requiring a hosted LLM API.

## Run the API

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Testing

Run the automated test suite:

```bash
pytest -q
```

Run Ruff:

```bash
ruff check .
```

Run Python compilation checks:

```bash
python -m compileall -q app tests
```

## Verification

The current implementation has been verified through:

- 11 automated tests passing
- Ruff validation passing
- Python compilation passing
- Live Ollama connectivity
- Qwen3:4b availability
- End-to-end Agent execution
- Successful tool selection
- Successful calculator execution
- Persistent SQLite memory functionality

### Example Agent Execution

**Input:**

```text
What is 25 multiplied by 4?
```

**Agent execution:**

```text
Planner
   |
   v
calculator("25 * 4")
   |
   v
100
```

**Final response:**

```text
25 multiplied by 4 equals 100.
```

## Core Components

### Agent

Coordinates the complete agent execution lifecycle.

Responsibilities include:

- Receiving user requests
- Managing execution steps
- Coordinating planning
- Executing selected tools
- Producing final responses
- Persisting conversation context

### Planner

Uses the configured LLM to determine the next action.

The planner can identify when a tool is required and provide the arguments needed for execution.

### Tool Registry

Provides a centralized mechanism for registering and discovering tools.

Current tools include:

- Calculator
- Current datetime

The registry is designed so additional tools can be added without rewriting the core agent loop.

### Executor

Responsible for executing selected tools and returning their results to the agent.

Keeping execution separate from planning allows the system to maintain a clear boundary between:

```text
Decision → Execution
```

### Memory

AgentForge uses SQLite for persistent conversation memory.

Memory provides:

- Conversation persistence
- Context retrieval
- Bounded memory usage
- Simple local storage
- No external database dependency

### LLM Client

The LLM layer communicates with Ollama and keeps model communication separate from the rest of the application.

This makes the architecture easier to extend to additional model providers in the future.

## Runtime Safety

AgentForge includes bounded execution controls to prevent uncontrolled agent loops.

Current runtime limits include:

- Maximum agent steps
- Maximum tool executions
- Maximum stored memory items

These limits provide basic protection against runaway execution while keeping the MVP architecture lightweight.

## Design Principles

AgentForge is intentionally structured around clear separation of responsibilities:

```text
API
 |
 v
Agent
 |
 +--> Planner
 |
 +--> Tool Registry
 |       |
 |       +--> Tools
 |
 +--> Executor
 |
 +--> Memory
 |
 +--> LLM Client
```

Key design principles:

- Separation of concerns
- Explicit tool registration
- Bounded execution
- Persistent state
- Local-first inference
- Testable components
- Configuration-driven behavior
- Small, maintainable modules

## API Layer

FastAPI provides the HTTP interface for interacting with the agent.

The API layer is intentionally separated from the underlying agent implementation so that the agent can be tested and evolved independently of HTTP concerns.

## Why AgentForge?

AgentForge focuses on the foundational engineering problems involved in building practical AI agents:

- LLM-based planning
- Tool calling
- Deterministic tool execution
- Persistent memory
- Runtime controls
- API integration
- Local model inference
- Modular architecture
- Automated verification

The project is intentionally compact while demonstrating the core building blocks required for larger agentic systems.

## Current Scope

The current MVP focuses on the foundational agent execution loop and supporting infrastructure.

Current capabilities include:

- Agent planning
- Local LLM inference
- Tool discovery
- Tool execution
- Persistent memory
- FastAPI integration
- Configuration
- Runtime limits
- Automated testing

## Future Extensions

Potential future extensions include:

- Additional production-grade tools
- Structured tool schemas
- More advanced planning strategies
- Multi-step workflows
- Agent observability
- Authentication and authorization
- Richer memory strategies
- Evaluation and tracing
- Deployment infrastructure
- Additional LLM providers
- Production monitoring

These are intentionally outside the current MVP scope.

## Project Status

**Status: MVP complete**

The current implementation has passed automated and live verification for its implemented functionality.

## License

No open-source license has been applied yet.
