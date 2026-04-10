# Gestao de Demandas - Proposta de Modelo de Dados (Backend)

Objetivo: separar (1) coleta publica de demandas (formulario simples) de (2) gestao interna do mandato, onde um "caso" agrupa uma ou mais demandas coletadas e recebe campos operacionais (responsavel, prioridade, status, etapa, encaminhamento, etc.).

Este documento descreve a estrutura minima recomendada de tabelas para o backend do AssessorAI, com espaco para evolucao (IA, georreferencia, anexos, trilha de eventos).

## Conceitos

- Demand Intake (coleta): submissao individual vinda do municipe/canal. Deve preservar o que foi informado.
- Demand Case (gestao): objeto "maior" do mandato. Agrega uma ou mais intakes e concentra o workflow.
- Case Item (vinculo): associa um intake a um case e permite anotacao especifica daquele intake dentro do case.
- Case Events (timeline): registro de mensagens e eventos do case (comentarios, mudancas de status/etapa, etc.).
- Geo Extraction: resultados estruturados (lat/lng etc.) extraidos a partir de campos de texto (via prompt/IA).
- Solicitante: entidade separada (por mandato) para permitir consultas e possivel deduplicacao.

## Regras de acesso

- Todos os registros pertencem a exatamente 1 mandato (via `mandato_id`).
- A API deve garantir isolamento: usuarios so acessam dados de seus mandatos.

## Tabelas propostas

### 1) demand_solicitantes

Entidade de solicitante (municipe) vinculada ao mandato.

Campos (MVP):

- `id` (PK)
- `mandato_id` (FK `mandatos.id`, index)
- `nome` (nullable)
- `telefone` (nullable)
- `endereco_texto` (nullable)
- `created_at`
- `updated_at`

Campos (opcional - dedupe):

- `dedupe_key` (ex: telefone normalizado)
- `UNIQUE(mandato_id, dedupe_key)`

Notas:

- Mesmo com solicitante em tabela separada, vale manter um snapshot no intake para preservar "o que veio no formulario".

### 2) demand_intakes

Registro "cru" da coleta publica (mobile first) ou de outros canais.

Campos (MVP):

- `id` (PK)
- `public_id` (string/UUID, UNIQUE) para uso em links/public API
- `mandato_id` (FK `mandatos.id`, index)
- `created_at`

Conteudo do formulario:

- `tipo` (string/enum: solicitacao, denuncia, reclamacao, sugestao, elogio, outro)
- `categoria` (string; pode virar enum depois)
- `origem` (string: public_form/whatsapp/telefone/presencial/importacao/interna/outro)
- `origem_meta` (JSON/TEXT)

Solicitante:

- `solicitante_id` (FK `demand_solicitantes.id`, nullable)
- `solicitante_nome` (nullable)
- `solicitante_telefone` (nullable)
- `solicitante_endereco_texto` (nullable)

Dados da demanda:

- `demanda_endereco_texto` (nullable)
- `descricao` (TEXT)

Campos (opcional - triagem):

- `triage_status` (string/enum: nova, triada, descartada)

### 3) demand_intake_attachments

Anexos (principalmente fotos) da coleta.

Campos (MVP):

- `id` (PK)
- `mandato_id` (FK `mandatos.id`, index)
- `intake_id` (FK `demand_intakes.id`, index)
- `created_at`
- `storage_path` ou `url`
- `content_type`
- `size_bytes`
- `caption` (nullable)

### 4) demand_cases

Objeto de gestao do mandato. Concentra workflow e campos operacionais.

Campos (MVP):

- `id` (PK)
- `public_id` (string/UUID, UNIQUE; opcional)
- `mandato_id` (FK `mandatos.id`, index)
- `created_at`
- `updated_at`

Campos de lista:

- `titulo` (nullable)
- `resumo` (nullable)

Campos operacionais (mandato):

- `responsavel_user_id` (FK `users.id`, nullable, index)
- `qualificacao` (nullable)
- `prioridade` (enum/string: baixa, media, alta, urgente) (index)
- `status` (enum/string: nova, em_triagem, em_andamento, encaminhada, resolvida, arquivada) (index)
- `etapa` (string/enum do workflow interno) (index)

