from fastapi.testclient import TestClient

from app.main import create_app


def test_recommendation_endpoint(repository) -> None:
    app = create_app(repository=repository)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "city": "Алматы",
                "event_date": "2026-11-14",
                "event_format": "свадьба",
                "category": "Фотограф",
                "budget_kzt": 200000,
                "duration_hours": 6,
                "language": "русский",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "matched"
    assert len(payload["items"]) == 2
    assert payload["meta"]["exclusions"]["busy"] == 1


def test_date_outside_dataset_window_is_rejected(repository) -> None:
    app = create_app(repository=repository)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "city": "Алматы",
                "event_date": "2027-01-01",
                "event_format": "свадьба",
                "category": "Фотограф",
                "budget_kzt": 200000,
            },
        )

    assert response.status_code == 422


def test_health_and_readiness(repository) -> None:
    app = create_app(repository=repository)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        ready = client.get("/ready")

    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_catalog_options(repository) -> None:
    app = create_app(repository=repository)
    with TestClient(app) as client:
        response = client.get("/api/v1/catalog/options")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cities"] == ["Алматы", "Астана"]
    assert "Фотограф" in payload["categories"]
    assert "свадьба" in payload["event_formats"]
