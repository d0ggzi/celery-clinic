from src.homework.tasks import create_record
from src.homework.main import app
from fastapi.testclient import TestClient
import pytest
import json


@pytest.fixture
def client():
    client = TestClient(app)
    return client


def test_task():
    assert create_record.delay("Терапевт")


def test_home(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_create_record(client):
    data = json.dumps({
        "doctor": "Терапевт"
    })
    resp = client.post("/records", data=data)
    record_id = resp.json()["record_id"]
    assert record_id


def test_status(client):
    data = json.dumps({
        "doctor": "Лор"
    })
    resp = client.post("/records", data=data)
    record_id = resp.json()["record_id"]

    response = client.get(f"/records/{record_id}")
    content = response.json()

    assert response.status_code == 200
    while content["record_status"] == "PENDING":
        response = client.get(f"/records/{record_id}")
        content = response.json()

    assert content == {"record_id": record_id, "doctor": "Лор", "record_status": "Обработка..."}
    while content["record_status"] == "Обработка...":
        response = client.get(f"/records/{record_id}")
        content = response.json()

    assert content == {"record_id": record_id, "doctor": "Лор", "record_status": "Запись..."}
    while content["record_status"] == "Запись...":
        response = client.get(f"/records/{record_id}")
        content = response.json()

    assert content == {"record_id": record_id, "doctor": "Лор", "record_status": "Успешно"}


def test_get_records(client):
    resp = client.get("/allRecords")
    assert resp.status_code == 200
