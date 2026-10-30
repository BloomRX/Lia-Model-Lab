# ADR-0001 — Consolidação oficial e fundação offline

Data: 2026-10-30. Estado: **aceito para organização e implementação local**, no escopo autorizado pelo proprietário. Não aprova modelo-base, dados de produção, GPU paga ou release.

## Contexto e integração

HEADs remotos confirmados antes da integração:

| Linha | HEAD | Conteúdo no levantamento |
|---|---|---|
| main | `20f1883ad1671139d7c023eff42b72c6bca96525` | Fundação v1, marca, governança 13 e instruções gerais de delegação; sem pesquisa/skills |
| pesquisa | `c18c4eed74f62a1c8e28ad03fad3107ed7d8da91` | Dois commits de pesquisa, inventário, matriz, arquitetura, planos, fontes e manifest |
| skills | `9b99756a7aaea25ed3c891a101de3bb766470494` | Nove skills, sete perfis, orquestração 14; compartilha ancestral de marca/governança com main |

README e AGENTS foram editados em paralelo nas três linhas. `.gitignore` divergiu entre pesquisa/main; manifest e shortlist só na pesquisa; docs 13/marca já em main; 14/skills/perfis só na linha skills. `20f1883` e `3317b92` têm título parecido, mas não são o mesmo commit. Integração por merges locais com revisão de conteúdo, sem merge remoto de PR nem troca de branch. Estado restaurado do workspace era idêntico à pesquisa remota; foi protegido antes do fast-forward.

## Decisão

- Uma única coleção numerada oficial em `docs/`, absorvendo a pesquisa mais detalhada. Remover os antigos documentos 00–11 duplicados; conteúdo útil de escopo, decisões, governança e gates foi integrado à coleção/ADRs. Git mantém a proveniência, sem pasta de documentação legada.
- Remover o documento conceitual obsoleto e suas referências. Não substituir por outro arquivo legado.
- Preservar `docs/BRAND-STANDARDS.md` sem alterações e manter governança 13; 14 passa a definir ownership/fallback operacional.
- Core como primeira adaptação, memória pessoal externa, runtime/integrações/permissões separados e AIRI apenas referência. Estes princípios do registro v1 permanecem válidos. Modelo único, MoE enorme e AIRI obrigatório não são requisitos.
- Usar **Lia Hearing** para percepção de áudio; **Lia Speech** para saída. Agent/Memory são papéis e contratos, não obrigação de checkpoints adicionais.
- Implementar primeiro ferramentas offline em Python 3.11+, schema v1 texto/tools, splits por grupo, integridade, planejamento de SFT e avaliação de predições. Não criar treinadores/downloaders implícitos.
- Manter nove skills porque separam artefatos e gates distintos; sete revisores read-only por instrução. Isso não cria sandbox próprio nem comprova execução no Codex/Arena.

## Estados de decisão e evidência

**Aprovado:** limites de autorização, independência, separação modelo/runtime e consolidação solicitada. **Proposta:** shortlist de piloto e metas de benchmark. **Hipótese:** ganho de persona/tool-use após SFT. **Experimento planejado:** configuração sem treino executado. **Experimento executado:** exige registro, logs e artefatos reais. **Resultado comprovado:** somente métrica/teste identificado no ambiente declarado. Testes sintéticos de software não comprovam qualidade de um modelo.

## Consequências e alternativas

Não manter duas árvores com instruções concorrentes. Custos da migração: atualizar links, skills, índice e manifest; testar os validadores. Base definitiva permanece aberta; Qwen3.5-4B é recomendação de candidato econômico, não “Lia Core já treinado”. Export local preserva apenas adapter e proveniência; não incorpora base nem publica pesos.

## Revisit conditions

Mudar base, schema, método, política de dados, targets de backend ou release requer novo ADR. Revisions/licenças/probes de treinamento devem ser fechados antes de downloads/treino autorizados. Não confundir a aceitação técnica deste ADR com aprovação de gastos ou de publicação.
