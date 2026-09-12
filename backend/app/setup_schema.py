from sqlalchemy.engine import make_url
import psycopg
from psycopg import sql

from app.core.config import settings


SCHEMA_NAME = "laya_market"


def main() -> None:
    url = make_url(settings.database_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL.")

    connection_kwargs = {
        "host": url.host or "127.0.0.1",
        "port": url.port or 5432,
        "user": url.username or "postgres",
        "dbname": url.database or "postgres",
    }
    if url.password:
        connection_kwargs["password"] = url.password

    with psycopg.connect(**connection_kwargs, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(SCHEMA_NAME)))
            print(f"PostgreSQL schema ready: {SCHEMA_NAME}")


if __name__ == "__main__":
    main()
