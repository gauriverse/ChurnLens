from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_database_url


def make_engine(url=None):
    return create_engine(url or get_database_url(), pool_pre_ping=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)

@lru_cache
def get_engine():
    return make_engine()

@lru_cache
def get_session_factory():
    return make_session_factory(get_engine())