# Integração DJEN / CNJ

Data de validação da API pública: **22/09/2026**.

## Endpoint

- Base (produção): `https://comunicaapi.pje.jus.br`
- Recurso: `GET /api/v1/comunicacao`
- Homologação (`https://hcomunicaapi.cnj.jus.br`): timeout observado na validação; configurável via `DJEN_BASE_URL`.

## Bloqueio 403 em nuvem internacional

A API passa por CloudFront e frequentemente responde **403** para IPs fora do Brasil
(datacenters nos EUA/Europa, como o plano free do Render em Oregon).

Importante: o bloqueio é no **IP de saída do servidor** Jurisly, não no IP do usuário.
Advogados acessando do Brasil pelo navegador continuam ok — quem precisa de IP BR é a
máquina que chama `comunicaapi.pje.jus.br`.

- Local (IP residencial BR): funciona.
- Render / Fly US / etc.: pode falhar com 403.

Mitigações:

1. Hospedar a aplicação em região/IP brasileiro (ex.: Fly.io `gru`, VPS BR).
2. Ou configurar `DJEN_HTTP_PROXY` com um proxy HTTP(S) cuja saída seja IP brasileiro.
3. **Temporário (multi-usuário):** relay 24/7 em São Paulo (`ops/djen_relay` no Fly.io `gru`).
   O Render aponta `DJEN_BASE_URL` para o relay; todos os usuários do SaaS passam a
   receber dados DJEN independentemente de onde estejam.

Ver `ops/djen_relay/README.md`.

## Parâmetros usados pelo Jurisly

| Parâmetro API | Origem no Jurisly |
|---|---|
| `numeroOab` | `InscricaoOab.numero` |
| `ufOab` | `InscricaoOab.uf` |
| `dataDisponibilizacaoInicio` / `Fim` | formulário de consulta |
| `nomeAdvogado` | `Advogado.nome_consulta` ou `nome_completo` |
| `nomeParte`, `numeroProcesso`, `siglaTribunal`, `texto` | filtros opcionais da tela de teste |
| `pagina`, `itensPorPagina` | paginação |

**CPF:** não existe filtro na API pública. O campo permanece no cadastro do advogado apenas para uso interno.

## Envelope observado

```json
{ "status": "success", "message": "Sucesso", "count": 0, "items": [] }
```

## Rate limit (headers observados)

- `x-ratelimit-limit`
- `x-ratelimit-remaining`

## Regras de negócio (fase atual)

- Chamadas **somente no backend** (`ClienteDjen` + `ServicoConsultaDjen`).
- Comunicação encontrada inicia como `PENDENTE` em `ComunicacaoAdvogado` (encontrada ≠ confirmada).
- Deduplicação: `fonte=DJEN` + `identificador_externo` (preferência pelo `hash`).

## UI temporária

Menu lateral **Consultas DJEN** (`/consultas/djen/`) — uso para inspecionar payloads. Será removido/incorporado ao dashboard principal depois.
