import os
from pathlib import Path

import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

# Load .env file
load_dotenv(Path(__file__).with_name(".env"))

# Connection pool for MySQL
def build_connection_pool():
    host = os.environ["MYSQL_HOST"]
    user = os.environ["MYSQL_USER"]
    password = os.environ["MYSQL_PASSWORD"]
    database = os.environ["MYSQL_DB"]
    port = int(os.environ.get("MYSQL_PORT", "3306"))

    return pooling.MySQLConnectionPool(
        pool_name="mcp_mysql_pool",
        pool_size=5,
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        charset="utf8mb4",
        autocommit=False,
    )

POOL = build_connection_pool()

def get_conn():
    return POOL.get_connection()

server = FastMCP(name="mysql-db")


@server.tool()
async def run_query(ctx: Context, sql: str):
    """
    Execute arbitrary SQL against the configured MySQL database.

    For SELECT queries returns {"columns": [...], "rows": [...]}
    For DML (INSERT/UPDATE/DELETE) returns {"rows_affected": n}
    """
    conn = get_conn()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql)
            if cur.description:
                rows = cur.fetchall()
                columns = [col[0] for col in cur.description]
                return {"columns": columns, "rows": rows}
            conn.commit()
            return {"rows_affected": cur.rowcount}
    finally:
        conn.close()


@server.tool()
async def describe_table(ctx: Context, schema: str, table_name: str):
    """
    Return column metadata for schema.table_name using INFORMATION_SCHEMA.
    """
    conn = get_conn()
    try:
        query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION;
        """
        with conn.cursor(dictionary=True) as cur:
            cur.execute(query, (schema, table_name))
            rows = cur.fetchall()
            return [
                {
                    "column": row["COLUMN_NAME"],
                    "type": row["DATA_TYPE"],
                    "nullable": row["IS_NULLABLE"] == "YES",
                    "length": row["CHARACTER_MAXIMUM_LENGTH"],
                }
                for row in rows
            ]
    finally:
        conn.close()


@server.tool()
async def describe_indexes_and_foreign_keys(ctx: Context, schema: str, table_name: str):
    """
    Return index definitions plus inbound/outbound foreign keys for schema.table_name.
    """
    conn = get_conn()
    try:
        index_query = """
            SELECT
                INDEX_NAME,
                NON_UNIQUE = 0 AS IS_PRIMARY_OR_UNIQUE,
                SEQ_IN_INDEX,
                COLUMN_NAME
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX;
        """

        fk_query = """
            SELECT
                CONSTRAINT_NAME,
                TABLE_SCHEMA,
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_SCHEMA,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION;
        """

        with conn.cursor(dictionary=True) as cur:
            # Indexes
            cur.execute(index_query, (schema, table_name))
            idx_rows = cur.fetchall()
            indexes = {}
            for row in idx_rows:
                idx_name = row["INDEX_NAME"] or "(unnamed)"
                if idx_name not in indexes:
                    indexes[idx_name] = {
                        "name": idx_name,
                        "is_primary_or_unique": bool(row["IS_PRIMARY_OR_UNIQUE"]),
                        "columns": [],
                    }
                indexes[idx_name]["columns"].append(
                    {
                        "name": row["COLUMN_NAME"],
                        "seq_in_index": row["SEQ_IN_INDEX"],
                    }
                )

            # Foreign keys (outbound from this table)
            cur.execute(fk_query, (schema, table_name))
            fk_rows = cur.fetchall()
            outbound = {}
            inbound = {}
            for row in fk_rows:
                fk_name = row["CONSTRAINT_NAME"]
                # outbound: this table references another
                if fk_name not in outbound:
                    outbound[fk_name] = {
                        "name": fk_name,
                        "target_schema": row["REFERENCED_TABLE_SCHEMA"],
                        "target_table": row["REFERENCED_TABLE_NAME"],
                        "columns": [],
                    }
                outbound[fk_name]["columns"].append(
                    {
                        "column": row["COLUMN_NAME"],
                        "references": row["REFERENCED_COLUMN_NAME"],
                    }
                )
                # inbound: conceptually, the referenced table is target of inbound FK
                key = f"{row['REFERENCED_TABLE_SCHEMA']}.{row['REFERENCED_TABLE_NAME']}.{fk_name}"
                if key not in inbound:
                    inbound[key] = {
                        "name": fk_name,
                        "source_schema": row["TABLE_SCHEMA"],
                        "source_table": row["TABLE_NAME"],
                        "columns": [],
                    }
                inbound[key]["columns"].append(
                    {
                        "column": row["COLUMN_NAME"],
                        "references": row["REFERENCED_COLUMN_NAME"],
                    }
                )

        return {
            "indexes": list(indexes.values()),
            "foreign_keys_outbound": list(outbound.values()),
            "foreign_keys_inbound": list(inbound.values()),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    server.run()
