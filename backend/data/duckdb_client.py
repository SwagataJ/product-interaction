"""Singleton DuckDB connection that loads Parquet files as views."""

import duckdb
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

_conn = None


def get_connection() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        _conn = duckdb.connect()
        _conn.execute(f"""
            CREATE VIEW IF NOT EXISTS events AS
            SELECT * FROM read_parquet('{DATA_DIR / "events.parquet"}');

            CREATE VIEW IF NOT EXISTS catalog AS
            SELECT * FROM read_parquet('{DATA_DIR / "product_catalog.parquet"}');

            CREATE VIEW IF NOT EXISTS inventory AS
            SELECT * FROM read_parquet('{DATA_DIR / "tag_inventory.parquet"}');
        """)
    return _conn


def query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    conn = get_connection()
    if params:
        result = conn.execute(sql, params)
    else:
        result = conn.execute(sql)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def query_df(sql: str, params: dict | None = None):
    """Execute a query and return a pandas DataFrame."""
    conn = get_connection()
    if params:
        return conn.execute(sql, params).fetchdf()
    return conn.execute(sql).fetchdf()
