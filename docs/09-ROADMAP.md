# 09 — Roadmap de execução

Roadmap proposto. Datas e custos não são estimados aqui porque dependem do Gate 0, do ambiente GPU e da decisão do proprietário.

## Fase 0 — Fundação documental e governança

**Objetivo:** o repo ter uma missão inequívoca e regras para agentes.

Entregáveis:
- documentação fundadora e AGENTS.md;
- catálogo AIRI e matriz modelo/runtime;
- shortlist e critérios;
- templates de dataset/experiment/model card;
- política de dados, licença e custos.

Gate: revisão do proprietário e aceitação das decisões iniciais.

## Fase 1 — Pesquisa comparativa e modelo-base

**Objetivo:** decidir uma base com provas, não com hype.

Entregáveis:
- Qwen3.8-27B, Qwen3.5-27B e Gemma 4 comparados;
- licença e modal matrix confirmadas;
- framework e target modules validados;
- estimativa de hardware/custo para LoRA e QLoRA;
- um relatório GO/NO-GO/NEEDS-PROBE.

Gate: aprovação explícita da base e infraestrutura antes de downloads/treino.

## Fase 2 — Dataset Factory e baseline

**Objetivo:** criar dataset pequeno, original, licenciado e testável.

Entregáveis:
- dataset cards;
- schema canônico;
- curadoria Persona/PT-BR;
- suite de avaliação inicial;
- baseline do modelo-base.

Gate: split selado, qualidade humana mínima e proveniência aprovada.

## Fase 3 — Lia Core SFT

**Objetivo:** primeiro adapter Lia.

Entregáveis:
- treino LoRA e/ou QLoRA;
- experiment cards;
- adapter versionado em armazenamento aprovado;
- comparação base vs adapter;
- model card experimental.

Gate: ganho em persona/PT-BR e ausência de regressão crítica.

## Fase 4 — Tool-use e agentic behavior

**Objetivo:** o modelo usar ferramentas de forma confiável.

Entregáveis:
- dataset de tool trajectories;
- SFT especializado;
- schema/function-calling tests;
- loop de retorno/erro/retry;
- integração de conformance com runtime Lia.

Gate: sucesso end-to-end nos cenários internos e testes de segurança.

## Fase 5 — Memória, skills e social

**Objetivo:** comportamento do modelo em memória e comunicação multicontexto.

Entregáveis:
- memory operation adapter/dataset;
- testes de recall/update/forget;
- diálogos sociais multiusuário simulados;
- conformance do connector Discord em ambiente de teste.

Gate: isolamento entre usuários, privacidade e memória com origem/controle de deleção.

## Fase 6 — Visão, tela e vídeo

**Objetivo:** transformar o Lia Core em um agente perceptivo confiável.

Entregáveis:
- avaliação VLM base;
- dataset de imagem/screenshots licenciado;
- testes de OCR/layout, grounding e desktop context;
- teste de vídeo temporal se base suportar.

Gate: resposta visual grounded e runtime de captura com consentimento.

## Fase 7 — Voz e embodiment

**Objetivo:** voz natural e expressão coerente.

Entregáveis:
- avaliação de ASR/TTS candidate engines;
- voz da Lia com licenças e consentimento;
- prosódia/emoção estruturada;
- integração com animações, visemes e avatar.

Gate: qualidade, latência, identidade, licença e privacidade.

## Fase 8 — Lia Game

**Objetivo:** provar jogo real em um ambiente específico.

Entregáveis:
- escolha de primeiro jogo;
- adapter do jogo e world-state interface;
- ambiente de teste e trajectories;
- behavior-cloning/SFT e depois RL somente se justificar;
- métricas de sucesso e safety.

Gate: completar cenários holdout repetidamente sem ações inválidas perigosas.

## Fase 9 — Quantização, distribuição e variantes

**Objetivo:** entregar pesos utilizáveis em hardware variado.

Entregáveis:
- master adapter/merge;
- variantes de quantização priorizadas;
- benchmark por backend/hardware;
- model card e checksums;
- procedimento de update/rollback.

Gate: quality/performance/license gate completo.

## Longo prazo — Lia Omni

Depois que as fases anteriores gerarem dados, métricas e capacidades comprovadas, avaliar:

- adapters interoperáveis ou especialistas independentes;
- modelos menores `Reflex/Fast` para baixa latência;
- `Deep` para raciocínio pesado;
- arquitetura MoE ou roteamento de especialistas;
- percepção/áudio/vídeo mais nativos;
- continual pretraining ou RL em ambientes apropriados.

MoE e treinamento do zero são escolhas futuras condicionadas a dados, orçamento e vantagem mensurável — não marcos obrigatórios.
