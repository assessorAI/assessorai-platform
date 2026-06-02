# Contribuindo com o AssessorAI Client

Obrigado pelo interesse em contribuir.

Este componente faz parte de um monorepo publico historico da plataforma AssessorAI, criada pela [Legisla Brasil](https://legislabrasil.org/). Contribuicoes sao avaliadas em regime de melhor esforco, sem SLA.

## Codigo De Conduta

Seja respeitoso e construtivo. Criticas devem ser direcionadas ao codigo, documentacao ou comportamento do sistema, nunca as pessoas.

## Escopo De Contribuicao

Contribuicoes mais adequadas para este repositorio:

- melhorias de documentacao;
- correcao de instrucoes de instalacao, build e testes;
- ajustes de seguranca;
- remocao de referencias internas residuais;
- manutencao comunitaria que preserve compatibilidade sempre que possivel.

Mudancas funcionais amplas devem explicar claramente motivacao, impacto e forma de validacao.

## Como Reportar Um Bug

Abra uma issue com:

- descricao clara do problema;
- passos para reproduzir;
- comportamento esperado e comportamento atual;
- versao do Node.js e navegador utilizados;
- prints ou videos, se ajudarem a entender o problema.

## Configuracao Do Ambiente

Siga as instrucoes do `README.md` deste app para instalar e rodar o projeto localmente.

## Fluxo De Trabalho

1. Crie uma branch com nome descritivo.
2. Implemente mudancas pequenas e focadas.
3. Rode `npm run test` quando alterar comportamento testado.
4. Rode `npm run lint` e `npm run build` quando estiverem disponiveis no ambiente local.
5. Atualize documentacao relevante.
6. Abra a pull request explicando o motivo da mudanca e a validacao realizada.

### Convencoes De Nome De Branch

| Prefixo | Uso |
|---|---|
| `feat/` | Nova funcionalidade |
| `fix/` | Correcao de bug |
| `tech/` | Refatoracao, manutencao ou dependencias |
| `docs/` | Atualizacao de documentacao |
| `test/` | Adicao ou correcao de testes |

## Padroes De Codigo

- TypeScript estrito sempre que possivel.
- Evite `any` sem justificativa.
- Prefira componentes e funcoes pequenas, com responsabilidade clara.
- Use atributos de acessibilidade nos elementos interativos.
- Preserve a organizacao existente entre `src/components/`, `src/features/` e `src/app/api/`.
- Nao inclua segredos, dados pessoais reais, arquivos `.env.local` ou credenciais.

## Testes

Testes ficam em `src/test/` e usam Jest com Testing Library.

Comando principal:

```bash
npm run test
```

## Mensagens De Commit

Prefira Conventional Commits em portugues:

```text
<tipo>(<escopo opcional>): <descricao curta>
```

Tipos usuais:

- `feat`: nova funcionalidade;
- `fix`: correcao de bug;
- `tech`: refatoracao ou melhoria tecnica sem mudanca de comportamento;
- `docs`: documentacao;
- `test`: adicao ou correcao de testes;
- `style`: formatacao, sem mudanca de logica.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
