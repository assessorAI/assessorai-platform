# Operacao e Configuracao

Guia consolidado para ambiente, deploy e importacao vetorial.

## Ambiente

Use `.env-sample` como base. Variaveis essenciais:

- Banco: `DATABASE_URL`, `SQL_ECHO`
- OpenAI: `OPENAI_API_KEY`
- Google: `GOOGLE_APPLICATION_CREDENTIALS` ou `GOOGLE_APPLICATION_BASE64`,
  `GCS_BUCKET_NAME`
- Email: `SENDGRID_API_KEY`, `SENDGRID_SENDER_EMAIL`, `SENDGRID_SENDER_NAME`
- App: `FRONTEND_URL`, `CORS_ORIGINS`, `DEBUG`
- Deploy/migracao: `DB_REFRESH_MODE` (`incremental` por padrao)

## Deploy

- Deploy atual: Railway sincronizado por push nas branches `dev`, `staging` e
  `production`.
- O container executa `scripts/entrypoint.sh`, que roda `scripts/manage_db.py`
  antes de subir a API.

## Importacao vetorial

### Formato esperado

JSON com lista de itens contendo os campos usados pelo importador
(`titulo`/`content` e metadados de origem). Mantenha encoding UTF-8.

### Fluxo recomendado

1. Subir arquivo pelo admin (`Admin Importador Vetorial`).
2. Processar em lotes.
3. Validar stats no painel admin.

### Controles de performance

- `VECTOR_IMPORT_BATCH_SIZE`: tamanho do lote por submissao.
- `EMBEDDING_BATCH_SIZE`: tamanho do lote enviado a embeddings.
- `VECTOR_BATCH_SIZE`: lote para inserts no banco vetorial.

### Concorrencia e seguranca operacional

- Evite rodar multiplas importacoes pesadas ao mesmo tempo.
- Prefira executar importacoes grandes fora de horarios de pico.
- Se houver falha, reduza batch size e tente novamente.
