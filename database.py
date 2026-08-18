"""
SQLite database connection and initialization services.

This module owns low-level database mechanics for the Media Archive
Manager.

Responsibilities:
    - Open SQLite database connections.
    - Enable SQLite foreign-key enforcement.
    - Initialize a database from schema.sql.

This module does NOT:
    - Implement media-domain operations.
    - Contain ingestion workflow logic.
    - Execute application-level queries.
    - Validate movie or television metadata.

Application-level persistence belongs in repository.py.
"""

import sqlite3
from pathlib import Path


def connect_database(
    database_path: Path,
) -> sqlite3.Connection:
    """
    Open a SQLite database connection.

    Foreign-key enforcement is explicitly enabled because SQLite
    does not enable it automatically for every connection.

    Args:
        database_path:
            Filesystem path to the SQLite database.

    Returns:
        An open SQLite connection configured for application use.
    """

    database_path = Path(database_path)

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        database_path
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_database(
    database_path: Path,
    schema_path: Path,
) -> None:
    """
    Initialize a SQLite database using the project's SQL schema.

    CREATE TABLE IF NOT EXISTS statements in schema.sql make this
    operation safe to run repeatedly against an existing database.

    Args:
        database_path:
            Filesystem path of the database to initialize.

        schema_path:
            Filesystem path to schema.sql.
    """

    database_path = Path(database_path)
    schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Database schema not found: "
            f"{schema_path}"
        )

    schema = schema_path.read_text(
        encoding="utf-8"
    )

    connection = connect_database(
        database_path
    )

    try:
        connection.executescript(
            schema
        )

        connection.commit()

    finally:
        connection.close()