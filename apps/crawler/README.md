# AssessorAI Crawler

Servico historico de coleta automatizada de dados legislativos da plataforma AssessorAI, criada pela [Legisla Brasil](https://legislabrasil.org/). Este app executa spiders para capturar proposicoes, metadados e arquivos publicos de diferentes casas legislativas, servindo como base para pesquisa, organizacao documental e enriquecimento de fluxos do produto.

## Arquitetura

O `apps/crawler` e a camada de coleta e operacao de dados legislativos.

- executa spiders em Scrapy;
- usa Scrapyd para orquestracao de execucoes;
- usa ScrapydWeb para monitoramento operacional;
- usa Nginx como proxy reverso para acesso unificado;
- persiste logs, items e downloads em diretorios locais de storage.

### Servicos principais

- `scrapyd`: execucao e agendamento dos spiders;
- `scrapydweb`: interface web de monitoramento;
- `logparser`: interpretacao de logs do Scrapyd;
- `nginx`: acesso consolidado aos servicos HTTP.

### Cobertura de fontes

O projeto inclui spiders para diferentes ambitos legislativos, incluindo:

- federal;
- estadual;
- municipal.

Exemplos presentes no repositorio:

- Congresso Nacional;
- Camara dos Deputados;
- ALMG, ALESP, ALEPE, ALESC, ALEP, ALBA, ALRS;
- camaras municipais como Sao Paulo, Fortaleza, Linhares, Pocos de Caldas e Sao Jose dos Campos.

### Integracoes externas

- Docker Compose para operacao local;
- Weaviate, Gemini e OpenAI em cenarios especificos, quando configurados.

## Pre-requisitos

- Docker 20.10 ou superior;
- Docker Compose 2.0 ou superior;
- recursos locais para armazenamento temporario de logs, items e downloads.

## Instalacao

```bash
cd apps/crawler
cp .env.example .env
mkdir -p storage/{logs,items,dbs,downloads}
docker compose up -d
```

Valide o estado dos servicos:

```bash
docker compose ps
```

## Configuracao Local

Use `.env.example` como base. O arquivo `.env` nao deve ser versionado.

As configuracoes padrao do exemplo cobrem o uso local basico com Docker. Tambem e necessario garantir a estrutura de armazenamento local:

```bash
mkdir -p storage/{logs,items,dbs,downloads}
```

### Operacao do Scrapyd

Variaveis principais:

- `SCRAPYD_BIND_ADDRESS`;
- `SCRAPYD_HTTP_PORT`;
- `SCRAPYDWEB_BIND`;
- `SCRAPYD_SERVERS`;
- `SCRAPYD_LOGS_DIR`.

Essas variaveis controlam a exposicao dos servicos e o roteamento entre os containers.

### Integracoes opcionais

Conforme o fluxo desejado, o projeto pode usar:

- `WEAVIATE_URL`;
- `WEAVIATE_API_KEY`;
- `WEAVIATE_CLASS`;
- `GEMINI_API_KEY`;
- `OPENAI_APIKEY`.

Essas variaveis sao opcionais e dependem dos pipelines ativados no projeto.

## Execucao

Subir os servicos:

```bash
docker compose up -d
```

Acessar a interface operacional local:

```text
http://localhost
```

Listar spiders via API:

```bash
curl http://localhost/scrapyd/listspiders.json?project=default
```

Executar um spider via API:

```bash
curl http://localhost/scrapyd/schedule.json \
  -d project=default \
  -d spider=proposicoesmg
```

Ao testar spiders localmente, prefira execucoes pequenas:

```bash
docker exec -it assessorai-scrapyd scrapy crawl es-linhares -a ano=2020 -a max_pages=1
```

## Testes E Validacao

Este app nao possui uma suite automatizada padronizada no mesmo nivel dos demais apps. A validacao minima recomendada para desenvolvimento local e:

```bash
docker compose config
docker compose up -d
docker compose ps
```

Smoke test local:

1. validar o `docker compose config`;
2. subir os containers;
3. listar spiders disponiveis;
4. executar um spider com escopo reduzido, preferencialmente com `max_pages=1`;
5. verificar logs e artefatos gerados localmente.

## Publicacao E Dados Locais

Este app foi publicado como parte de um monorepo historico sanitizado. O repositorio nao inclui:

- arquivos `.env` reais;
- credenciais privadas;
- conteudo persistido em `storage/`;
- downloads, logs, bancos locais ou outputs gerados por execucoes reais.

## Licenca

Este app esta coberto pela licenca `GNU Affero General Public License v3.0` adotada no monorepo. Consulte `../../LICENSE`.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
