"""
Relay temporário da API DJEN com IP de saída brasileiro.

Uso local (com túnel Cloudflare/ngrok):
  set RELAY_SECRET=um-segredo-forte
  python ops/djen_relay/main.py

No Render:
  DJEN_BASE_URL=https://SEU-TUNEL.trycloudflare.com
  DJEN_RELAY_SECRET=um-segredo-forte
"""

from __future__ import annotations

import os

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, Response

DJEN_UPSTREAM = os.environ.get("DJEN_UPSTREAM", "https://comunicaapi.pje.jus.br").rstrip("/")
RELAY_SECRET = os.environ.get("RELAY_SECRET", "").strip()
HOST = os.environ.get("RELAY_HOST", "127.0.0.1")
PORT = int(os.environ.get("RELAY_PORT", "8090"))

app = FastAPI(title="Jurisly DJEN Relay", docs_url=None, redoc_url=None)


def _autorizado(header_valor: str | None) -> bool:
    if not RELAY_SECRET:
        return False
    return (header_valor or "").strip() == RELAY_SECRET


@app.get("/health/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "djen-relay"}


@app.get("/api/v1/comunicacao")
def comunicar(
    request: Request,
    x_jurisly_relay: str | None = Header(default=None, alias="X-Jurisly-Relay"),
) -> Response:
    if not _autorizado(x_jurisly_relay):
        raise HTTPException(status_code=401, detail="Relay não autorizado.")

    params = dict(request.query_params)
    with httpx.Client(
        timeout=httpx.Timeout(45.0, connect=10.0),
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Origin": "https://comunica.pje.jus.br",
            "Referer": "https://comunica.pje.jus.br/",
            "User-Agent": (
                "Mozilla/5.0 (compatible; Jurisly-Relay/0.1) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
        },
        follow_redirects=True,
    ) as client:
        upstream = client.get(f"{DJEN_UPSTREAM}/api/v1/comunicacao", params=params)

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


if __name__ == "__main__":
    if not RELAY_SECRET:
        raise SystemExit("Defina RELAY_SECRET antes de iniciar o relay.")
    print(f"DJEN relay em http://{HOST}:{PORT} -> {DJEN_UPSTREAM}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
