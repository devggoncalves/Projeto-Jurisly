# Segurança

## Autenticação

- Login por e-mail + senha
- Hash via Django (PBKDF2/argon2 conforme configuração)
- Sessão cookie-based (sem JWT na aplicação web nesta fase)
- Mensagens genéricas em falha de login (anti-enumeração)
- Recuperação de senha sem confirmar existência do e-mail

## Sessão e "Lembrar de mim"

- Marcado: `session.set_expiry(SESSION_COOKIE_AGE)` (padrão 14 dias)
- Desmarcado: `session.set_expiry(0)` (expira ao fechar o navegador)

Cookies: `HttpOnly`, `SameSite=Lax`. Em produção: `Secure=True`, `SECURE_SSL_REDIRECT=True`.

## Multi-tenant

Nunca confiar em `organizacao_id` enviado pelo cliente. Validar contra `OrganizacaoUsuario` do usuário autenticado.

## Auditoria

Registra `LOGIN_SUCESSO`, `LOGIN_FALHA`, `LOGOUT`.  
Nunca registra senha, token, secret ou cookie de sessão.

## Produção

Headers e flags em `config/settings/production.py`:

- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_SSL_REDIRECT`
- `SECURE_HSTS_*`
- `SECURE_PROXY_SSL_HEADER`
