# AgentForge

> Production-oriented AI agent framework built with Python, FastAPI, Ollama, and SQLite.

AgentForge is a local AI agent system that demonstrates how an LLM can plan actions, select registered tools, execute them through a controlled runtime, and maintain persistent conversation memory.

The project focuses on the core engineering components required to build practical agentic AI systems: planning, tool calling, deterministic execution, memory, runtime safety, API integration, testing, and local LLM inference.

---

## 🚀 Overview

AgentForge implements an end-to-end agent execution architecture:

```text
                         ┌─────────────────────┐
                         │       Client        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     FastAPI API     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       Agent         │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────────┐ ┌──────────┐
              │ Planner  │   │ Tool Registry│ │  Memory  │
              │          │   │              │ │  SQLite  │
              └────┬─────┘   └──────┬───────┘ └──────────┘
                   │                │
                   ▼                ▼
              ┌──────────┐    ┌──────────────┐
              │  Ollama  │    │   Executor   │
              │ Qwen3:4b │    │              │
              └──────────┘    └──────┬───────┘
                                      │
                              ┌───────┴────────┐
                              ▼                ▼
                        Calculator      Current Datetime

The architecture separates:

Planning — deciding whether a tool is required
Tool discovery — selecting registered capabilities
Execution — running tools through a controlled executor
Memory — persisting conversation state
LLM integration — communicating with the local model
API — exposing the agent through FastAPI
Runtime controls — bounding agent execution
✨ Key Features
LLM-driven agent planning
Tool selection and execution
Extensible tool registry
Calculator tool
Current datetime tool
Persistent SQLite conversation memory
FastAPI REST API
Local Ollama LLM integration
Qwen3:4b development model
Bounded agent execution
Maximum-step controls
Maximum-tool-execution controls
Bounded memory usage
Configuration-driven behavior
Automated pytest test suite
Ruff static analysis
Python compilation validation
Live Ollama connectivity verification
End-to-end agent execution verification
🧠 Agent Execution Pipeline

AgentForge follows a controlled execution loop:

User Request
     │
     ▼
FastAPI API
     │
     ▼
Agent
     │
     ▼
Planner
     │
     ├───────────────┐
     │               │
     ▼               ▼
No Tool Required   Tool Required
     │               │
     │               ▼
     │        Tool Registry
     │               │
     │               ▼
     │           Executor
     │               │
     │               ▼
     │        Tool Execution
     │               │
     └───────┬───────┘
             │
             ▼
       Final Response
             │
             ▼
      SQLite Memory

The separation between planning and execution provides a clear boundary:

Decision → Execution

The LLM determines the required action, while the executor is responsible for performing the selected registered tool.

🛠️ Tech Stack
Technology	Purpose
Python	Core application
FastAPI	HTTP API layer
Pydantic	Data validation and configuration
Ollama	Local LLM inference
Qwen3:4b	Verified development model
SQLite	Persistent conversation memory
pytest	Automated testing
Ruff	Static analysis and code quality
Git	Version control
📁 Project Structure
AgentForge/
│
├── app/
│   ├── agent/
│   │   ├── agent.py
│   │   └── planner.py
│   │
│   ├── api/
│   │
│   ├── core/
│   │
│   ├── llm/
│   │
│   ├── memory/
│   │
│   └── tools/
│       ├── calculator.py
│       ├── datetime.py
│       └── registry.py
│
├── tests/
│
├── live_test.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
🔄 How It Works

AgentForge processes a request through the following sequence:

1. User sends a request
        │
        ▼
2. FastAPI receives the request
        │
        ▼
3. Agent receives the request
        │
        ▼
4. Planner determines the required action
        │
        ▼
5. Registered tool is selected when required
        │
        ▼
6. Executor runs the selected tool
        │
        ▼
7. Tool result is returned
        │
        ▼
8. Agent generates the final response
        │
        ▼
9. Conversation state is persisted

This design keeps the core agent lifecycle independent from individual tool implementations.

🧩 Core Components
Agent

The Agent coordinates the complete execution lifecycle.

Responsibilities include:

Receiving user requests
Managing execution steps
Coordinating planning
Selecting registered tools
Executing selected tools
Producing final responses
Persisting conversation context
Planner

The Planner uses the configured LLM to determine the next action.

It can identify when a tool is required and provide the arguments needed for execution.

The planner is responsible for decision-making, while tool execution remains outside the LLM itself.

Tool Registry

The Tool Registry provides a centralized mechanism for registering and discovering tools.

Current tools include:

Calculator
Current datetime

The registry allows additional tools to be introduced without rewriting the core agent execution loop.

Executor

The Executor is responsible for running selected tools and returning their results to the agent.

This creates a deliberate separation:

LLM Decision
     │
     ▼
Tool Selection
     │
     ▼
Controlled Execution
     │
     ▼
Tool Result
Memory

AgentForge uses SQLite for persistent conversation memory.

Memory provides:

Conversation persistence
Context retrieval
Bounded memory usage
Simple local storage
No external database dependency
LLM Client

The LLM layer communicates with Ollama and keeps model communication separate from the rest of the application.

The current verified development model is:

qwen3:4b

The separation makes the LLM integration easier to evolve toward additional model providers.

🛡️ Runtime Safety

AgentForge includes bounded execution controls to prevent uncontrolled agent loops.

Current runtime controls include:

Maximum agent steps
Maximum tool executions
Maximum stored memory items

These controls provide basic protection against runaway execution while keeping the MVP architecture lightweight.

The runtime is intentionally bounded rather than allowing an unrestricted autonomous loop.

🔧 Current Tools
Calculator

The calculator tool provides deterministic arithmetic execution.

Example:

User:
What is 25 multiplied by 4?

Planner
   │
   ▼
calculator("25 * 4")
   │
   ▼
100

Result:

25 multiplied by 4 equals 100.
Current Datetime

The datetime tool provides access to the current datetime through a registered tool interface.

Keeping these capabilities behind the tool registry allows the agent to discover and execute tools through the same execution mechanism.

🌐 API Layer

FastAPI provides the HTTP interface for interacting with AgentForge.

The API layer is separated from the underlying agent implementation so the agent can be tested and evolved independently of HTTP concerns.

Start the development server with:

uvicorn app.main:app --reload

The API is available locally at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs
🧪 Testing

Run the automated test suite:

pytest -q

Current verified result:

11 tests passed

The test suite provides automated verification of the implemented AgentForge components.

🔍 Code Quality

AgentForge uses Ruff for static analysis.

Run:

ruff check .

Python compilation can be verified with:

python -m compileall -q app tests

Current verification includes:

Pytest:       PASSED
Ruff:         PASSED
Compilation:  PASSED
🔬 Verification

The current implementation has been verified through multiple layers.

Automated Verification
11 automated tests passing
Ruff validation passing
Python compilation passing
Runtime Verification
Live Ollama connectivity
Qwen3:4b availability
End-to-end agent execution
Successful tool selection
Successful calculator execution
Persistent SQLite memory functionality

These checks verify the implemented local MVP rather than claiming production-scale deployment performance.

🧠 Agent Architecture

AgentForge intentionally separates the major responsibilities:

                     ┌───────────────┐
                     │   FastAPI     │
                     └───────┬───────┘
                             │
                             ▼
                     ┌───────────────┐
                     │     Agent     │
                     └───────┬───────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
     ┌──────────┐      ┌─────────────┐    ┌──────────┐
     │ Planner  │      │ Tool Registry│    │  Memory  │
     └────┬─────┘      └──────┬──────┘    └──────────┘
          │                   │
          ▼                   ▼
     ┌──────────┐       ┌─────────────┐
     │  Ollama  │       │   Executor  │
     └──────────┘       └──────┬──────┘
                                │
                                ▼
                          Registered Tools

This architecture follows several practical software engineering principles:

Separation of concerns
Explicit tool registration
Controlled execution
Persistent state
Local-first inference
Testable components
Configuration-driven behavior
Small, maintainable modules
🏗️ Design Decisions
Local-First Inference

AgentForge uses Ollama for local inference rather than requiring a hosted LLM API.

This provides:

Local development
Reproducible experimentation
No dependency on paid hosted inference for the MVP
Direct control over the model runtime
Explicit Tool Execution

Tools are registered separately from the planner.

This prevents the planning layer from being responsible for arbitrary execution logic and creates a clearer interface between:

Planning
   ↓
Tool Selection
   ↓
Execution
Persistent Local Memory

SQLite provides simple persistent storage without introducing an external database dependency.

This is appropriate for the current local MVP while keeping the memory interface isolated enough to evolve later.

Bounded Runtime

Agent execution is explicitly bounded through runtime limits.

This is important for agentic systems because an unrestricted planning loop can otherwise consume excessive execution time or repeatedly invoke tools.

📦 Setup
1. Clone the Repository
git clone https://github.com/syed-ashar-raza/AgentForge.git
cd AgentForge
2. Create a Virtual Environment
python -m venv .venv
3. Activate the Environment

Windows PowerShell:

.venv\Scripts\Activate.ps1

Linux/macOS:

source .venv/bin/activate
4. Install Dependencies
pip install -e .
5. Configure Environment Variables

Windows PowerShell:

Copy-Item .env.example .env

Review .env and adjust configuration if required.

🤖 Ollama

AgentForge uses Ollama for local LLM inference.

Verified development model:

qwen3:4b

Make sure Ollama is installed and running, then make the model available locally.

The application communicates with the local Ollama service rather than requiring a hosted LLM API.

▶️ Run the Application

Start the FastAPI development server:

uvicorn app.main:app --reload

Open the interactive API documentation:

http://127.0.0.1:8000/docs
📊 Current Scope

The current MVP focuses on the foundational agent execution loop and supporting infrastructure.

Implemented capabilities include:

LLM-based planning
Local LLM inference
Tool discovery
Tool selection
Tool execution
Persistent conversation memory
FastAPI integration
Configuration
Runtime limits
Automated testing
Static analysis
Python compilation verification

The implementation is intentionally compact and focused on the core mechanics of an AI agent.

🔄 Future Extensions

Potential future extensions include:

Additional production-grade tools
Structured tool schemas
More advanced planning strategies
More complex multi-step workflows
Agent observability
Authentication and authorization
Richer memory strategies
Evaluation and tracing
Deployment infrastructure
Additional LLM providers
Production monitoring

These are planned extensions rather than claims about the current implementation.

📈 Project Status

Status: MVP complete

The current implementation has passed automated and live verification for its implemented functionality.

Current evidence includes:

11 automated tests passing
Ruff validation passing
Python compilation passing
Live Ollama connectivity
Qwen3:4b availability
End-to-end agent execution
Tool selection and execution
Persistent SQLite memory

AgentForge is currently positioned as a local AI agent engineering project demonstrating the core architecture behind tool-using LLM applications.

🎯 What This Project Demonstrates

AgentForge demonstrates practical AI engineering across multiple layers:

Python
   ↓
Software Architecture
   ↓
FastAPI
   ↓
LLM Integration
   ↓
Agent Planning
   ↓
Tool Calling
   ↓
Controlled Execution
   ↓
Persistent Memory
   ↓
Runtime Safety
   ↓
Testing
   ↓
Code Quality

The project goes beyond a simple LLM API wrapper by implementing the control loop required for a functional tool-using AI agent.

It demonstrates how planning, deterministic execution, memory, runtime controls, and API integration can be combined into a maintainable local agent architecture.

👨‍💻 Author

Syed Ashar Raza

AI Engineer | Machine Learning | Generative AI | LLMs | RAG | AI Agents

Building practical AI systems focused on:

AI Engineering
Agentic AI
LLM Applications
Generative AI
Machine Learning
Python
Backend Development
Production AI Systems
📄 License

No open-source license has been applied yet.

⭐ Project

If you find AgentForge useful or interesting, consider giving the repository a ⭐ on GitHub.
