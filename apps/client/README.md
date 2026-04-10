# AssessorAI — Frontend

> Plataforma web para acelerar a produtividade de assessores legislativos brasileiros.

---

## O que é o AssessorAI?

O **AssessorAI** é uma ferramenta desenvolvida para equipes de mandatos parlamentares. Ela centraliza tarefas que hoje são feitas de forma manual, fragmentada e demorada — como redigir projetos de lei, criar requerimentos, analisar emendas e coletar demandas da base eleitoral.

A plataforma combina inteligência artificial com o contexto específico do mandato (perfil parlamentar, posicionamento político, documentos da casa legislativa) para produzir textos legislativos mais precisos, no estilo do parlamentar e dentro das normas da casa.

### Funcionalidades principais

- **Produção legislativa com IA**: geração de projetos de lei, requerimentos, sugestão de emendas e análise de constitucionalidade
- **Coleta de demandas**: página pública personalizada para o eleitorado enviar demandas diretamente ao mandato
- **Gestão do mandato**: configuração do perfil parlamentar, equipe, documentos e dados públicos
- **Busca de referências**: pesquisa em fontes legislativas para embasar propostas
- **Administração**: painel para gerenciar múltiplos mandatos e usuários da plataforma

---

## Documentação completa

A documentação central do projeto agora vive no monorepo `assessorai-platform`.

- README raiz: `../../README.md`
- Checklist de publicação: `../../docs/publication-checklist.md`

---

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | [Next.js 15](https://nextjs.org/) (App Router) |
| UI | [React 19](https://react.dev/), [Tailwind CSS](https://tailwindcss.com/), [Radix UI](https://www.radix-ui.com/) |
| Formulários | [React Hook Form](https://react-hook-form.com/) + [Zod](https://zod.dev/) |
| Autenticação | [Auth.js v5 (NextAuth)](https://authjs.dev/) com JWT |
| Requisições | Axios (`apiClient`) |
| Testes | [Jest](https://jestjs.io/) + [Testing Library](https://testing-library.com/) |
| Estilos extras | SCSS Modules com design tokens |

---

## Arquitetura BFF (Backend For Frontend)

Este repositório contém **apenas o frontend**. O backend real é um microsserviço externo separado.

O servidor Next.js atua como um **BFF**: as rotas em `src/app/api/` recebem as chamadas do navegador, adicionam autenticação (token JWT da sessão) e repassam para a API externa. Isso evita expor a URL e as credenciais do backend diretamente para o cliente.

```
Navegador  →  /api/mandato  →  BFF (Next.js)  →  https://api.assessorai.org
```

---

## Pré-requisitos

- [Node.js](https://nodejs.org/) >= 20
- [npm](https://www.npmjs.com/) >= 10
- Acesso a uma instância da API AssessorAI (backend externo)

---

## Instalação e execução

```bash
# 1. Entre no diretório do app dentro do monorepo
cd apps/client

# 2. Instale as dependências
npm install

# 3. Configure as variáveis de ambiente
cp .env.example .env.local
# Edite o .env.local com os valores do seu ambiente

# 4. Inicie o servidor de desenvolvimento
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000) no navegador.

---

## Variáveis de ambiente

Copie `.env.example` para `.env.local` e preencha os valores.
O arquivo `.env.local` **nunca deve ser commitado**.

| Variável | Obrigatória | Descrição |
|---|---|---|
| `BACKEND_ASSESSORAI_URL` | ✅ | URL base da API do backend externo |
| `AUTH_SECRET` | ✅ | Secret do NextAuth — gere com `openssl rand -base64 32` |
| `NEXTAUTH_URL` | ✅ | URL pública da aplicação (ex: `http://localhost:3000`) |
| `GOOGLE_PLACES_API_KEY` | ✅ | Chave da Google Places API (autocomplete de endereços) |
| `NEXT_PUBLIC_GOOGLE_TAG_ID` | ❌ | ID do Google Tag Manager (analytics) |
| `NEXT_FACEBOOK_PIXEL_ID` | ❌ | ID do Facebook Pixel (analytics) |
| `NEXT_PUBLIC_WHATSAPP_NUMBER` | ❌ | Número de WhatsApp de suporte |
| `NEXT_PUBLIC_LOCALE` | ❌ | Locale padrão (default: `pt-BR`) |

---

## Scripts disponíveis

```bash
npm run dev      # Inicia o servidor de desenvolvimento
npm run build    # Gera o build de produção
npm run start    # Inicia o servidor de produção (requer build)
npm run lint     # Verifica o código com ESLint
npm run test     # Roda os testes com Jest
```

---

## Estrutura de pastas

```
src/
├── app/                     # Rotas Next.js (App Router)
│   ├── (public)/            # Páginas públicas (login, registro, coleta de demandas)
│   ├── (private)/           # Páginas autenticadas (dashboard, configurações)
│   ├── (adm)/               # Painel de administração
│   └── api/                 # Rotas BFF — proxy autenticado para o backend externo
│
├── features/                # Módulos por domínio de negócio (lógica + UI)
│   ├── auth/                # Autenticação (login, registro, reset de senha)
│   ├── configurar-mandato/  # Dados, equipe, documentos e foto do mandato
│   ├── coleta-demadas/      # Coleta de demandas do eleitorado
│   ├── adm/                 # Administração de mandatos e usuários
│   └── ...
│
├── api/                     # Handlers BFF e services (comunicação com o backend)
│   ├── mandato/             # Operações de mandato
│   ├── register/            # Registro e validação de campos
│   └── ...
│
├── components/              # Componentes UI reutilizáveis
├── config/                  # Configurações globais (endpoints, constantes)
├── lib/                     # Utilitários e serviços compartilhados
├── styles/                  # Tokens de design e estilos globais (SCSS)
├── i18n/                    # Internacionalização (pt-BR)
└── test/                    # Testes unitários e de integração
```

---

## Testes

```bash
npm run test
```

Os testes usam **Jest** com **Testing Library**. Os arquivos ficam em `src/test/`.

---

## Contribuição

Leia o [CONTRIBUTING.md](./CONTRIBUTING.md) para entender o fluxo de trabalho, padrões de código e como abrir um Pull Request.

## Status de publicação

Este app foi saneado no monorepo para publicacao tecnica:

- nenhum `.env` real deve ser versionado
- a configuracao publica parte de `.env.example`
- o backend continua sendo uma dependencia externa

---

## Licença

[MIT](./LICENSE)
