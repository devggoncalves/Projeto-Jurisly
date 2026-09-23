# Integração DJEN / CNJ

Data de validação da API pública: **22/09/2026**.

## Endpoint

- Base (produção): `https://comunicaapi.pje.jus.br`
- Recurso: `GET /api/v1/comunicacao`
- Homologação (`https://hcomunicaapi.cnj.jus.br`): timeout observado na validação; configurável via `DJEN_BASE_URL`.

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
