# 04 — Seleção do modelo-base

> **Atualização Missão 001 (2026-10-30):** documento v1.0 preservado. Consulte o [índice da pesquisa e correções](README.md), a [auditoria](research/00-PROJECT-AUDIT.md) e as [fontes atuais](research/SOURCES.md). Afirmações históricas não comprovam validação nesta missão.

**Status:** shortlist para avaliação, nenhum modelo aprovado como base definitiva.

## 1. Histórico e evolução da shortlist

A decisão original registrada nas conversas era avaliar **Qwen3.5** como primeira opção e **Gemma 4** como alternativa. A pesquisa de 30/10/2026 encontrou também **Qwen3.8-27B**, candidato posterior relevante, e por isso a avaliação deve incluir os três sem apagar o histórico.

## 2. Candidatos

### A. Qwen3.8-27B — candidato prioritário para primeira avaliação

Informações do model card oficial consultado em 30/10/2026:

- 27B parâmetros, modelo denso, pesos BF16 no repositório principal.
- Tipo `Causal Language Model with Vision Encoder`.
- Entrada visual nativa; o card descreve compreensão de imagens e vídeos.
- Contexto nativo informado de 262.144 tokens, extensível por configuração/serviço.
- O card destaca coding, professional work, research e tarefas agentic de longo horizonte.
- Licença declarada no Hugging Face: Apache-2.0.
- Artefatos no formato Transformers; o card lista compatibilidade com Transformers, vLLM, SGLang e TokenSpeed.

**Por que avaliar:** parece alinhar texto, raciocínio/agentic, visão e vídeo em um checkpoint denso de 27B, reduzindo a necessidade de uma segunda base logo no início.

**O que ainda precisa provar:** qualidade pt-BR nos cenários Lia; tool calling no protocolo exato do runtime Lia; estabilidade do chat template; suporte efetivo a LoRA/QLoRA no framework escolhido; compatibilidade de inferência/quantização em GPU AMD/Vulkan/ROCm; performance sob contexto real; qualidade multimodal e limites de vídeo; export para os targets de distribuição.

**Não assumir:** o model card afirmar agentic use não garante que o modelo conclua tarefas de Lia sem tool schemas, permissões, ambiente e treino/avaliação próprios.

### B. Qwen3.5-27B — baseline de comparação e candidato legado

- Model card oficial declara formato Transformers e licença Apache-2.0.
- É a família prioritária que já estava no plano anterior.
- Deve servir como baseline comparativo para entender se o ganho do Qwen3.8 compensa mudança de família/framework.

**Gate:** verificar modalidades e limitações no model card exato, tokenizer/template, LoRA targets, compatibilidade do runtime e quantização. Não assumir suporte de áudio pelo fato de ser multimodal.

### C. Gemma 4 — alternativa importante

A documentação oficial atual descreve Gemma 4 com entrada de texto, áudio e imagem, suporte a mais de 140 idiomas e contexto de 128K/até 256K, além de tamanhos como E2B, E4B, 31B e 26B A4B. A documentação de tuning lista fluxos de LoRA via Keras, JAX, Transformers/PEFT, LLaMA Factory e XTuner.

**Por que avaliar:** candidato interessante quando áudio e imagem nativos e diversidade de tamanhos são mais importantes do que escolher uma base densa de 27B.

**Correção Missão 001 (2026-10-30):** o [card oficial atual](https://ai.google.dev/gemma/docs/core/model_card_4) declara **Apache 2.0** para Gemma 4. A hipótese anterior de termos próprios foi corrigida; revisar LICENSE/NOTICE do checkpoint exato e direitos dos dados/vozes antes de distribuir derivados.

**Gate:** conferir o card específico da variante (31B, 26B A4B, E4B etc.), funcionamento de tool calling, templates, finetuning multimodal, quantização e deployment alvo.

## 3. Comparação preliminar

| Critério | Qwen3.8-27B | Qwen3.5-27B | Gemma 4 |
|---|---|---|---|
| Linha anterior do plano | Não; candidato novo | Sim; prioridade original | Sim; alternativa original |
| Tamanho de referência | 27B denso | 27B | várias variantes, incluindo 31B e 26B A4B |
| Imagem | Declarada nativa | Confirmar na variante/card | Declarada na família |
| Vídeo | Declarado no card 3.8 | confirmar por variante | não assumir para toda variante sem card |
| Áudio de entrada | Não declarado como capacidade principal do card 3.8 | confirmar por variante | declarado na família |
| Tool/agentic | card destaca long-horizon agentic | medir | medir e testar function calling |
| Licença | Apache-2.0 no card | Apache-2.0 no card | Apache-2.0 (correção Missão 001) |
| Fit inicial | candidato forte para Core + Vision | baseline histórico | candidato multimodal alternativo |
| Risco principal | compatibilidade de tuning/deploy e pt-BR | ganho relativo à geração nova | footprint real e diferenças entre variantes |

Esta tabela é uma triagem documental, não ranking de qualidade. Métricas públicas de fabricantes não substituem avaliação própria.

## 4. Gate 0 — antes de baixar pesos

O agente deve produzir um relatório comparativo sem download de checkpoints, contendo:

1. Model card, licença e política de distribuição/derivados.
2. Architecture config, tokenizer, chat template e special tokens.
3. Modality matrix real: text, image, video, audio input, audio output, tool calling, structured output.
4. Compatibilidade com Transformers/PEFT/TRL e versão mínima.
5. LoRA/QLoRA suportado por módulos concretos; lista de target modules.
6. Requisitos de memória estimados para inference, LoRA, QLoRA e full fine-tune — separadamente; declarar método e incerteza.
7. Engines de inferência e formatos de quantização compatíveis.
8. Suporte verificado a AMD e fallback CPU/Vulkan; distinguir treino de inferência.
9. Benchmarks existentes e avaliação interna necessária em pt-BR.
10. Limites para redistribuir adapter, merged checkpoint e quantized variant.

**Saída do Gate 0:** `GO`, `NO-GO` ou `NEEDS-PROBE` por modelo, com provas e comandos de reprodução. Só depois de GO pode-se autorizar download/training pilot.

## 5. Matriz de pontuação sugerida

Pontuação 0–5, peso total 100. Cada nota precisa de evidência.

| Critério | Peso |
|---|---:|
| Qualidade de conversa e pt-BR | 15 |
| Raciocínio/planejamento e tarefas longas | 15 |
| Tool calling e schemas robustos | 15 |
| Visão/tela (para a meta AIRI) | 10 |
| Multimodalidade adicional (vídeo/áudio) | 8 |
| Fine-tuning LoRA/QLoRA reproduzível | 12 |
| Runtime e quantização em hardware-alvo | 10 |
| Licença e distribuição | 10 |
| Eficiência/latência/custo total | 5 |

Um modelo não pode compensar licença impeditiva ou incompatibilidade fatal de deployment com nota alta em benchmark.

## 6. Baseline obrigatório

Antes de fine-tuning, medir o modelo-base sem adapter nos mesmos prompts/splits, com a mesma temperatura, template e ferramenta. Sem baseline não é possível provar que o fine-tuning melhorou o modelo.
