from sqlalchemy import create_engine, text
import os

url=os.environ.get("DATABASE_URL")

engine=create_engine(url)

with engine.begin() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS recipes(
        id SERIAL PRIMARY KEY,
        title VARCHAR(200),
        minutes INTEGER,
        description TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    )
    """))
print("DB OK")