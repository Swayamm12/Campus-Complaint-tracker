import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
AUTH = (main.STAFF_USERNAME, main.STAFF_PASSWORD)  # staff login

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
    assert len(client.get("/complaints", auth=AUTH).json()) == 2
    assert len(client.get("/complaints?category=canteen", auth=AUTH).json()) == 1
    assert len(client.get("/complaints?status=Resolved", auth=AUTH).json()) == 0


def test_get_missing_complaint_404():
    assert client.get("/complaints/99", auth=AUTH).status_code == 404


def test_valid_status_flow():
    create()
    r1 = client.patch("/complaints/1/status", json={"status": "In Progress"}, auth=AUTH)
    assert r1.status_code == 200 and r1.json()["status"] == "In Progress"
    r2 = client.patch("/complaints/1/status", json={"status": "Resolved"}, auth=AUTH)
    assert r2.status_code == 200 and r2.json()["status"] == "Resolved"


def test_cannot_skip_open_to_resolved():
    create()
    r = client.patch("/complaints/1/status", json={"status": "Resolved"}, auth=AUTH)
    assert r.status_code == 400


def test_cannot_go_backwards():
    create()
    client.patch("/complaints/1/status", json={"status": "In Progress"}, auth=AUTH)
    r = client.patch("/complaints/1/status", json={"status": "Open"}, auth=AUTH)
    assert r.status_code == 400


def test_resolved_is_final():
    create()
    client.patch("/complaints/1/status", json={"status": "In Progress"}, auth=AUTH)
    client.patch("/complaints/1/status", json={"status": "Resolved"}, auth=AUTH)
    r = client.patch("/complaints/1/status", json={"status": "In Progress"}, auth=AUTH)
    assert r.status_code == 400



def test_staff_endpoints_need_login():
    create()
    assert client.get("/complaints").status_code == 401
    assert client.get("/complaints/1").status_code == 401
    assert client.patch("/complaints/1/status", json={"status": "In Progress"}).status_code == 401


def test_wrong_password_rejected():
    r = client.get("/complaints", auth=(main.STAFF_USERNAME, "wrong-password"))
    assert r.status_code == 401


def test_student_page_and_staff_page_load():
    assert client.get("/").status_code == 200
    assert client.get("/staff").status_code == 200
