# Guia de Contribuição — AssessorAI Frontend

Obrigado por querer contribuir com o AssessorAI! Este documento explica como o projeto está organizado e o que esperamos de um bom Pull Request.

---

## Índice

- [Código de Conduta](#código-de-conduta)
- [Como reportar um bug](#como-reportar-um-bug)
- [Como sugerir uma melhoria](#como-sugerir-uma-melhoria)
- [Configuração do ambiente](#configuração-do-ambiente)
- [Fluxo de trabalho com Git](#fluxo-de-trabalho-com-git)
- [Padrões de código](#padrões-de-código)
- [Testes](#testes)
- [Mensagens de commit](#mensagens-de-commit)

---

## Código de Conduta

Seja respeitoso e construtivo. Críticas devem ser direcionadas ao código, nunca às pessoas.

---

## Como reportar um bug

1. Verifique se o bug já foi reportado nas [Issues](../../issues).
2. Abra uma nova issue com:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs. comportamento atual
   - Versão do Node.js e navegador utilizados
   - Prints ou vídeos, se possível

---

## Como sugerir uma melhoria

1. Abra uma issue com o prefixo `[Feature Request]` no título.
2. Descreva o **caso de uso** — qual problema a funcionalidade resolve.
3. Aguarde o feedback dos mantenedores antes de abrir um PR.

---

## Configuração do ambiente

Siga as instruções do [README.md](./README.md) para instalar e rodar o projeto localmente.

---

## Fluxo de trabalho com Git

1. **Fork** o repositório
2. Crie uma branch a partir de `main` com nome descritivo:
   ```bash
   git checkout -b feat/nome-da-funcionalidade
   # ou
   git checkout -b fix/descricao-do-bug
   ```
3. Implemente as mudanças
4. Rode os testes: `npm run test`
5. Verifique o lint: `npm run lint`
6. Faça o commit seguindo as [convenções de mensagem](#mensagens-de-commit)
7. Abra um **Pull Request** para a branch `main`

### Convenções de nome de branch

| Prefixo | Uso |
|---|---|
| `feat/` | Nova funcionalidade |
| `fix/` | Correção de bug |
| `tech/` | Refatoração, atualização de dependências |
| `docs/` | Atualização de documentação |
| `test/` | Adição ou correção de testes |

---

## Padrões de código

### Geral

- TypeScript estrito — evite `any`
- Prefira `const` em vez de `function` para componentes e funções
- Use **early returns** para reduzir aninhamento
- Nomes de funções de evento devem começar com `handle` (ex: `handleClick`, `handleBlur`)
- Implemente atributos de acessibilidade nos elementos interativos (`aria-label`, `tabIndex`, etc.)

### Estilização

- Use **Tailwind CSS** para estilização. Evite CSS inline ou arquivos `.css` avulsos
- Para estilização com tokens do design system, use **SCSS Modules** com `@use "../../../styles/tokens.scss"`
- Não misture abordagens: escolha Tailwind ou SCSS Module por componente

### Componentes

- Componentes reutilizáveis ficam em `src/components/`
- Componentes específicos de um domínio ficam em `src/features/`
- Quando um componente tiver arquivos associados (`.scss`, `.types.ts`), crie uma pasta para ele:
  ```
  src/components/upload-photo-perfil/
  ├── upload-photo-perfil.tsx
  └── upload-photo-perfil.module.scss
  ```

### Formulários

- Use **React Hook Form** com `zodResolver`
- Defina o schema Zod em um arquivo separado com sufixo `.schema.ts`
- Mensagens de validação ficam no arquivo `.i18n.ts` do módulo correspondente

### Rotas de API (BFF)

- Cada rota em `src/app/api/` deve delegar sua lógica a um **handler** em `src/api/`
- O arquivo `route.ts` deve ser enxuto, apenas chamando o handler
- Handlers que acessam o backend externo **devem** usar o `apiClient` (injeta o token JWT automaticamente)
- Endpoints públicos (sem autenticação) devem usar `fetch` diretamente

---

## Testes

- Testes ficam em `src/test/`
- Escreva testes para comportamentos críticos de formulários e fluxos de usuário
- Use `@testing-library/react` e `@testing-library/user-event`
- Rode os testes antes de abrir o PR:
  ```bash
  npm run test
  ```

---

## Mensagens de commit

Siga o padrão [Conventional Commits](https://www.conventionalcommits.org/) **em português**:

```
<tipo>(<escopo opcional>): <descrição curta>
```

### Tipos aceitos

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `tech` | Refatoração ou melhoria técnica sem mudança de comportamento |
| `docs` | Documentação |
| `test` | Adição ou correção de testes |
| `style` | Formatação, sem mudança de lógica |

### Exemplos

```
feat(mandato): adiciona campo de slug para URL pública
fix(coleta-demandas): corrige parâmetro da rota dinâmica [slug-mandato]
tech(auth): remove componentes de teste deixados no código
docs: adiciona guia de contribuição e licença MIT
```

---

## Dúvidas?

Abra uma [Discussion](../../discussions) ou uma issue com a label `question`.
