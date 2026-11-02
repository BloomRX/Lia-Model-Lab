# 00 — Auditoria atual e integração

Data: 2026-10-30. Escopo: conteúdo remoto, documentação, skills/perfis e fundação técnica local. Pesquisa AIRI anterior incorporada com suas limitações; nenhuma validação de produto/modelo é inferida.

## Estado remoto confirmado antes da operação

| Linha | HEAD confirmado | O que já estava presente |
|---|---|---|
| main | `20f1883ad1671139d7c023eff42b72c6bca96525` | Fundação v1, BRAND-STANDARDS, governança 13, instruções gerais de delegação |
| pesquisa | `c18c4eed74f62a1c8e28ad03fad3107ed7d8da91` | Pesquisa 57b9d1f+c18c4ee, 14 entregáveis, ledger, índice, manifest; não estava em main |
| skills | `9b99756a7aaea25ed3c891a101de3bb766470494` | Nove skills, sete perfis Codex, doc 14; não estavam em main |

Main e skills compartilham o ancestral `311eb4a`; pesquisa deriva de `182f1a1`. Main e skills têm commits diferentes de finalização de índices (`20f1883`/`3317b92`); títulos parecidos não provam equivalência. O checkout restaurado inicialmente tinha HEAD antigo e alterações de pesquisa, conferidas byte a byte com a branch remota antes de proteger o estado e avançar.

## Modificações paralelas e resolução

- **README e AGENTS:** alterados nas três linhas. Resolução semântica: uma entrada oficial, políticas preservadas, instruções de marca, skills e implementação integradas. Removidos textos de ZIP e handoffs contraditórios.
- **.gitignore:** pesquisa ignorava clone temporário; main adicionava caches ML, configuração local e artefatos. Mantidas as proteções úteis de main e metadata Python local.
- **Manifest e shortlist:** pesquisa modificou; main/skills não tinham atualização equivalente. Manifest é regenerado por código com cobertura completa, não reaproveitado sem checar hashes.
- **Documentos:** pesquisa duplicava a v1 em subárvores. Promovida coleção numerada mais completa à raiz `docs/`, removidos antigos 00–11 duplicados, sem criar arquivo legado substituto. [ADR-0001](adr/0001-CONSOLIDATION.md) registra princípios mantidos e decisões de organização.
- **Marca e governança:** BRAND-STANDARDS de main preservado integralmente; doc 13 mantido; doc 14 integrado e melhorado. Nove skills revistas com entradas, passos, saída, critérios, limites e ownership. Sete perfis continuam revisão read-only por instrução.

## Inconsistências resolvidas

| Tema | Conclusão atual |
|---|---|
| AIRI como arquitetura permanente | AIRI é referência técnica, aplicação Lia independente; nada exige importar runtime AIRI |
| Um único grande modelo para tudo | Core primeiro; papéis/especialistas separados quando necessário. MoE e Omni são hipóteses de longo prazo |
| Gemma 4 licença/modalidades | Card consultado declara Apache 2.0; áudio só E2B/E4B/12B; 31B e 26B A4B sem áudio |
| 27B como primeiro treino obrigatório | Recomendado piloto econômico 4B, 0.8B para conformance; 27B somente comparação remota autorizada |
| Voice/Hearing/Speech | Hearing para percepção/ASR; Speech para síntese; sem obrigação de pesos separados por nome |
| Memória pgvector no AIRI | Placeholder não prova retrieval implementado; memória pessoal é externa |
| Factorio via UI | Conexão/configuração não prova agente server-side jogável |
| Hardware local | Ryzen 5 5500/~16 GB/RX 580 2048SP ~4 GB é referência histórica do pedido; docs anteriores citam 8 GB. PC atual não medido |
| Schema proposto sem código | Schema v1 texto/tools, validador, dedup e splits agora implementados; multimodal continua planejado |
| Validação YAML pendente | Parser real instalado e executado nesta entrega, junto de JSON/TOML; ver relatório atual |

## Proveniência técnica preservada

Inventário AIRI permanece auditado estaticamente em v0.13.0 SHA `3c4aca209330f1a78fe7288e8c4ca75639cd10e6`, referência beta.5 `6ea680f51486d257f9b0eeda3bdc25db4307d3bb` e snapshot separado Lia Project `db99c709059a6d074b18361bfb32c9f144620632`. Todos os 39 registros de código foram preservados no [ledger](evidence/airi-evidence.json); os 48 requisitos continuam na [matriz](02-LIA-CAPABILITY-MATRIX.md). Não foi reexecutado AIRI ou Lia nesta consolidação. [Fontes](SOURCES.md).

## Resultado da consolidação

[Fundação técnica](15-IMPLEMENTATION-FOUNDATION.md) implementada, com [testes realmente executados](VALIDATION.md). Não há base adotada, dataset de produção, checkpoint Lia treinado ou resultado ML real. Treino/PEFT/inferência e plataformas de GPU continuam gates abertos, sem bloquear progresso de software offline.
