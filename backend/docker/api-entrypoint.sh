#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS_ON_STARTUP" = "true" ]; then
  echo "RUN_MIGRATIONS_ON_STARTUP=true; running migrations"
  python scripts/run_migrations.py
else
  echo "RUN_MIGRATIONS_ON_STARTUP is not true; skipping migrations"
fi

exec "$@"
