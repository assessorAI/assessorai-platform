# AssessorAI Crawler

Sistema de web scraping para coleta automatizada de proposições legislativas de diversas casas legislativas brasileiras.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
- [Spiders Disponíveis](#spiders-disponíveis)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estrutura de Dados](#estrutura-de-dados)
- [Desenvolvimento](#desenvolvimento)
- [Manutenção](#manutenção)

## 🎯 Sobre o Projeto

O AssessorAI Crawler é uma solução baseada em Scrapy para extração de proposições legislativas de múltiplas casas legislativas brasileiras. O sistema utiliza Scrapyd para gerenciamento de spiders em produção e ScrapydWeb para interface de monitoramento.

### Principais Funcionalidades

- ✅ Scraping automatizado de proposições legislativas
- ✅ Suporte a múltiplas casas legislativas (estaduais e municipais)
- ✅ Interface web para gerenciamento (ScrapydWeb)
- ✅ Download de arquivos associados (PDFs, imagens, etc.)
- ✅ Sistema de validação e pipeline de processamento
- ✅ Armazenamento persistente de dados e logs
- ✅ Proxy reverso Nginx para acesso unificado

## 🏗️ Arquitetura

O sistema é composto por 4 containers Docker orquestrados via Docker Compose:

```
┌─────────────────────────────────────────────────┐
│                    NGINX                        │
│            (Proxy Reverso - :80)                │
└─────────┬───────────────────────────┬───────────┘
          │                           │
    ┌─────▼─────┐             ┌───────▼────────┐
    │  SCRAPYD  │             │  SCRAPYDWEB    │
    │   :6800   │◄────────────┤     :5000      │
    └─────┬─────┘             └────────────────┘
          │
    ┌─────▼─────┐
    │ LOGPARSER │
    │           │
    └───────────┘
```

### Containers

- **nginx**: Proxy reverso para acesso unificado aos serviços
- **scrapyd**: Daemon do Scrapy para execução dos spiders
- **scrapydweb**: Interface web para gerenciamento e monitoramento
- **logparser**: Parser de logs do Scrapyd

### Volumes

- **scrapyd-eggs**: Armazena projetos deployados
- **./storage**: Diretório local com todos os dados persistentes
  - `logs/`: Logs de execução dos spiders
  - `items/`: Items extraídos em formato JSON
  - `dbs/`: Databases SQLite
  - `downloads/`: Arquivos baixados pelos spiders

## 🕷️ Spiders Disponíveis

### Âmbito Federal

| Spider | Nome | Casa Legislativa |
|--------|------|------------------|
| `proposicoescn` | ProposicoesCNSpider | Congresso Nacional |
| `proposicoespcd` | ProposicoesPCDSpider | Câmara dos Deputados |

### Âmbito Estadual

| Spider | Nome | Estado |
|--------|------|--------|
| `proposicoesba` | ProposicoesBASpider | Bahia (ALBA) |
| `proposicoesmg` | ProposicoesMGSpider | Minas Gerais (ALMG) |
| `proposicoespe` | ProposicoesPESpider | Pernambuco (ALEPE) |
| `proposicoespr` | ProposicoesPRSpider | Paraná (ALEP) |
| `proposicoesrs` | ProposicoesRSSpider | Rio Grande do Sul (ALRS) |
| `proposicoessc` | ProposicoesSCSpider | Santa Catarina (ALESC) |
| `proposicoessp` | ProposicoesSPSpider | São Paulo (ALESP) |

### Âmbito Municipal

| Spider | Nome | Município |
|--------|------|-----------|
| `proposicoescidsp` | ProposicoescidspSpider | São Paulo (CMSP) |
| `proposicoesfortaleza` | ProposicoesFortalezaSpider | Fortaleza |
| `proposicoeslinhares` | ProposicoesLinharesSpider | Linhares |
| `proposicoespocosdecaldas` | ProposicoesPocosDeCaldasSpider | Poços de Caldas |
| `proposicoessjc` | ProposicoesSJCSpider | São José dos Campos |

## 📦 Requisitos

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM mínimo
- 10GB espaço em disco (recomendado)

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/pmarkun/assessorai_crawler.git
cd assessorai_crawler
```

### 2. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Exemplo de variáveis de ambiente
WEAVIATE_URL=http://weaviate:8080
GOOGLE_API_KEY=your_api_key_here
```

O repositório publico nao deve conter `.env` real, arquivos baixados, bancos ou artefatos de scraping gerados localmente.

### 3. Crie a Estrutura de Storage

```bash
mkdir -p storage/{logs,items,dbs,downloads}
```

Esses diretorios sao somente locais e estao fora da publicacao do monorepo.

### 4. Inicie os Containers

```bash
docker compose up -d
```

### 5. Verifique o Status

```bash
docker compose ps
```

Todos os containers devem estar com status `Up`.

## 💻 Uso

### Interface Web

Acesse o ScrapydWeb através do navegador:

```
http://localhost
```

### Executar um Spider via Interface

1. Acesse http://localhost
2. Navegue até "Jobs" → "Run"
3. Selecione o spider desejado
4. Configure os parâmetros (se necessário)
5. Clique em "Run"

### Executar um Spider via API

```bash
# Listar spiders disponíveis
curl http://localhost/scrapyd/listspiders.json?project=default

# Executar um spider
curl http://localhost/scrapyd/schedule.json \
  -d project=default \
  -d spider=proposicoesmg

# Verificar status
curl http://localhost/scrapyd/listjobs.json?project=default
```

### Executar um Spider via CLI (Local)

```bash
# Dentro do container
docker exec -it assessorai-scrapyd bash
scrapy crawl proposicoesmg

# Ou diretamente
docker exec -it assessorai-scrapyd scrapy crawl proposicoesmg
```

### Executar Múltiplos Spiders

```bash
# Script para executar todos os spiders
for spider in proposicoesba proposicoesmg proposicoessp; do
  curl http://localhost/scrapyd/schedule.json \
    -d project=default \
    -d spider=$spider
done
```

## 📊 Estrutura de Dados

### Item de Proposição

Os items extraídos seguem uma estrutura padrão:

```json
{
  "id": "string",
  "numero": "string",
  "ano": "integer",
  "tipo": "string",
  "ementa": "string",
  "autor": "string",
  "data_apresentacao": "string (YYYY-MM-DD)",
  "situacao": "string",
  "url": "string",
  "url_inteiro_teor": "string",
  "files": ["array de URLs de arquivos"],
  "origem": "string (fonte dos dados)"
}
```

### Localização dos Dados

```
storage/
├── items/
│   └── default/
│       ├── proposicoesmg/
│       │   └── items-YYYY-MM-DD_HH-MM-SS.jl
│       └── proposicoessp/
│           └── items-YYYY-MM-DD_HH-MM-SS.jl
├── logs/
│   └── default/
│       └── proposicoesmg/
│           └── log-YYYY-MM-DD_HH-MM-SS.log
└── downloads/
    └── full/
        └── [hash]/
            └── arquivo.pdf
```

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
assessorai_crawler/
├── assessorai_crawler/
│   ├── __init__.py
│   ├── items.py           # Definição dos items
│   ├── middlewares.py     # Middlewares customizados
│   ├── pipelines.py       # Pipelines de processamento
│   ├── settings.py        # Configurações do Scrapy
│   ├── utils.py           # Funções utilitárias
│   └── spiders/
│       ├── __init__.py
│       ├── proposicoeslegislapi.py  # Spider base para APIs Legislativas
│       └── [outros spiders].py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── scrapy.cfg
├── scrapyd.conf
└── nginx.conf
```

### Criar um Novo Spider

```bash
# Dentro do container
docker exec -it assessorai-scrapyd bash
scrapy genspider nome_spider domain.com

# Ou localmente (se tiver Scrapy instalado)
scrapy genspider nome_spider domain.com
```

### Testar um Spider

```bash
# Teste rápido (10 items)
docker exec -it assessorai-scrapyd scrapy crawl proposicoesmg -s CLOSESPIDER_ITEMCOUNT=10

# Com output em arquivo
docker exec -it assessorai-scrapyd scrapy crawl proposicoesmg -o /app/storage/items/test.json

# Com logs detalhados
docker exec -it assessorai-scrapyd scrapy crawl proposicoesmg -L DEBUG
```

### Deploy de Alterações

Após modificar o código:

```bash
# Rebuild e restart
docker compose down
docker compose build
docker compose up -d
```

Ou apenas restart (se montou o código como volume):

```bash
docker compose restart scrapyd
```

## 🛠️ Manutenção

### Visualizar Logs

```bash
# Logs do container
docker compose logs -f scrapyd

# Logs específicos de um spider
docker exec -it assessorai-scrapyd cat /app/storage/logs/default/proposicoesmg/latest.log

# Via interface web
# http://localhost/scrapyd/logs/
```

### Limpar Dados Antigos

```bash
# Limpar logs com mais de 30 dias
find storage/logs -type f -mtime +30 -delete

# Limpar items processados
rm -rf storage/items/default/*/items-*.jl
```

### Backup

```bash
# Backup completo do storage
tar czf backup-storage-$(date +%Y%m%d).tar.gz storage/

# Backup apenas dos items
tar czf backup-items-$(date +%Y%m%d).tar.gz storage/items/
```

### Monitoramento

```bash
# Status dos containers
docker compose ps

# Uso de recursos
docker stats

# Jobs em execução
curl http://localhost/scrapyd/listjobs.json?project=default | jq
```

### Atualizar Dependências

```bash
# Edite requirements.txt
vim requirements.txt

# Rebuild da imagem
docker compose build

# Restart dos containers
docker compose down
docker compose up -d
```

## 🔍 Troubleshooting

### Container não inicia

```bash
# Verificar logs
docker compose logs scrapyd

# Verificar configuração
docker compose config
```

### Spider falha ao executar

```bash
# Verificar logs detalhados
docker exec -it assessorai-scrapyd scrapy crawl proposicoesmg -L DEBUG

# Verificar conectividade
docker exec -it assessorai-scrapyd curl -I https://www.almg.gov.br
```

### Storage cheio

```bash
# Verificar uso de disco
du -sh storage/*

# Limpar logs antigos
docker exec -it assessorai-scrapyd find /app/storage/logs -mtime +7 -delete
```

### Resetar ambiente

```bash
# CUIDADO: Remove todos os dados!
docker compose down -v
rm -rf storage/*
mkdir -p storage/{logs,items,dbs,downloads}
docker compose up -d
```

## 📝 Licença

Este projeto está sob a licença [especificar licença].

## 👥 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📧 Contato

Projeto AssessorAI - [@pmarkun](https://github.com/pmarkun)

---

**Nota**: Este projeto faz parte da iniciativa AssessorAI para democratização do acesso a dados legislativos brasileiros.
