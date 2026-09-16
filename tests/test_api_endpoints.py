"""
End-to-end integration tests for FastAPI REST endpoints:
Health, Projects, Agents, Skills, Settings, AI Providers, Chat, and Dev Diagnostics.
"""

from fastapi.testclient import TestClient
from gokai.apps.backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "active_providers" in data


def test_projects_crud():
    # Create project
    res = client.post("/api/projects", json={"name": "Test Project API", "description": "API Test", "default_stack": "python"})
    assert res.status_code == 201
    proj = res.json()
    proj_id = proj["id"]

    # Get project
    res_get = client.get(f"/api/projects/{proj_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Test Project API"

    # List projects
    res_list = client.get("/api/projects")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Cleanup delete
    res_del = client.delete(f"/api/projects/{proj_id}")
    assert res_del.status_code == 204


def test_agents_and_skills_endpoints():
    # Agents
    res = client.get("/api/agents")
    assert res.status_code == 200
    assert len(res.json()) >= 5

    # Skills list
    res_skills = client.get("/api/skills")
    assert res_skills.status_code == 200
    assert len(res_skills.json()) >= 2


def test_settings_endpoints():
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "default_provider" in data
    assert "max_debug_cycles" in data

    # Update settings
    res_put = client.put("/api/settings", json={"autonomy_level": "high"})
    assert res_put.status_code == 200
    assert res_put.json()["autonomy_level"] == "high"


def test_provider_management_endpoints():
    # List providers
    res = client.get("/api/settings/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 5
    prov_ids = [p["provider"] for p in providers]
    assert "gemini" in prov_ids
    assert "openai" in prov_ids
    assert "anthropic" in prov_ids
    assert "mock" in prov_ids

    # Test mock connection
    res_test = client.post("/api/settings/providers/test", json={"provider": "mock"})
    assert res_test.status_code == 200
    assert res_test.json()["success"] is True


def test_chat_and_attachments_endpoints():
    # Create conversation
    res_conv = client.post("/api/chat/conversations", json={"title": "Test Integration Chat"})
    assert res_conv.status_code == 200
    conv = res_conv.json()
    conv_id = conv["id"]

    # Send message with code attachment
    msg_payload = {
        "content": "Review this sample Python function for edge cases.",
        "attachments": [
            {
                "name": "calc.py",
                "type": "code",
                "size_bytes": 64,
                "content": "def add(a: int, b: int) -> int:\n    return a + b\n"
            }
        ]
    }
    res_msg = client.post(f"/api/chat/conversations/{conv_id}/messages", json=msg_payload)
    assert res_msg.status_code == 200
    ai_resp = res_msg.json()
    assert ai_resp["role"] == "assistant"
    assert len(ai_resp["content"]) > 0

    # Retrieve messages
    res_msgs = client.get(f"/api/chat/conversations/{conv_id}")
    assert res_msgs.status_code == 200
    msgs = res_msgs.json()
    assert len(msgs) >= 2  # user + assistant

    # Delete conversation
    res_del = client.delete(f"/api/chat/conversations/{conv_id}")
    assert res_del.status_code == 200


def test_skills_crud_and_toggle_endpoints():
    # Create custom skill
    skill_payload = {
        "name": "docker-compose-deploy",
        "description": "Deployment using Docker Compose stacks",
        "when_to_use": "Use when creating multi-container deployment files",
        "tags": ["docker", "compose", "devops"],
        "instructions": "# Docker Compose Guidelines\nUse version 3.8+ syntax."
    }
    res_create = client.post("/api/skills", json=skill_payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["name"] == "docker-compose-deploy"
    assert created["is_builtin"] is False

    # Toggle skill
    res_toggle = client.post("/api/skills/docker-compose-deploy/toggle")
    assert res_toggle.status_code == 200
    assert res_toggle.json()["enabled"] is False

    # Delete custom skill
    res_del = client.delete("/api/skills/docker-compose-deploy")
    assert res_del.status_code == 200


def test_dev_diagnostics_endpoints():
    res = client.get("/api/dev/diagnostics")
    assert res.status_code == 200
    diag = res.json()
    assert "system" in diag
    assert "backend" in diag
    assert "providers" in diag
    assert "sandbox" in diag
    assert "recent_logs" in diag

    # Test cache clear
    res_cache = client.post("/api/dev/clear-cache")
    assert res_cache.status_code == 200
    assert res_cache.json()["status"] == "success"

    # Test config reload
    res_reload = client.post("/api/dev/reload-config")
    assert res_reload.status_code == 200
    assert res_reload.json()["status"] == "success"
