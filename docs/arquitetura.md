# Arquitetura — Fase 01

## Visão geral

O Jurisly é um monólito modular Django preparado para evoluir como SaaS multi-tenant.

```
Internet → Reverse Proxy (futuro) → Django
                                    ├── PostgreSQL
                                    ├── Redis (futuro)
                                    └── Celery (futuro)
```

## Módulos

| App | Responsabilidade |
|---|---|
| `apps.contas` | Usuário customizado, autenticação, recuperação de senha |
| `apps.organizacoes` | Organizações e vínculos usuário/organização |
| `apps.auditoria` | Logs de eventos sensíveis (login/logout) |
| `apps.core` | Healthcheck, dashboard temporário, utilidades |

## Settings

- `config/settings/base.py` — compartilhado
- `config/settings/local.py` — desenvolvimento
- `config/settings/production.py` — produção

## Multi-tenancy

**Shared database + shared schema.**

Isolamento lógico por `organizacao_id`. Helpers em `apps.organizacoes.services` garantem que filtros partam dos vínculos do usuário autenticado — nunca de um ID enviado pelo cliente sem validação.

## Frontend

Django Templates + Tailwind CSS + HTMX (preparado). Login usa POST tradicional.

## APIs

Django REST Framework instalado e configurado, sem endpoints de negócio nesta fase.
