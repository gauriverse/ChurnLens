import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

load_dotenv()
url = os.getenv("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL not found in .env")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

engine = create_engine(url, pool_pre_ping=True)

tables = sorted(inspect(engine).get_table_names())
print(len(tables), "tables:", tables)

with engine.connect() as conn:
    version = conn.execute(text("select version_num from alembic_version")).scalar()
    print("alembic revision:", version)

    print("\nCHECK constraints:")
    rows = conn.execute(text(
        "select conrelid::regclass::text, conname from pg_constraint "
        "where contype = 'c' order by 1, 2"
    ))
    for table, name in rows:
        print(" ", table, "->", name)

    print("\nIndexes:")
    rows = conn.execute(text(
        "select tablename, indexname from pg_indexes "
        "where schemaname = 'public' order by 1, 2"
    ))
    for table, name in rows:
        print(" ", table, "->", name)

# The database itself should refuse bad data. engine.begin() rolls back on error.
try:
    with engine.begin() as conn:
        conn.execute(text(
            "insert into datasets (name, row_count, file_hash, is_reference) "
            "values ('bad', -1, 'bad', false)"
        ))
    print("\nPROBLEM: a negative row_count was accepted")
except IntegrityError:
    print("\nOK: the database rejected a negative row_count")