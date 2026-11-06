from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.main import create_app

def sqlite_session():
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session:
        yield session

def broken_session():
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("select 1", None, Exception("database is down"))

    yield BrokenSession()

def client_with(db_override=None):
    app = create_app()
    if db_override is not None:
        app.dependency_overrides[get_db] = db_override
    return TestClient(app)

def test_liveness_does_not_need_the_database():
    response = client_with().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_connected_database():
    response = client_with(sqlite_session).get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_readiness_returns_503_when_database_is_down():
    response = client_with(broken_session).get("/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}


def test_swagger_docs_and_openapi_are_available():
    client = client_with()
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert "/health" in paths and "/health/db" in paths


def test_cors_allows_the_frontend_origin_only():
    client = client_with()
    ok = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    bad = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in bad.headers