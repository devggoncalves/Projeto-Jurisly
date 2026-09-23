#!/bin/sh
set -e

echo "Aguardando PostgreSQL..."
python <<'PY'
import os
import time
from urllib.parse import urlparse

import psycopg

url = os.environ.get("DATABASE_URL", "")
parsed = urlparse(url)
deadline = time.time() + 90

while time.time() < deadline:
    try:
        with psycopg.connect(
            dbname=parsed.path.lstrip("/") or "jurisly",
            user=parsed.username or "jurisly",
            password=parsed.password or "jurisly",
            host=parsed.hostname or "db",
            port=parsed.port or 5432,
        ):
            print("PostgreSQL disponível.")
            break
    except Exception as exc:  # noqa: BLE001
        print(f"Aguardando banco... ({exc})")
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL não ficou disponível a tempo.")
PY

if [ "${RUN_MIGRATE:-1}" = "1" ]; then
  echo "Aplicando migrations..."
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  echo "Coletando estáticos..."
  python manage.py collectstatic --noinput
fi

if [ "${SEED_DEMO:-0}" = "1" ]; then
  echo "Garantindo usuário demo..."
  python manage.py criar_advogado_demo || true
  echo "Garantindo admin do sistema..."
  python manage.py criar_admin_sistema || true
fi

exec "$@"
