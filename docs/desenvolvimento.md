# Desenvolvimento

## Subir com Docker

```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## Sem Docker (avançado)

1. Suba PostgreSQL 16 localmente.
2. Ajuste `DATABASE_URL` no `.env` para `127.0.0.1`.
3. Crie um venv e instale dependências:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

4. Build do CSS:

```bash
npm install && npm run build:css
```

## Testes

```bash
pytest
```

Requer PostgreSQL acessível (mesma `DATABASE_URL` do `.env`, ou override via env).

## Qualidade

```bash
ruff check .
black .
pre-commit install
```

## Estrutura útil

```
apps/          # domínio
config/        # settings e URLs
templates/     # HTML
static/        # CSS/JS/imagens
tests/         # testes automatizados
docs/          # documentação
docker/        # scripts de container
```
