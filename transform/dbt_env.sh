#!/usr/bin/env bash
set -euo pipefail

# Runs dbt with connection env vars loaded from the repo's root .env.
# This avoids common failures where dbt can't see MSSQL_* variables.
#
# Usage:
#   ./dbt_env.sh debug
#   ./dbt_env.sh build
#   ./dbt_env.sh run --select some_model

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${repo_root}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${repo_root}/.env"
  set +a
fi

# If the user didn't explicitly set MSSQL_PASSWORD, prefer MSSQL_SA_PASSWORD.
# This prevents a stale/foreign MSSQL_PASSWORD from breaking local dev.
if [[ -z "${MSSQL_PASSWORD:-}" && -n "${MSSQL_SA_PASSWORD:-}" ]]; then
  export MSSQL_PASSWORD="${MSSQL_SA_PASSWORD}"
fi

cd "${repo_root}/transform"
exec dbt "$@"
