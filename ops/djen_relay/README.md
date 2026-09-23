# DJEN Relay (temporário — IP brasileiro)

Serviço mínimo em São Paulo que encaminha `GET /api/v1/comunicacao` para a API pública do CNJ.

O Jurisly (Render/EUA) chama este relay; o CNJ vê o IP do relay no Brasil. **Usuários em qualquer lugar** usam o app normalmente — a geolocalização relevante é a do servidor, não a do navegador.

## Deploy (Fly.io `gru`)

```bash
cd ops/djen_relay
fly auth login
fly apps create jurisly-djen-relay --org personal
fly secrets set RELAY_SECRET="gere-um-segredo-forte"
fly deploy
```

URL típica: `https://jurisly-djen-relay.fly.dev`

## No Render (Environment)

| Variável | Valor |
|---|---|
| `DJEN_BASE_URL` | `https://jurisly-djen-relay.fly.dev` |
| `DJEN_RELAY_SECRET` | o mesmo `RELAY_SECRET` |
| `DJEN_HTTP_PROXY` | *(deixar vazio)* |

Depois: **Manual Deploy** do Jurisly (ou restart do serviço) para pegar as envs.

## Quando migrar a hospedagem para o Brasil

Pode desligar este relay e voltar:

- `DJEN_BASE_URL=https://comunicaapi.pje.jus.br`
- remover `DJEN_RELAY_SECRET`
