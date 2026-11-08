import pytest

from backend.app.core.config import get_cors_origins, get_database_url


@pytest.mark.parametrize("given, expected", [
    ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("postgresql://u:p@h/db?sslmode=require", "postgresql+psycopg://u:p@h/db?sslmode=require"),
    ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("sqlite://", "sqlite://"),
])
def test_database_url_names_the_psycopg_driver(monkeypatch, given, expected):
    monkeypatch.setenv("DATABASE_URL", given)
    assert get_database_url() == expected


def test_missing_database_url_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        get_database_url()


def test_cors_origins_default_and_list(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert get_cors_origins() == ["http://localhost:5173"]
    monkeypatch.setenv("CORS_ORIGINS", "https://a.vercel.app, http://localhost:5173")
    assert get_cors_origins() == ["https://a.vercel.app", "http://localhost:5173"]