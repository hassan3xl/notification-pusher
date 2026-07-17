import os
from sqlalchemy import create_engine, text

db_url = "postgresql://neondb_owner:npg_8TM0RHFtYQsN@ep-broad-silence-za34j2xk-pooler.c-2.eu-west-2.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(db_url)
with engine.connect() as conn:
    res = conn.execute(text("SELECT key, name, is_active FROM api_keys"))
    for row in res:
        print(row)