Encaminhamento (MVP):

- `tipo_encaminhamento` (nullable)
- `orgao_encaminhado` (nullable)
- `encaminhamento_texto` (TEXT, nullable)

Observacoes gerais (opcional):

- `observacoes_gerais` (TEXT, nullable)

Nota sobre "oficio":

- Por enquanto, nao persistir "oficio" como entidade. Quando existir uma tabela `oficios`, o case pode ganhar `oficio_id` (FK).

### 5) demand_case_items

Tabela de vinculo entre case e intake. Permite adicionar/remover intakes de um case e registrar uma observacao especifica daquele intake dentro do case.

Campos (MVP):

- `case_id` (FK `demand_cases.id`)
- `intake_id` (FK `demand_intakes.id`)
- `mandato_id` (FK `mandatos.id`, index) (redundante, mas util para filtro e seguranca)
- `added_at`
- `added_by_user_id` (FK `users.id`, nullable)
- `observacao` (TEXT, nullable)  # observacao "dessa demanda" dentro do case

Chaves/constraints recomendadas:

- PK composta: `(case_id, intake_id)`
- Se um intake deve pertencer a no maximo 1 case: `UNIQUE(intake_id)`

### 6) demand_case_events

Timeline do case (mensagens e eventos) para entendimento do processo.

Campos (MVP):

- `id` (PK)
- `mandato_id` (FK `mandatos.id`, index)
- `case_id` (FK `demand_cases.id`, index)
- `created_at`
- `created_by_user_id` (FK `users.id`, nullable)
- `event_type` (string/enum: comment, status_change, etapa_change, system, ai_suggestion, etc.)
- `body` (TEXT)
- `meta` (JSON/TEXT, nullable)  # exemplo: {"from_status": "...", "to_status": "..."}

Notas:

- Em vez de uma tabela separada de status_history, o MVP pode registrar mudancas como eventos.

### 7) demand_geo_extractions

Resultados estruturados de georreferencia extraidos a partir de texto (prompt/IA). Mantido separado para permitir reprocessamento e auditoria.

Campos (MVP):

- `id` (PK)
- `mandato_id` (FK `mandatos.id`, index)
- `source_type` (string: intake|case)
- `source_id` (int)
- `kind` (string: demanda_endereco|solicitante_endereco|outro)
- `input_text` (TEXT ou JSON/TEXT)  # snapshot do texto usado na extracao
- `latitude` (nullable)
- `longitude` (nullable)
- `confidence` (nullable)
- `provider` (nullable)
- `raw_response` (JSON/TEXT, nullable)
- `created_at`

Indices recomendados:

- `INDEX(source_type, source_id)`

## Indices minimos (performance)

- `demand_intakes(mandato_id, created_at DESC)`
- `demand_cases(mandato_id, status, etapa)`
- `demand_cases(mandato_id, prioridade)`
- `demand_cases(mandato_id, responsavel_user_id)`
- `demand_case_items(case_id)`
- `demand_case_events(case_id, created_at DESC)`
- `demand_intake_attachments(intake_id)`

## Fluxos (alto nivel)

### Coleta publica

1. Public form cria `demand_intakes` (e opcionalmente `demand_solicitantes`).
2. Upload de fotos cria `demand_intake_attachments`.
3. (Futuro) job/prompt gera `demand_geo_extractions` com base nos textos.

### Gestao do mandato

1. Gestor cria `demand_cases`.
2. Gestor adiciona 1+ `demand_intakes` no case via `demand_case_items` (inclui `observacao`).
3. Gestor atualiza campos operacionais no `demand_cases` (responsavel, prioridade, status, etapa).
4. A cada acao relevante, criar registro em `demand_case_events` (comentario/alteracao).

## Decisoes pendentes (para fechar constraints)

1) Um `demand_intake` pertence a no maximo 1 `demand_case`? (recomendado: sim, com `UNIQUE(intake_id)`).
2) Deduplicacao de solicitante: vamos deduplicar por telefone normalizado (por mandato) ou permitir duplicados no MVP?
3) Precisamos de algum status de triagem no intake (`triage_status`) ou toda triagem sera feita apenas via cases?
