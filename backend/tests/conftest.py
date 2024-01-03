import pytest
import psycopg
import os

from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def test_db():
    conninfo = f'host={os.getenv("DB_HOST")} port={os.getenv("DB_PORT")} dbname={os.getenv("DB_NAME")} user={os.getenv("DB_USER")} password={os.getenv("DB_PASSWORD")}' 
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            # currently only deletes account and the tables that reference account
            # ...which is (almost) all of them, i believe
            cur.execute('truncate account cascade')
            conn.commit()