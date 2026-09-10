"""Shared database connection settings."""
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "hospital_dw"),
    "user": os.getenv("DB_USER", "de_user"),
    "password": os.getenv("DB_PASSWORD", "de_password"),
}


def connection_string() -> str:
    c = DB_CONFIG
    return f"postgresql://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['dbname']}"
