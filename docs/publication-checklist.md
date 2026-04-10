# Checklist Operacional de Publicacao

Checklist executavel para preparar os repositorios do monorepo `assessorai-platform` para publicacao.

Ordem recomendada de execucao:

1. `apps/crawler`
2. `apps/client`
3. `apps/server`
4. Revisao final do monorepo

## Como usar

- `Bloqueador`: precisa estar resolvido antes de qualquer publicacao publica.
- `Importante`: deve estar resolvido para uma publicacao tecnica confiavel.
- `Desejavel`: melhora manutencao, onboarding e apresentacao do projeto.

## Fase 0: Decisao de Escopo

### Bloqueador

- [ ] Definir se cada app sera publico completo, publico sanitizado ou privado.
- [ ] Definir se o monorepo publico contera codigo executavel dos tres apps ou apenas parte deles.
- [ ] Definir se a apresentacao publica tera demo funcional, capturas de tela ou apenas landing page institucional.

### Importante

- [ ] Definir a licenca que sera usada em cada app e no monorepo.
- [ ] Definir o nivel de suporte publico esperado: issues, PRs, contribuicoes externas.

## Fase 1: `apps/crawler`

Status atual observado: risco alto.

### Bloqueador

- [ ] Remover `.env` real do diretorio do projeto.
- [ ] Revogar e rotacionar credenciais expostas anteriormente, se estas chaves tiverem sido usadas de verdade.
- [ ] Verificar se essas credenciais entraram no historico Git que sera publicado.
- [ ] Remover `storage/` e qualquer massa de dados gerada do conteudo a publicar.
- [ ] Remover downloads, outputs, logs, bancos e duplicacoes como `storage/storage/`.
- [ ] Confirmar que o `.gitignore` cobre todo artefato operacional gerado localmente.
- [ ] Revisar scripts e modulos por chaves hardcoded ou endpoints privados.

### Importante

- [ ] Definir se algum dataset pequeno e sanitizado sera mantido como exemplo.
- [ ] Revisar `README.md` para uso externo e reduzir foco em operacao interna.
- [ ] Confirmar o fluxo minimo de execucao publica: Docker, Compose, Scrapyd, ScrapydWeb.
- [ ] Documentar um smoke test pequeno e barato, por exemplo um spider com escopo reduzido.
- [ ] Revisar nomes de imagens, containers e instrucoes para refletir padrao publico.
- [ ] Revisar se o workflow de Docker publica a imagem correta para o repositorio correto.

### Desejavel

- [ ] Adicionar uma secao explicando limites legais, eticos e operacionais de scraping.
- [ ] Adicionar exemplos pequenos de comando para rodar um spider com baixa carga.
- [ ] Adicionar uma secao de arquitetura resumida para quem chega de fora.

### Criterio de pronto

- [ ] Nenhuma credencial real no repo.
- [ ] Nenhuma massa de dados operacional versionada.
- [ ] Ambiente minimo sobe com documentacao clara.
- [ ] Existe um smoke test pequeno e reproduzivel.

## Fase 2: `apps/client`

Status atual observado: risco medio.

### Bloqueador

- [ ] Remover `.env` real do conteudo a publicar.
- [ ] Verificar se segredos reais entraram no historico Git.
- [ ] Revisar o codigo para garantir que nenhuma URL privada ou segredo esta hardcoded fora de arquivos de exemplo.
- [ ] Garantir que apenas `.env.example` permanece exposto.

### Importante

- [ ] Alinhar a versao do Node na CI com a versao documentada no README.
- [ ] Validar `npm install`.
- [ ] Validar `npm run build`.
- [ ] Validar `npm run lint`.
- [ ] Validar `npm run test`.
- [ ] Revisar `README.md` para publico externo.
- [ ] Substituir placeholders como link de documentacao externa, se for manter a referencia.
- [ ] Explicar claramente a dependencia do backend e como rodar sem ambiente privado.

### Desejavel

