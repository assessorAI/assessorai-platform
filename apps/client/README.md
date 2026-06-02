# AssessorAI Client

Frontend web historico da plataforma AssessorAI, criada pela [Legisla Brasil](https://legislabrasil.org/). Este app organiza a experiencia do produto para autenticacao, configuracao de mandatos, producao legislativa assistida, administracao e atendimento de demandas, atuando tambem como BFF para a API principal.

## Arquitetura

O `apps/client` e a camada de experiencia do produto na web.

- entrega a interface principal da plataforma;
- usa Next.js App Router com React 19;
- implementa rotas BFF em `src/app/api/` para consumo autenticado do backend;
- concentra fluxos de autenticacao, configuracao de mandato e operacao legislativa;
- possui area administrativa para gestao de usuarios e mandatos.

### Componentes principais

- `src/app/`: paginas e rotas App Router;
- `src/app/api/`: rotas BFF para comunicacao com a API;
- `src/features/`: modulos de negocio por dominio;
- `src/components/`: componentes reutilizaveis de interface;
- `src/config/`: configuracoes globais e endpoints;
- `src/test/`: testes com Jest e Testing Library.

### Integracoes externas

- API principal AssessorAI;
- Auth.js / NextAuth para autenticacao;
- Google Places API para autocomplete e endereco;
- ferramentas opcionais de analytics e suporte.

## Pre-requisitos

- Node.js 20 ou superior;
- npm 10 ou superior;
- acesso a uma instancia local ou remota do backend AssessorAI.

## Instalacao

```bash
cd apps/client
npm install
cp .env.example .env.local
```

Depois de preencher `.env.local`, inicie o ambiente de desenvolvimento:

```bash
npm run dev
```

Abra `http://localhost:3000` no navegador.

## Configuracao Local

Use `.env.example` como base. O arquivo `.env.local` nao deve ser versionado.

Exemplo minimo para desenvolvimento local:

```env
BACKEND_ASSESSORAI_URL=http://localhost:8000
AUTH_SECRET=seu_secret_local
NEXTAUTH_URL=http://localhost:3000
GOOGLE_PLACES_API_KEY=sua_chave_local
NEXT_PUBLIC_LOCALE=pt-BR
NEXT_PUBLIC_LOCALE_CODE=BR
```

### Backend AssessorAI

- `BACKEND_ASSESSORAI_URL`: obrigatoria.

Define a URL base da API usada pelo BFF e pelos fluxos autenticados do produto.

### Autenticacao

- `AUTH_SECRET`: obrigatoria;
- `NEXTAUTH_URL`: obrigatoria.

Essas variaveis sustentam o fluxo de autenticacao e callbacks do Auth.js.

### Google Places

- `GOOGLE_PLACES_API_KEY`: necessaria quando o autocomplete de enderecos estiver habilitado.

### Analytics e suporte

Variaveis opcionais:

- `NEXT_PUBLIC_GOOGLE_TAG_ID`;
- `NEXT_FACEBOOK_PIXEL_ID`;
- `NEXT_PUBLIC_WHATSAPP_NUMBER`;
- `NEXT_PUBLIC_WHATSAPP_MESSAGE`;
- `NEXT_PUBLIC_LINK_PRECISANDO_AJUDA`.

## Execucao

Ambiente local:

```bash
cd apps/client
npm run dev
```

Build de producao:

```bash
npm run build
npm run start
```

Fluxo basico:

1. iniciar o backend AssessorAI;
2. configurar `BACKEND_ASSESSORAI_URL`;
3. iniciar o frontend com `npm run dev`;
4. acessar login, dashboard, configuracao de mandato e fluxos de producao legislativa.

## Testes

Comandos principais:

```bash
npm run test
npm run build
```

Observacoes:

- os testes usam Jest com Testing Library;
- o build valida o App Router, as rotas BFF e a tipagem principal;
- testes funcionais completos dependem de um backend disponivel no ambiente configurado.

## Publicacao E Dados Locais

Este app foi publicado como parte de um monorepo historico sanitizado. O repositorio nao inclui:

- arquivos `.env.local` reais;
- credenciais privadas;
- dados operacionais de ambientes reais;
- builds, caches ou dependencias locais geradas.

## Licenca

Este app esta coberto pela licenca `GNU Affero General Public License v3.0` adotada no monorepo. Consulte `../../LICENSE`.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
