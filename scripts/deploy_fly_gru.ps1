# Deploy Jurisly no Fly.io (São Paulo / gru)
# Pré-requisito: flyctl auth login (já logado)

$ErrorActionPreference = "Stop"
$env:Path = "C:\Users\Mitkawa\.fly\bin;" + $env:Path
Set-Location "C:\Users\Mitkawa\Jurisly Projeto\Jurisly"

flyctl auth whoami

$app = "jurisly-app"
$secretKey = -join ((48..57 + 65..90 + 97..122) | Get-Random -Count 64 | ForEach-Object { [char]$_ })

# App
$apps = flyctl apps list --json 2>$null | ConvertFrom-Json
if (-not ($apps | Where-Object { $_.Name -eq $app })) {
  flyctl apps create $app --org personal
}

# Postgres gerenciado no mesmo app/org (região gru)
$pgName = "jurisly-db"
$pgExists = $false
try {
  flyctl postgres list --json 2>$null | ConvertFrom-Json | ForEach-Object {
    if ($_.Name -eq $pgName) { $pgExists = $true }
  }
} catch {}

if (-not $pgExists) {
  Write-Host "Criando Postgres em gru (pode levar alguns minutos)..."
  flyctl postgres create --name $pgName --region gru --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1 --org personal
}

Write-Host "Anexando Postgres ao app..."
flyctl postgres attach $pgName --app $app

flyctl secrets set `
  SECRET_KEY="$secretKey" `
  ALLOWED_HOSTS="$app.fly.dev,localhost" `
  CSRF_TRUSTED_ORIGINS="https://$app.fly.dev" `
  --app $app

Write-Host "Deploy..."
flyctl deploy --app $app --region gru

Write-Host ""
Write-Host "Pronto: https://$app.fly.dev"
Write-Host "Admin: admin@jurisly.com / SenhaForte123!"
Write-Host "Demo:  advogado@jurisly.com / advogado123"
