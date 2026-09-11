from sqlalchemy.engine import make_url
import psycopg
from psycopg import sql

from app.core.config import settings


def main() -> None:
    url = make_url(settings.database_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL.")

    database_name = url.database or "laya_market"
    connection_kwargs = {
        "host": url.host or "127.0.0.1",
        "port": url.port or 5432,
        "user": url.username or "postgres",
        "dbname": "postgres",
    }
    if url.password:
        connection_kwargs["password"] = url.password

    try:
        with psycopg.connect(**connection_kwargs, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
                exists = cur.fetchone() is not None
                if not exists:
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
                    print(f"Created PostgreSQL database: {database_name}")
                else:
                    print(f"PostgreSQL database ready: {database_name}")
    except Exception as exc:
        raise RuntimeError(
            "Could not connect to local PostgreSQL. Check backend/.env host, port, user and password."
        ) from exc


if __name__ == "__main__":
    main()
