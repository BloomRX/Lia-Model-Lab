# 05 — Comparação de modelos-base

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Método, data e limites

Consulta 2026-10-30. Cards oficiais M1–M6 e repositórios em [SOURCES](SOURCES.md). Fatos de card = DOCUMENTED, não medição Lia. Contagens de Qwen nos cards aparecem no bloco Language Model: não tratá-las como contagem exata de todos os encoders/auxiliares. Revision de pesos/tokenizer ainda **não congelada**; nenhum download nem benchmark. “Melhor disponível” não pode ser comprovado por marketing de fornecedor ou só uma família; ranking é ordem de experimentação condicionada aos recursos, não resultado científico.

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

## Reavaliação consolidada — recomendação técnica para o próximo piloto

Reconsulta oficial em 2026-10-30: [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/README.md), [Qwen3.5-27B](https://huggingface.co/Qwen/Qwen3.5-27B/raw/main/README.md), [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/README.md) e [Gemma 4](https://ai.google.dev/gemma/docs/core/model_card_4). As propriedades estruturais acima continuam documentadas; nenhuma medição pt-BR/persona/tools Lia foi acrescentada. Cards são mutáveis: freeze de revisions/weights/tokenizer/template é gate antes de adquirir pesos.

**Recomendo Qwen3.5-4B como candidato do primeiro piloto útil Core**, condicionado à revisão de licença específica, probe processor/PEFT, baseline selado e GPU/autorização. Motivos: footprint muito menor que 27B, caminho VLM para evolução, licença Apache declarada e exemplos de tuning documentados. Não escolher 0.8B como produto final apenas por caber: usar para conformance pode isolar erros do pipeline, mas capacidade esperada é inferior e não medida nos cenários Lia.

**Alternativas e motivos para não começar por elas:**

- **Qwen3.8-27B:** primeiro comparador remoto orientado a qualidade agentic/reasoning, mas ~54 GB só em pesos BF16 antes de encoder/cache/treino. Não é alvo sensato para RX 580 histórica ou sandbox; custo maior sem evidência de ganho pt-BR/persona após adaptação.
- **Qwen3.5-27B:** controle histórico útil quando houver GPU/budget, mas não há razão comprovada para tornar a escala 27B o requisito inicial.
- **Gemma 4 E2B/E4B:** alternativas de entrada multimodal/áudio, porém footprint com embeddings/encoders é maior que o nome “E” sugere. Não copiar requisitos de denso 2B/4B. Medir templates/PLE e PEFT por variante.
- **Gemma 4 12B Unified:** alternativa a investigar se áudio de entrada e consolidação multimodal justificarem custo; novo fluxo decoder-only multimodal não dispensa probe de SFT/LoRA/QLoRA/export.
- **Gemma 4 31B ou 26B A4B:** não escolher só por benchmark de fornecedor ou parâmetros ativos; memória total e backend importam. Não oferecem áudio nativo como as variantes menores.
- **Qwen3-Omni:** pesquisa futura de áudio end-to-end; complexidade Thinker/Talker/codec e export de voz não é necessária ao primeiro adapter de texto/persona/tools. Especialistas ASR/TTS desacoplados preservam viabilidade.

### Comparação de custo e viabilidade

Inferência local inicial: modelos pequenos em CPU, opcional Vulkan após teste no PC; **não** ROCm oficial RX 580 assumido. Treino remoto 4B QLoRA pode ser estudado em envelope 16–24 GB, 27B em 48–80 GB, ambos estimativas condicionadas a seq=2K/microbatch=1/checkpointing e kernels suportados. RAM/disco precisam guardar shards, cache e staging; reservar 32–64 GB RAM para planejamento remoto 4B e >=64 GB para 27B é hipótese conservadora a medir, não mínimo oficial. Local 16 GB não significa que um VLM 4B+ASR+TTS+produto simultâneos caberão.

**Estimativa de custo por cenário, não cotação/proposta de compra:** 1 milhão de tokens de treino a 100 tokens/s agregados levaria 2,78 h; multiplicador ilustrativo 1,5 para avaliação/checkpoints/inicialização = 4,17 h. A tarifa hipotética de US$2/h daria US$8,34 de GPU, sem storage/transferência. A 25 tokens/s seriam 16,67 h com o mesmo multiplicador, US$33,34. Esses throughputs/tarifas não foram medidos/cotados para nenhum candidato; não representam previsão confiável ou autorização. Obter cotação datada, dry probe e teto explícito antes do job. Custos efetivos continuam desconhecidos e **zero recurso pago foi provisionado**.

### Gate de escolha objetiva

Proposta de pontuação (0–5, pesos somam 100): pt-BR/conversa 15, raciocínio/planejamento 15, tools 15, visão/tela 10, modalidades adicionais 8, tuning reproduzível 12, runtime/quantização 10, licença 10, eficiência/custo 5. Hoje não há notas Lia defensáveis. Licença impeditiva, backend incompatível e dados sem direitos são gates fatais, não compensáveis por média. Baseline→adapter→quantizado precisam dos mesmos testes. Somente então o proprietário pode aprovar uma base como linhagem Lia Core; o ranking atual é recomendação de experimento.

## Primeiro smoke de infraestrutura — fase seguinte

Reconsulta de repositórios e restrições atuais em [16](16-REAL-INFERENCE-PILOT.md): recomendar 0.8B para testar a arquitetura antes do 4B, com Qwen3-0.6B como controle textual. Não muda a recomendação de capacidade 4B nem aprova downloads. Tamanhos exatos/revisions/licenças de artefatos ainda pendentes.

## Hardening — evidência do loader (não benchmark)

TF5.22.1 instalado **sem Torch/pesos** confirma registries/configs. Qwen3.5 completo exige o caminho AutoProcessor/Qwen3VLProcessor + AutoModelForImageTextToText/Qwen3_5ForConditionalGeneration no Lab. Controle Qwen3-0.6B exige qwen3/Qwen3ForCausalLM + AutoTokenizer/Qwen2Tokenizer. Config/arquitetura divergente falha; shortlist Gemma/MoE não significa suporte no loader. Testes slow oficiais usam o ID Qwen3.5-0.8B em dois caminhos (texto e VLM); os de Qwen3 consultados usam **0.6B-Base**, não o controle post-trained. Não foram executados aqui. Config/revision/template originais de 0.8B/4B/0.6B ainda não foram adquiridos; não há validação real de pesos/qualidade. Ver [16](16-REAL-INFERENCE-PILOT.md) para matrizes, autorização externa e próximo gate.
