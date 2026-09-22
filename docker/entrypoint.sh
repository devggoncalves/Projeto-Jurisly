#!/bin/sh
set -e

echo "Aguardando PostgreSQL..."
python <<'PY'
import os
import time

import psycopg
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
parsed = urlparse(url)
deadline = time.time() + 60

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

exec "$@"
