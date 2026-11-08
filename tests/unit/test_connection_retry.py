import pytest

from backend.app.database.session import retry_connect


class Flaky(Exception):
    pass


def test_retries_until_the_connection_succeeds():
    attempts, waits = [], []

    def connect():
        attempts.append(1)
        if len(attempts) < 3:
            raise Flaky("could not translate host name")
        return "connection"

    assert retry_connect(connect, Flaky, attempts=3, base_delay=0.5, sleep=waits.append) == "connection"
    assert len(attempts) == 3
    assert waits == [0.5, 1.0]


def test_gives_up_after_the_last_attempt_and_raises_the_original_error():
    calls, waits = [], []

    def connect():
        calls.append(1)
        raise Flaky("down")

    with pytest.raises(Flaky, match="down"):
        retry_connect(connect, Flaky, attempts=3, sleep=waits.append)
    assert len(calls) == 3 and len(waits) == 2


def test_other_errors_are_not_retried():
    calls = []

    def connect():
        calls.append(1)
        raise ValueError("bad dsn")

    with pytest.raises(ValueError):
        retry_connect(connect, Flaky, sleep=lambda seconds: None)
    assert len(calls) == 1


def test_success_on_the_first_try_never_sleeps():
    waits = []
    assert retry_connect(lambda: "ok", Flaky, sleep=waits.append) == "ok"
    assert waits == []