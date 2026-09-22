# Jurisly

Plataforma WEB SaaS para advogados e escritórios de advocacia.

Esta é a **Fase 01**: fundação do projeto, PostgreSQL, autenticação, organizações, auditoria e tela de login.

## Pré-requisitos

- Docker e Docker Compose
- (Opcional, sem Docker) Python 3.13+, PostgreSQL 16+, Node.js 22+ para build do CSS

## Configuração rápida (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Em outro terminal:

```bash
docker compose exec web python manage.py createsuperuser
```

Acesse:

- Login: http://localhost:8000/login/
- Dashboard: http://localhost:8000/dashboard/
- Health: http://localhost:8000/health/
- Admin: http://localhost:8000/admin/

## Variáveis de ambiente

Veja `.env.example`. Nunca versionar o arquivo `.env`.

Principais:

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django |
| `DEBUG` | `True` apenas em desenvolvimento |
| `DATABASE_URL` | URL PostgreSQL |
| `SESSION_COOKIE_AGE` | Duração da sessão com "Lembrar de mim" (segundos) |

## Migrations

```bash
docker compose exec web python manage.py migrate
```

## Testes

```bash
docker compose exec web pytest
```

## Qualidade

```bash
docker compose exec web ruff check .
docker compose exec web black --check .
```

## Parar containers

```bash
docker compose down
```

## Documentação

- [Arquitetura](docs/arquitetura.md)
- [Banco de dados](docs/banco_de_dados.md)
- [Segurança](docs/seguranca.md)
- [Desenvolvimento](docs/desenvolvimento.md)

## Build do CSS (Tailwind)

Com Node local:

```bash
npm install
npm run build:css
```

Ou via CLI standalone:

```bash
./tailwindcss.exe -i ./static/src/input.css -o ./static/css/app.css --minify
```
