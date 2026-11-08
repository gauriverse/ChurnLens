import time
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_database_url

CONNECT_ATTEMPTS = 3
CONNECT_BASE_DELAY = 0.5  # seconds: waits 0.5 s, then 1 s, between attempts


def retry_connect(connect, errors, attempts=CONNECT_ATTEMPTS,
                  base_delay=CONNECT_BASE_DELAY, sleep=time.sleep):
    for attempt in range(1, attempts + 1):
        try:
            return connect()
        except errors:
            if attempt == attempts:
                raise
            sleep(base_delay * attempt)


def make_engine(url=None):
    target = url or get_database_url()
    options = {}
    if make_url(target).get_backend_name() == "postgresql":
        options["connect_args"] = {"connect_timeout": 10}  

    engine = create_engine(
        target,
        pool_pre_ping=True,   
        pool_recycle=300,     
        **options,
    )

    if engine.dialect.name == "postgresql":
        @event.listens_for(engine, "do_connect")
        def connect_with_retry(dialect, connection_record, cargs, cparams):
            return retry_connect(
                lambda: dialect.connect(*cargs, **cparams),
                dialect.loaded_dbapi.OperationalError,
            )

    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@lru_cache
def get_engine():
    return make_engine()


@lru_cache
def get_session_factory():
    return make_session_factory(get_engine())