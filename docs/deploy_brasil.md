# Deploy Jurisly no Brasil (São Paulo)

## Por que Brasil?

A API pública do DJEN/CNJ bloqueia IPs de datacenter fora do Brasil (403 no Render/Oregon).
A aplicação precisa sair de um IP brasileiro.

## Opção recomendada agora: Fly.io `gru` (São Paulo)

Não há plano “sempre grátis” contínuo no Fly.io em 2026 (trial curto). O menor machine
em `gru` fica em torno de alguns dólares/mês — é a forma mais rápida de ter IP BR + HTTPS.

Pré-requisitos: conta Fly.io (cartão) + Postgres (pode reutilizar o do Render ou Neon free).

```powershell
$env:Path = "C:\Users\Mitkawa\.fly\bin;" + $env:Path
cd "C:\Users\Mitkawa\Jurisly Projeto\Jurisly"

flyctl auth login
flyctl apps create jurisly-app
flyctl secrets set `
  SECRET_KEY="gere-uma-chave-longa" `
  DATABASE_URL="postgres://..." `
  ALLOWED_HOSTS="jurisly-app.fly.dev" `
  CSRF_TRUSTED_ORIGINS="https://jurisly-app.fly.dev"

flyctl deploy
```

URL: `https://jurisly-app.fly.dev`

## Opção 100% gratuita: Oracle Cloud Always Free (São Paulo)

1. Crie conta em https://cloud.oracle.com (home region **Brazil East / São Paulo**).
2. Suba uma VM Always Free (Ampere A1 ou E2.1.Micro).
3. Instale Docker e rode o `docker-compose` do projeto com Postgres + web.
4. Abra as portas 80/443 e use um domínio ou IP público.

Capacidade Always Free em SP às vezes esgota (“out of capacity”) — nesse caso tente
outro AD ou faça upgrade para PAYG (recursos Always Free continuam sem cobrança dentro
do limite).

## Render

Pode continuar para testes de UI, mas **DJEN não funciona** de lá (IP EUA).
