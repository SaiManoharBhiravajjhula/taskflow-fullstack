import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.NamedTemporaryFile(delete=False).name}"
os.environ["JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client, email="admin@taskflow.dev", password="Admin123!"):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_and_dashboard_summary(client):
    headers = login(client)
    response = client.get("/dashboard/summary", headers=headers)
    assert response.status_code == 200
    assert response.json()["total_tasks"] >= 2


def test_admin_can_create_task_and_user_can_only_update_status(client):
    admin_headers = login(client)
    users = client.get("/admin/users", headers=admin_headers).json()
    assignee = next(user for user in users if user["role"] == "user")

    created = client.post(
        "/tasks",
        headers=admin_headers,
        json={"title": "Write release notes", "priority": "urgent", "assignee_id": assignee["id"]},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    user_headers = login(client, "user@taskflow.dev", "User123!")
    updated = client.patch(
        f"/tasks/{task_id}",
        headers=user_headers,
        json={"title": "Blocked title change", "status": "review"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Write release notes"
    assert updated.json()["status"] == "review"


def test_registration_prevents_duplicate_email(client):
    response = client.post(
        "/auth/register",
        json={"name": "Demo User", "email": "user@taskflow.dev", "password": "Password123!"},
    )
    assert response.status_code == 409
