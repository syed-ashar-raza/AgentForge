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
