# 05 — Comparação de modelos-base

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Método, data e limites

Consulta 2026-10-30. Cards oficiais M1–M6 e repositórios em [SOURCES](../research/SOURCES.md). Fatos de card = DOCUMENTED, não medição Lia. Contagens de Qwen nos cards aparecem no bloco Language Model: não tratá-las como contagem exata de todos os encoders/auxiliares. Revision de pesos/tokenizer ainda **não congelada**; nenhum download nem benchmark. “Melhor disponível” não pode ser comprovado por marketing de fornecedor ou só uma família; ranking é ordem de experimentação condicionada aos recursos, não resultado científico.

## Comparação estrutural

| Candidato exato / fonte | Parâmetros declarados (total/ativos) | Arquitetura | Contexto nominal | Modalidades de entrada → saída | Licença declarada |
|---|---|---|---|---|---|
| Qwen3.8-27B (M1) | LM 27B, denso; ativos não separados | Gated DeltaNet + atenção, FFN, encoder visual | 262.144; extensão 1M distinta | texto/imagem/vídeo → texto | Apache-2.0 |
| Qwen3.5-27B (M2) | LM 27B, denso | DeltaNet/atenção 3:1 + FFN, visão | 262.144; extensão 1.010.000 | texto/imagem/vídeo → texto | Apache-2.0 |
| Qwen3.5-4B (M3) | LM 4B, denso | DeltaNet/atenção + visão | 262.144; extensão 1.010.000 | texto/imagem/vídeo → texto | Apache-2.0 |
| Qwen3.5-0.8B (M4) | LM 0.8B, denso | DeltaNet/atenção + visão | 262.144 | texto/imagem/vídeo → texto | Apache-2.0 |
| Qwen3.5-35B-A3B (M5) | LM 35B / 3B ativos | DeltaNet/atenção + MoE, 256 experts, 8 routed +1 shared | 262.144; extensão 1.010.000 | texto/imagem/vídeo → texto | Apache-2.0 |
| Gemma 4 E2B IT (M6) | 2.3B efetivos / 5.1B com embeddings; não MoE | atenção local/global + PLE, encoders visual/áudio | 128K | texto/imagem/áudio e frames de vídeo → texto | Apache-2.0 |
| Gemma 4 E4B IT (M6) | 4.5B efetivos / 8B com embeddings; não MoE | local/global + PLE | 128K | texto/imagem/áudio e frames → texto | Apache-2.0 |
| Gemma 4 12B Unified IT (M6) | 11.95B | decoder unificado, projeções leves sem encoders separados | 256K | texto/imagem/áudio e frames → texto | Apache-2.0 |
| Gemma 4 26B A4B IT (M6) | 25.2B / 3.8B ativos; visão ~550M indicada separadamente | MoE 128 experts, 8 ativos +1 shared; local/global | 256K | texto/imagem/frames → texto; **sem áudio** | Apache-2.0 |
| Gemma 4 31B IT (M6) | 30.7B; visão ~550M indicada separadamente | denso local/global | 256K | texto/imagem/frames → texto; **sem áudio** | Apache-2.0 |
| Qwen3-Omni-30B-A3B-Instruct (M7) | família nominal 30B/3B ativos; total completo Thinker+Talker não recontado | MoE Thinker–Talker + áudio/visão + code2wav | validar limite por componente; config tem limites distintos | texto/imagem/áudio/vídeo → texto/áudio | card: license_name Apache-2.0; campo license=other, conferir LICENSE |

Os nomes efetivos/ativos não são memória de pesos residentes: Gemma E2B não é simplesmente um arquivo de 2B, MoE A3B não cabe como denso 3B. Contexto estendido não tem mesmo custo/qualidade do nativo. Áudio de entrada não implica saída falada. Vídeo por frames não implica percepção contínua ou execução de ações.

## Capacidades, português e maturidade

