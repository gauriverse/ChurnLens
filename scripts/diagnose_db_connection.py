import socket
import time

import psycopg2
from sqlalchemy.engine import make_url

from backend.app.core.config import get_database_url

url = make_url(get_database_url())
dsn = url.set(drivername="postgresql").render_as_string(hide_password=False) 
host, port = url.host, url.port or 5432
print("database host:", host)

print("\n1. name lookups (Windows caches answers, so nslookup above is the fairer test)")
failed = 0
for i in range(1, 11):
    start = time.perf_counter()
    try:
        found = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        families = sorted({"IPv6" if r[0] == socket.AF_INET6 else "IPv4" for r in found})
        print(f"  lookup {i:2}: ok    {(time.perf_counter() - start) * 1000:6.0f} ms  {', '.join(families)}")
    except socket.gaierror as error:
        failed += 1
        print(f"  lookup {i:2}: FAIL  {error}")
    time.sleep(1)

print("\n2. fresh connections, no pool")
connect_failed = 0
for i in range(1, 11):
    start = time.perf_counter()
    try:
        connection = psycopg2.connect(dsn, connect_timeout=10)
        with connection.cursor() as cursor:
            cursor.execute("select 1")
        connection.close()
        print(f"  connect {i:2}: ok    {(time.perf_counter() - start) * 1000:6.0f} ms")
    except psycopg2.OperationalError as error:
        connect_failed += 1
        first_line = str(error).strip().splitlines()[0]
        print(f"  connect {i:2}: FAIL  {(time.perf_counter() - start) * 1000:6.0f} ms  {first_line}")
    time.sleep(2)

print(f"\nlookup failures: {failed}/10   connection failures: {connect_failed}/10")