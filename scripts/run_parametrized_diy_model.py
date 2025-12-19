#!/usr/bin/env python3
"""Run the DIY HHS-HCC SQL script using settings from config.yml.

This script:
- reads run_settings from a YAML config
- injects a parameterized DECLARE prelude
- strips the hard-coded "User Inputs" DECLARE block from DIY-Model-Script/diy_model_script.sql
- executes the resulting SQL batch against SQL Server via ODBC

Environment variables (defaults match the container quickstart):
  MSSQL_SERVER   default: localhost,1433
  MSSQL_DATABASE default: edge
  MSSQL_USER     default: sa
  MSSQL_PASSWORD default: $MSSQL_SA_PASSWORD (if set)

Example:
  MSSQL_PASSWORD=... python scripts/run_diy_model.py
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

SQL_MARKER = "/***** End User Inputs; Do not edit below this line ******/"


def build_connection_string(
    *,
    driver: str,
    server: str,
    database: str,
    user: str,
    password: str,
    encrypt: bool = True,
    trust_server_certificate: bool = True,
) -> str:
    enc = "yes" if encrypt else "no"
    trust = "yes" if trust_server_certificate else "no"
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Encrypt={enc};"
        f"TrustServerCertificate={trust};"
    )


def load_config(config_path: Path) -> dict:
    return yaml.safe_load(config_path.read_text())


def load_params(cfg: dict) -> dict:
    s = cfg["run_settings"]
    return {
        "benefit_year": s["benefit_year"],
        "start_date": s["analysis_period"]["start_date"],
        "end_date": s["analysis_period"]["end_date"],
        "paid_through": s["analysis_period"]["paid_through_date"],
        "state": s["population_filters"]["state"],
        "market": s["population_filters"]["market"],
        "issuer_hios": s["population_filters"]["issuer_hios_id"],
    }


def load_db_settings(cfg: dict) -> dict:
    db = cfg.get("database")
    if not isinstance(db, dict):
        raise ValueError("Missing required 'database' section in config.yml")

    driver = db.get("driver", "ODBC Driver 18 for SQL Server")
    server = db.get("server")
    database = db.get("database")
    user = db.get("user")

    password = db.get("password")
    if not password:
        password_env = db.get("password_env")
        if password_env:
            password = os.getenv(password_env)

    if not server or not database or not user or not password:
        raise ValueError(
            "Database config incomplete. Required: database.server, database.database, database.user, and either "
            "database.password or database.password_env (set that env var)."
        )

    encrypt = bool(db.get("encrypt", True))
    trust = bool(db.get("trust_server_certificate", True))

    return {
        "driver": driver,
        "server": server,
        "database": database,
        "user": user,
        "password": password,
        "encrypt": encrypt,
        "trust_server_certificate": trust,
    }


def build_sql_batch(sql_path: Path) -> str:
    sql_text = sql_path.read_text()

    if SQL_MARKER not in sql_text:
        raise ValueError(
            f"Could not find SQL marker line in {sql_path}: {SQL_MARKER!r}. "
            "Refusing to guess where to cut the DECLARE block."
        )

    # Remove the original hard-coded user-input DECLARE block.
    sql_tail = sql_text.split(SQL_MARKER, 1)[1]

    # Parameterized prelude. Keep non-config variables as defaults.
    prelude = """
SET NOCOUNT ON;

DECLARE @benefityear int = ?;
DECLARE @startdate date = ?;
DECLARE @enddate date = ?;
DECLARE @paidthrough date = ?;

DECLARE @state varchar(2) = ?;
DECLARE @market int = ?;
DECLARE @issuer_hios varchar(5) = ?;

DECLARE @droptemp bit = 1;
DECLARE @output_table varchar(50) = 'hcc_list';
DECLARE @drop_existing bit = 0;
""".strip(
        "\n"
    )

    return prelude + "\n\n" + SQL_MARKER + sql_tail


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "config.yml"
    sql_path = repo_root / "DIY-Model-Script" / "diy_model_script.sql"

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    cfg = load_config(config_path)
    params = load_params(cfg)
    db = load_db_settings(cfg)
    sql_batch = build_sql_batch(sql_path)

    # Import here so syntax checks don't require pyodbc installed.
    import pyodbc  # noqa: PLC0415

    cn_str = build_connection_string(
        driver=db["driver"],
        server=db["server"],
        database=db["database"],
        user=db["user"],
        password=db["password"],
        encrypt=db["encrypt"],
        trust_server_certificate=db["trust_server_certificate"],
    )

    with pyodbc.connect(cn_str) as cn:
        cur = cn.cursor()
        cur.execute(
            sql_batch,
            params["benefit_year"],
            params["start_date"],
            params["end_date"],
            params["paid_through"],
            params["state"],
            params["market"],
            params["issuer_hios"],
        )

        # Consume any result sets to avoid "results pending" issues.
        while cur.nextset():
            pass

        cn.commit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