| Família | Português / reasoning / tools | Ecossistema/documentação | Risco principal |
|---|---|---|---|
| Qwen3.8 | Claims multilíngues; flexible thinking, reasoning_effort/preserve_thinking; parsers tools em exemplos | Transformers, vLLM, SGLang, TokenSpeed listados | Templates/preservação de thinking e kernels híbridos; pt-BR não medido |
| Qwen3.5 | Família anuncia 201 idiomas; reasoning/coding/agents e visão | Transformers/vLLM/SGLang/KTransformers; llama.cpp mostra uso de 0.8B | Capacidade varia drasticamente com tamanho; não copiar scores 27B para 0.8B |
| Gemma 4 | Card anuncia 140+ idiomas no pretrain, 35+ de uso; thinking, function calling nativo | JAX oficial tem Gemma4_E4B, fine-tuning e LoRA; Transformers/PEFT exigem versão exata | PLE/arquitetura Unified/MoE diferem; não herdar regras Gemma anterior |
| Qwen3-Omni | 119 idiomas de texto; português listado em speech input/output; Instruct e Thinking distintos | Transformers e receitas multimodais oficiais; card ainda contém avisos de suporte de áudio em engines | Modalidades/backend têm maturidade desigual; customizar voz não é escolher preset |

Não há nota pt-BR específica Lia validada para nenhuma base. Não transportar benchmarks de card entre harnesses, budgets ou versões; a suíte Lia deve medir naturalidade, cultura/registros e tarefas reais.

## Treinabilidade e distribuição (compatibilidade não executada)

| Candidato | SFT | LoRA | QLoRA | Merge | Distribuição / frameworks a validar |
|---|---|---|---|---|---|
| Qwen3.8-27B | Viável em princípio no grafo Transformers; probe pendente | Módulos lineares e híbridos: mapear | Depende de kernels quantizados e módulos; não garantido | Só módulos suportados, base exata | Formato Transformers oficial; GGUF/AWQ/GPTQ não assumidos |
| Qwen3.5 0.8B/4B/27B | Candidatos SFT; notebook Unsloth 4B visual documentado | Candidato PEFT/Unsloth | Candidato, testar dtype/kernel/gradientes | Comparar separado vs merged | Transformers; llama.cpp documenta 0.8B GGUF; cada variante visual requer projector compatível |
| Qwen3.5-35B-A3B | Candidato com experts | Targets dos experts podem não ser Linear padrão | Não extrapolar caminho denso | Validar experts e export | MoE precisa de memória total e backend compatível |
| Gemma 4 E2B/E4B/12B/26B/31B | JAX oficial oferece FT; validar por variante | Guia LoRA geral não prova todos os encoders/PLE/experts | Probe específico por variante/framework | Validar PLE, tied weights e precisão | JAX/Transformers candidates; quantizações e conversores por variante |
| Qwen3-Omni | Separar Thinker, Talker, encoders | Começar estudo só no Thinker | Complexidade multimodal alta, pendente | Não presumir merge do sistema inteiro | Transformers oficial; não pressupor export GGUF preservando fala |

SFT/LoRA são métodos, não um selo universal de suporte. Probe futuro deve confirmar load, tokenizer/processor/chat template, forward/backward finito, parâmetros treináveis esperados, save/reload, adapter equivalência, merge e inferência em backend alvo. Não rodado aqui.

Pesos abertos disponíveis segundo cards; artefatos Transformers/configs e acesso HF/ModelScope documentados em Qwen, checkpoints em ecossistema Gemma. Inventário de arquivos safetensors/revisions por checkpoint ainda precisa ser congelado. Não afirmar que quantizações comunitárias são oficiais. Apache 2.0 permite uso comercial sob suas condições, preservando licença/notices e alterações; não concede direito de usar qualquer dado/voz/marca. Revisão legal do artefato exato continua gate.

## Memória e GPUs: estimativas inferiores, não promessas

Para N bilhões, pesos brutos em GB decimais = N × bits/8. Não inclui encoder, scales, buffers, KV/estado recorrente, ativações ou optimizer. Qwen nominal LM é usado só para estimativa. Quantização mixed-block tem mais bits efetivos que o rótulo.

