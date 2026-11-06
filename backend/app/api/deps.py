from collections.abc import Iterator

from sqlalchemy.orm import Session

from backend.app.database.session import get_session_factory

def get_db() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()