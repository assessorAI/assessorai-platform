# Projeto e Branches

Este repositorio esta em modo de descontinuacao (sunset) e usa uma estrategia
de branches para separar referencia publica de desenvolvimento continuo.

## Estrategia de branches

- `main`: referencia publica estavel e documentacao prioritaria.
- `dev`: novas features e ajustes em andamento.
- `staging`: validacao antes de promover para producao.
- `production`: linha historica de deploy usada pelo Railway.

Regra pratica: quando `dev` divergir muito de `main`, atualize este arquivo com
as novidades mais relevantes e mantenha o README alinhado.

## Novidades ativas em `dev`

- Coleta de demandas publica com token de contato.
- Triagem IA para demandas (`coleta_demandas_triagem`).
- Slug de mandato e endpoint de validacao de disponibilidade.
- GET publico de mandato por id/slug e proxy de imagem de perfil.

## Backlog

- Reenviar email de ativacao quando usuario for removido e readicionado ao
  mandato sem ter ativado a conta.
- Revisar validacao de mandato para garantir `exists=true` quando o registro ja
  existir.
