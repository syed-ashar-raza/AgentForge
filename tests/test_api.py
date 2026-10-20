from fastapi.testclient import TestClient

from app.main import app


def test_root() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "AgentForge"


def test_tools() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["tools"]}
    assert "calculator" in names
    assert "current_datetime" in names


def test_mcp_lifespan_startup_and_shutdown(monkeypatch) -> None:
    import app.api.routes as routes
    import app.main as main
    from app.agent.agent import Agent
    from app.core.config import settings

    test_agent = Agent()
    monkeypatch.setattr(settings, "mcp_enabled", True)
    monkeypatch.setattr(main, "agent", test_agent)
    monkeypatch.setattr(routes, "agent", test_agent)

    with TestClient(main.app) as client:
        assert main.app.state.mcp_client is not None

        response = client.get("/api/v1/tools")
        assert response.status_code == 200

        names = {item["name"] for item in response.json()["tools"]}
        assert "mcp__agentforge__calculator" in names
        assert "mcp__agentforge__current_datetime" in names

    assert main.app.state.mcp_client is None


def test_health_reports_ollama_provider(monkeypatch) -> None:
    import app.api.routes as routes
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(routes.agent.llm, "health", lambda: True)

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provider"] == "ollama"
    assert data["ollama"] is True
    assert data["model"] == routes.agent.llm.model


def test_health_reports_gemini_provider(monkeypatch) -> None:
    import app.api.routes as routes
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(routes.agent.llm, "health", lambda: True)

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provider"] == "gemini"
    assert data["ollama"] is False
    assert data["model"] == routes.agent.llm.model


def test_request_observability_adds_request_id_and_logs_duration(
    caplog,
) -> None:
    import logging
    from uuid import UUID

    with caplog.at_level(logging.INFO, logger="app.main"):
        response = TestClient(app).get("/")

    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)

    log_record = next(
        record
        for record in caplog.records
        if record.name == "app.main" and request_id in record.getMessage()
    )
    assert "http_request_completed" in log_record.message
    assert "method=GET" in log_record.message
    assert "status_code=200" in log_record.message
    assert "duration_ms=" in log_record.message


def test_request_observability_logs_not_found_status(caplog) -> None:
    import logging

    with caplog.at_level(logging.INFO, logger="app.main"):
        response = TestClient(app).get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert "X-Request-ID" in response.headers
    assert any(
        record.name == "app.main"
        and "http_request_completed" in record.message
        and "status_code=404" in record.message
        for record in caplog.records
    )


def test_request_observability_logs_unhandled_exception(caplog) -> None:
    import logging

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import app.main as main

    test_app = FastAPI()

    @test_app.get("/fail")
    def fail() -> None:
        raise RuntimeError("simulated internal failure")

    test_app.middleware("http")(main.observe_requests)

    with caplog.at_level(logging.ERROR, logger="app.main"):
        response = TestClient(
            test_app,
            raise_server_exceptions=False,
        ).get("/fail")

    assert response.status_code == 500
    assert "X-Request-ID" in response.headers
    assert any(
        record.name == "app.main"
        and "http_request_failed" in record.message
        and "request_id=" in record.message
        for record in caplog.records
    )
