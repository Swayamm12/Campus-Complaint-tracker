import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

SAMPLE = {"title": "Broken fan", "category": "hostel", "description": "Fan in room 204 not working"}


@pytest.fixture(autouse=True)
def reset_storage():
    main.complaints.clear()
    main.next_id = 1


def create(**overrides):
    return client.post("/complaints", json={**SAMPLE, **overrides})


def test_submit_complaint_starts_open():
    r = create()
    assert r.status_code == 201
    assert r.json()["status"] == "Open"
    assert r.json()["id"] == 1


def test_submit_invalid_category_rejected():
    assert create(category="parking").status_code == 422


def test_submit_missing_title_rejected():
    r = client.post("/complaints", json={"category": "hostel", "description": "something"})
    assert r.status_code == 422


def test_list_and_filter():
    create()
    create(title="Bad food", category="canteen")
    assert len(client.get("/complaints").json()) == 2
    assert len(client.get("/complaints?category=canteen").json()) == 1
    assert len(client.get("/complaints?status=Resolved").json()) == 0


def test_get_missing_complaint_404():
    assert client.get("/complaints/99").status_code == 404


def test_valid_status_flow():
    create()
    r1 = client.patch("/complaints/1/status", json={"status": "In Progress"})
    assert r1.status_code == 200 and r1.json()["status"] == "In Progress"
    r2 = client.patch("/complaints/1/status", json={"status": "Resolved"})
    assert r2.status_code == 200 and r2.json()["status"] == "Resolved"


def test_cannot_skip_open_to_resolved():
    create()
    r = client.patch("/complaints/1/status", json={"status": "Resolved"})
    assert r.status_code == 400


def test_cannot_go_backwards():
    create()
    client.patch("/complaints/1/status", json={"status": "In Progress"})
    r = client.patch("/complaints/1/status", json={"status": "Open"})
    assert r.status_code == 400


def test_resolved_is_final():
    create()
    client.patch("/complaints/1/status", json={"status": "In Progress"})
    client.patch("/complaints/1/status", json={"status": "Resolved"})
    r = client.patch("/complaints/1/status", json={"status": "In Progress"})
    assert r.status_code == 400
