import os
import sys
from dotenv import load_dotenv
import psycopg

load_dotenv()

if not os.getenv("DB_HOST") or not os.getenv("DB_PORT") or not os.getenv("DB_NAME") or not os.getenv("DB_USER") or not os.getenv("DB_PASSWORD"):
    sys.exit("Could not find required database environment variables (ie. DB_HOST, DB_PORT, DB_NAME, DB_USER, or DB_PASSWORD).")

conninfo = f'host={os.getenv("DB_HOST")} port={os.getenv("DB_PORT")} dbname={os.getenv("DB_NAME")} user={os.getenv("DB_USER")} password={os.getenv("DB_PASSWORD")}'


try:
    conn = psycopg.connect(conninfo=conninfo)
    with open('database/schema.sql', 'r') as schema_file:
        with conn.cursor() as cur:
            schema = schema_file.read()
            try:
                cur.execute(schema)
            except Exception as e:
                print(f'Unable to execute schema.sql: {e}')
                quit()
            conn.commit()
            print('Successfully updated all commands described in schema.sql.')
except Exception as e:
    sys.exit(f'Unable to connect to the database: {e}')
