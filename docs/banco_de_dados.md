# Banco de dados

## PostgreSQL

Único banco suportado em desenvolvimento e produção nesta fase. SQLite não é utilizado como banco principal.

## Nomenclatura

Tudo em português, `snake_case`, minúsculo:

- tabelas: `usuarios`, `organizacoes`, `organizacoes_usuarios`, `logs_auditoria`
- colunas: `nome`, `email`, `ativo`, `data_criacao`, `data_atualizacao`
- FKs: `usuario_id`, `organizacao_id`
- constraints: `uq_organizacoes_usuarios`
- índices: `idx_logs_auditoria_data_criacao`

## Entidades

### usuarios

UUID PK · email único · nome · sobrenome · ativo · datas · ultimo_acesso  
Hash de senha via mecanismo do Django (`password`).

### organizacoes

UUID PK · nome · slug único · ativo · datas

### organizacoes_usuarios

UUID PK · organizacao_id · usuario_id · perfil · ativo · datas  
Unique `(organizacao_id, usuario_id)`.

Perfis: `PROPRIETARIO`, `ADMINISTRADOR`, `ADVOGADO`, `ASSISTENTE`, `VISUALIZADOR`.

### advogados

UUID PK · organizacao_id · usuario_id (**1:1** com usuarios) · nome · sobrenome · email · telefone · cpf · numero_oab · uf_oab · ativo · datas

Unique `(organizacao_id, numero_oab, uf_oab)`.

Na aplicação web, cada usuário autentica e edita **somente o próprio** perfil (`/meus-dados/`). Cadastro de outros advogados fica restrito ao Django Admin.

## on_delete

| Relação | Comportamento | Motivo |
|---|---|---|
| OrganizacaoUsuario → Organizacao | `PROTECT` | Evita apagar org com membros |
| OrganizacaoUsuario → Usuario | `CASCADE` | Remove vínculos se usuário for excluído |
| LogAuditoria → Org/Usuario | `SET_NULL` | Preserva histórico |
