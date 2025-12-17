# dbt transforms + docs (SQL Server)

This repo includes a dbt project in `transform/` that targets the same SQL Server database created by `containers/mssql/init/bootstrap.sql`.

## Quickstart

Note: this project uses `dbt-sqlserver`, which depends on `pyodbc`. Use Python 3.12 (or 3.11); Python 3.13 may fail to build `pyodbc`.

1) Start SQL Server + init

```bash
podman compose -f containers/mssql/docker-compose.yml up -d
podman compose -f containers/mssql/docker-compose.yml logs -f mssql-init
```

2) Install dbt (SQL Server adapter)

```bash
# If you use uv, a reliable setup is:
#   uv python install 3.12
#   uv venv --python 3.12 .venv
#   source .venv/bin/activate

python -m pip install -r transform/requirements.txt
```

3) Configure your dbt profile

```bash
mkdir -p ~/.dbt
cp transform/profiles/profiles.yml ~/.dbt/profiles.yml
```

The profile reads connection info from env vars. The repo uses `.env` for the container, and dbt will also pick up values from your shell environment.

If you prefer hardcoding local credentials (no env vars), copy the gitignored template and edit it:

```bash
mkdir -p ~/.dbt
cp transform/profiles/profiles.local.yml ~/.dbt/profiles.yml
# edit ~/.dbt/profiles.yml and set the password
```

If `dbt debug` fails with `Login failed for user`, it usually means your current shell doesn't have the repo's `.env` values exported (dbt does not automatically read `.env`), or you have a stale `MSSQL_PASSWORD` overriding the intended password.

4) Run dbt

```bash
cd transform
dbt deps
dbt build
dbt docs generate
python make_static_docs.py
```

Optional helper (loads repo `.env` and runs dbt from `transform/`):

```bash
./dbt_env.sh debug
./dbt_env.sh build
```
