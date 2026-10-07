
Architecture Decision Records
ADR-001 — Model Gateway

Decision: Isolate provider/model-specific communication behind a model gateway.

Reason: Prevent provider-specific HTTP, retry, timeout, routing, and circuit-breaker logic from leaking into orchestration.

Evidence: Nexora.

Trade-off: Adds a service boundary and operational complexity.

ADR-002 — Tools Outside the LLM

Decision: The model may select a registered capability, but application code executes it.

Reason: The LLM is not an authority to execute arbitrary side effects.

Evidence: AgentForge.

Trade-off: Requires schemas, validation, and runtime handling.

ADR-003 — Bounded Agent Execution

Decision: Enforce maximum agent steps and maximum tool calls.

Reason: Prevent runaway loops, latency amplification, and uncontrolled execution.

Evidence: AgentForge checkpoint 0f55ede.

Trade-off: Complex workflows may need decomposition.

ADR-004 — Evaluation as a Release Gate

Decision: Run behavioral evaluation with automated tests and linting.

Reason: Unit tests alone cannot establish retrieval quality, answer evidence, or abstention behavior.

Evidence: RAGForge continuous evaluation gate.

Trade-off: CI takes additional time and requires maintained datasets.

ADR-005 — Health and Readiness

Decision: Separate process health from dependency readiness.

Reason: Deployment systems need to know whether traffic can safely reach a service.

Evidence: Nexora /health and /ready.

ADR-006 — Independent Scaling

Decision: Scale stateless APIs independently from model serving and stateful services.

Reason: These workloads have different resource profiles.

Trade-off: Requires explicit persistence and service boundaries.

ADR-007 — Async Only When Justified

Decision: Do not introduce queues merely for architectural completeness.

Reason: Distributed infrastructure adds latency, failure modes, deployment complexity, and operational cost.

Trigger: Introduce workers/queues when measured workload duration, concurrency, or isolation requirements justify them.