- [ ] Definir uma estrategia de demo publica: mock, staging ou backend publico controlado.
- [ ] Adicionar capturas de tela ou GIFs curtos no README.
- [ ] Adicionar uma secao curta de arquitetura BFF com diagrama simplificado.

### Criterio de pronto

- [ ] Nenhum `.env` real no repo.
- [ ] Build, lint e testes funcionando no ambiente documentado.
- [ ] README compreensivel para terceiros.
- [ ] CI coerente com a stack real.

## Fase 3: `apps/server`

Status atual observado: risco medio.

### Bloqueador

- [ ] Confirmar que nao existe `.env` real no repo.
- [ ] Revisar se ha arquivos sensiveis como `google-key.json`, bancos locais ou credenciais residuais.
- [ ] Verificar se segredos ou dados sensiveis entraram no historico Git.
- [ ] Revisar dados de exemplo em `data/` e manter apenas o que puder ser publico.

### Importante

- [ ] Corrigir o workflow de CI para instalar o projeto da forma real usada pelo repositorio.
- [ ] Alinhar CI com `pyproject.toml` e os comandos efetivos de teste.
- [ ] Validar instalacao local documentada.
- [ ] Validar subida da API.
- [ ] Validar testes automatizados relevantes.
- [ ] Revisar Dockerfile e instrucoes de deploy para uso publico.
- [ ] Revisar README para remover referencias internas e fluxos legados desnecessarios.
- [ ] Confirmar se o console admin Streamlit deve estar no repo publico ou apenas documentado.

### Desejavel

- [ ] Adicionar uma secao de arquitetura do backend para terceiros.
- [ ] Documentar melhor dependencias opcionais e servicos externos.
- [ ] Adicionar uma matriz simples de funcionalidades disponiveis com e sem servicos externos.

### Criterio de pronto

- [ ] Nenhum segredo ou arquivo sensivel no repo.
- [ ] CI verde com instalacao correta.
- [ ] API sobe conforme README.
- [ ] Testes e docs estao alinhados.

## Fase 4: Revisao do Monorepo

### Bloqueador

- [ ] Garantir que o monorepo nao reintroduz arquivos sensiveis copiados dos apps.
- [ ] Revisar o escopo publico final dos tres diretorios em `apps/`.
- [ ] Confirmar que o GitHub Pages nao expoe links quebrados ou detalhes internos indevidos.

### Importante

- [ ] Atualizar o `README.md` raiz com o status publico real de cada app.
- [ ] Adicionar uma tabela com disponibilidade por app: publico, sanitizado, privado.
- [ ] Adicionar uma secao "o que nao esta incluido".
- [ ] Definir padrao de contribuicao e manutencao do monorepo.

### Desejavel

- [ ] Adicionar `CONTRIBUTING.md` central.
- [ ] Adicionar `.gitignore` central se o monorepo passar a ter fluxos de desenvolvimento proprios.
- [ ] Adicionar automacao comum para setup local.

## Go / No-Go Final

Publicar apenas quando todos os itens abaixo estiverem verdadeiros:

- [ ] Nenhum segredo real no conteudo atual dos repositorios.
- [ ] Nenhum segredo real no historico Git a ser publicado.
- [ ] Nenhum dado operacional pesado ou sensivel versionado sem intencao.
- [ ] CI minimo funcionando para os apps que serao publicos.
- [ ] READMEs estao claros para terceiros.
- [ ] Licencas estao definidas.
- [ ] O escopo publico foi aprovado.

## Execucao Recomendada

### Sprint 1: saneamento critico

- [ ] Sanear `apps/crawler`
- [ ] Remover `.env` real de `apps/client`
- [ ] Revisar presenca de arquivos sensiveis em `apps/server`

### Sprint 2: build e documentacao

- [ ] Corrigir CI de `apps/client`
- [ ] Corrigir CI de `apps/server`
- [ ] Revisar READMEs dos tres apps

### Sprint 3: consolidacao publica

- [ ] Atualizar README raiz do monorepo
- [ ] Revisar GitHub Pages
- [ ] Definir publicacao final repo a repo
