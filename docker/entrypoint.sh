#!/usr/bin/env sh
set -eu

umask 027

DB_URL="${HMS_DB_URL:-sqlite:///hospital.db}"

case "${DB_URL}" in
    sqlite:////*)
      SQLITE_DB_PATH="${DB_URL#sqlite:////}"
      ;;
    sqlite:///*)
      SQLITE_DB_PATH="/app/${DB_URL#sqlite:///}"
      ;;
    *)
      SQLITE_DB_PATH=""
      ;;
esac

if [ -n "${SQLITE_DB_PATH}" ]; then
  SQLITE_DB_DIR="$(dirname "${SQLITE_DB_PATH}")"
  mkdir -p "${SQLITE_DB_DIR}"
  touch "${SQLITE_DB_PATH}"
  chmod 600 "${SQLITE_DB_PATH}" || true
fi

python -c "from core.models import init_db; from core.auth import seed_default_data; init_db(); seed_default_data()"

exec "$@"
