import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.app.api.deps import get_db
from backend.app.main import create_app


class FailingSession:
    """A stand-in session whose every database call raises the given error."""

    def __init__(self, error):
        self.error = error

    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise self.error
        return fail


def client_failing_with(error):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: FailingSession(error)
    return TestClient(app)


def test_connection_problems_become_503_with_retry_after():
    error = OperationalError(
        "select 1", None, Exception('could not translate host name "db.example" to address')
    )
    response = client_failing_with(error).get("/api/v1/customers")
    assert response.status_code == 503
    assert response.json() == {"detail": "database temporarily unavailable, please retry"}
    assert response.headers["retry-after"] == "5"


def test_other_database_errors_are_not_disguised():
    error = ProgrammingError("select 1", None, Exception("column does not exist"))
    with pytest.raises(ProgrammingError):  # the test client re-raises unhandled server errors
        client_failing_with(error).get("/api/v1/customers")