from backend.app.database.session import make_engine


def test_postgres_engines_get_the_connection_retry():
    engine = make_engine("postgresql+psycopg://user:pass@localhost/db")  
    assert engine.dialect.driver == "psycopg"
    assert engine.dialect.dispatch.do_connect


def test_other_databases_are_left_alone():
    engine = make_engine("sqlite://")
    assert not engine.dialect.dispatch.do_connect