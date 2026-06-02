# Notas de Publicacao

Registro publico da preparacao do monorepo `assessorai-platform` para publicacao como projeto historico da Legisla Brasil.

## Escopo Publicado

O repositorio publica os principais componentes da plataforma AssessorAI:

- `apps/server`: backend FastAPI e console administrativo Streamlit;
- `apps/client`: frontend web Next.js e rotas BFF;
- `apps/crawler`: infraestrutura de coleta legislativa com Scrapy/Scrapyd;
- `docs/`: site estatico de apresentacao para GitHub Pages.

O codigo e apresentado como base historica e sanitizada. Ele pode ser estudado, executado localmente e adaptado nos termos da AGPL v3.0, sem promessa de suporte operacional continuo.

## Criterios De Publicacao Aplicados

- Licenca consolidada em `GNU Affero General Public License v3.0`.
- Documentacao publica revisada para remover pendencias internas e linguagem de rascunho.
- Creditos institucionais e de desenvolvimento incluidos nos pontos publicos principais.
- Arquivos de ambiente reais, credenciais, bancos locais, caches, logs e dados operacionais nao fazem parte do conteudo publicado.
- Cada app preserva instrucoes proprias de instalacao, configuracao local e validacao minima.

## Conteudo Nao Publicado

- Credenciais reais e arquivos `.env`.
- Arquivos locais de servicos externos, como chaves do Google Cloud.
- Dados sensiveis, bancos locais e massas operacionais.
- Logs, downloads e outputs persistidos por execucoes do crawler.
- Ambientes privados, staging, producao ou demonstracoes hospedadas.

## Suporte E Manutencao

O repositorio e publicado em regime de arquivo historico. Issues e pull requests podem ser avaliados em melhor esforco, especialmente quando tratarem de:

- documentacao;
- reproducibilidade local;
- remocao de referencias internas residuais;
- seguranca;
- manutencao comunitaria.

Nao ha SLA de resposta, compromisso de roadmap ou garantia de correcao para todas as branches historicas.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
