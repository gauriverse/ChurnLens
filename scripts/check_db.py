import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.getenv("DATABASE_URL")

if not url:
    raise SystemExit("DATABASE_URL not found. Check that .env is in the ChurnLens root.")

if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

engine = create_engine(url, pool_pre_ping=True)

with engine.connect() as conn:
    print(conn.execute(text("select version()")).scalar())
    print(conn.execute(text("select current_database(), current_user")).one())