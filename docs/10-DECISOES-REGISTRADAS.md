# 10 — Decisões registradas

> **Atualização Missão 001 (2026-10-30):** documento v1.0 preservado. Consulte o [índice da pesquisa e correções](README.md), a [auditoria](research/00-PROJECT-AUDIT.md) e as [fontes atuais](research/SOURCES.md). Afirmações históricas não comprovam validação nesta missão.

**ADR index inicial — v1.0 — 30/10/2026**

| ID | Decisão | Estado |
|---|---|---|
| D-001 | O primeiro modelo/linhagem é Lia Core | Aprovado |
| D-002 | O objetivo de longo prazo é uma família Lia Omni, não necessariamente um único checkpoint | Aprovado como visão |
| D-003 | Primeira geração adapta um modelo-base aberto; não treina foundation model do zero | Aprovado |
| D-004 | SFT é o método inicial; LoRA/QLoRA são caminhos prioritários | Aprovado conceitualmente; hyperparams abertos |
| D-005 | Qwen3.5 era candidato prioritário original; Gemma 4 alternativa | Histórico preservado |
| D-006 | Qwen3.8-27B é adicionado à shortlist atual | Aprovado para avaliação, não para adoção |
| D-007 | Modelo-base definitivo só depois de Gate 0 | Aprovado |
| D-008 | Memória pessoal e mutável permanece fora dos pesos | Aprovado |
| D-009 | Integrações/execução/permissões permanecem no runtime da Lia | Aprovado |
| D-010 | Personality deve ser parcialmente treinada nos pesos e também governada por profile/config | Aprovado |
| D-011 | Discord e jogos precisam de datasets/adapters e conectores próprios; não são “um prompt” | Aprovado como requisito de arquitetura |
| D-012 | AIRI é referência técnica/catálogo de capacidades; Lia é produto independente | Aprovado no Lia-Project em 28/10/2026 |
| D-013 | Pesos grandes/datasets brutos não são commitados no Git | Aprovado |
| D-014 | Sem GPU paga, API paga, grande download ou upload público sem aprovação explícita | Aprovado como regra operacional |

## Decisões ainda abertas

1. Modelo-base após benchmark comparativo.
2. Framework de treino: Transformers/PEFT/TRL, Unsloth, Axolotl, LLaMA Factory ou combinação.
3. Ambiente GPU e orçamento por rodada.
4. Modelo de voz e direitos de uso/replicação da voz Lia.
5. Primeiro jogo-alvo para Lia Game.
6. Primeiro backend de inferência local (e formatos de quantização).
7. Se vision será integrado na mesma base ou roteado para modelo especialista.
8. Estratégia de memory store e contrato de memória entre app e modelo.
9. Política de publicação: adapters somente, merged checkpoint, quantizações e distribuição de base.

## Regras para mudar decisões

Uma mudança deve ser proposta em ADR com contexto, alternativas, consequências, licença, impacto no runtime, evidências e migração. Um agente pode propor; o proprietário aprova decisões de produto, custo e distribuição.