| N (B) | BF16/FP16 | 8-bit | 6-bit | 5-bit | 4-bit |
|---|---|---|---|---|---|
| 0.8 | 1.6 | 0.8 | 0.6 | 0.5 | 0.4 |
| 4 | 8 | 4 | 3 | 2.5 | 2 |
| 8 | 16 | 8 | 6 | 5 | 4 |
| 11.95 | 23.9 | 11.95 | 8.96 | 7.47 | 5.98 |
| 27 | 54 | 27 | 20.25 | 16.875 | 13.5 |
| 35 | 70 | 35 | 26.25 | 21.875 | 17.5 |

Hipóteses de **envelopes de piloto**, seq 2K, microbatch 1, checkpointing, QLoRA 4-bit: 4B em GPU 16–24 GB e 27B em 48–80 GB são pontos de orçamento a investigar, não sizing validado. BF16 LoRA 27B já exige >54 GB só na base; full FT Adam pode aproximar 12–20 bytes/parâmetro antes das ativações, dependendo de master weights/optimizer/sharding. Gemma E2B/E4B dimensionar com embeddings+encoders, não somente “efetivos”. Omni precisa contabilizar Talker/codec/encoders além do Thinker. Multi-GPU traz comunicações e pode não reduzir custo/latência.

## Ranking recomendado (proposto, sem scores Lia)

**Piloto de engenharia com recursos limitados:** (1) Qwen3.5-0.8B para conformance, sem expectativa de qualidade final; (2) Qwen3.5-4B para primeiro Core candidato; (3) Gemma 4 E2B/E4B para comparação de entrada de áudio/edge, respeitando footprint real. Melhorar viabilidade é parte da seleção, não vencer por tamanho.

**Core/Deep remoto orientado a qualidade:** (1) Qwen3.8-27B; (2) Qwen3.5-27B como controle histórico; (3) Gemma 4 12B Unified/31B como alternativas multimodais; (4) Qwen3.5-35B-A3B ou Gemma 4 26B A4B se throughput justificar memória total; (5) Qwen3-Omni como trilha de pesquisa áudio end-to-end, não default do primeiro treino.

A ordem 1/2 remota é hipótese informada pelo alinhamento agentic/visão e disponibilidade, não superioridade verificada. Antes de comprar GPU, aplicar os pesos de critérios da v1.0 e gates fatais licença/compatibilidade; medir três finalistas no mesmo budget. Revisitar outros lançamentos oficiais no Gate 0: esta consulta não estabelece vencedor universal.

## Especialistas: evitar usar o LLM como tudo

| Área | Candidatos oficiais consultados | Decisão de estudo / limites |
|---|---|---|
| ASR | Whisper + faster-whisper; Qwen3-ASR 0.6B/1.7B e ForcedAligner 0.6B | Whisper CPU baseline; Qwen ASR alternativa atual. Medir WER pt-BR/ruído/latência. faster-whisper é engine, não nova base |
| TTS / voz | Qwen3-TTS 0.6B/1.7B Base, CustomVoice, VoiceDesign | Português listado; prosódia/clonagem documentadas, mas consentimento e voz própria não resolvidos. 97ms upstream não é promessa Lia |
| TTS alternativo | Piper; CosyVoice | Piper legado aponta migração OHF-Voice/piper1-gpl: rever licença de código e cada voz. CosyVoice README lista nove idiomas sem português: não presumir pt-BR |
| Embeddings / reranking | Qwen3-Embedding/Reranker 0.6B/4B/8B; BGE-M3/FlagEmbedding | Começar avaliação 0.6B vs BGE-M3; pt-BR, recall@k e memória. Não treinar um “Memory LLM” para armazenar fatos |
| Visão | VLM Qwen/Gemma acima; MediaPipe nos drivers AIRI | VLM para grounding, detector/landmarks para reflexos; não impor LLM a blinking/pose |
| Jogos | Voyager, OpenAI VPT, AIRI Minecraft | Voyager é arquitetura de agente/skills; VPT política de ações por vídeo. Não são substitutos intercambiáveis de Core nem agentes Factorio prontos |

Licenças de checkpoints especializados, vozes/vocoders e datasets ainda exigem cards exatos; README/licença de código não licenciam todos os pesos. Nenhum especialista aprovado para distribuição nesta missão.
