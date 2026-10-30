# 05 — Plano de treinamento e criação de pesos

## 1. Estratégia da primeira geração

Começar com um modelo-base aberto existente e criar pesos personalizados usando **SFT + LoRA/QLoRA**. Não treinar uma arquitetura foundation do zero na primeira etapa.

A meta é melhorar comportamento e capacidade específica da Lia mantendo os conhecimentos e habilidades gerais da base. O adapter é o primeiro artefato treinado e deve ser mantido versionado fora do Git.

## 2. LoRA versus QLoRA

### LoRA

Congela os pesos-base e aprende matrizes de baixo rank em módulos selecionados. O checkpoint base permanece sem alteração; o adapter é relativamente menor. Pode ser treinado em precisão adequada ao hardware disponível.

### QLoRA

Carrega uma cópia quantizada de 4-bit do modelo-base, mantém o backbone congelado e treina adapters LoRA através dele. O trabalho original QLoRA documenta o uso de NF4, double quantization e paged optimizers para reduzir memória.

### Escolha inicial

Executar dois pilotos comparáveis, se hardware permitir:

- LoRA no formato suportado de maior fidelidade pelo ambiente;
- QLoRA 4-bit no formato quantizado suportado.

A comparação deve medir qualidade, estabilidade, memória, throughput, latência, perda multimodal e facilidade de export. Não escolher QLoRA só porque cabe em uma placa menor; qualidade da variante exportada também importa.

## 3. Quantização: não confundir treino e distribuição

- **Checkpoint de referência:** manter o modelo-base original e seu hash. Não sobrescrever.
- **Base para QLoRA:** representação 4-bit de treinamento, com config e método registrados.
- **Adapter treinado:** manter separadamente e validar junto ao exato checkpoint-base.
- **Merge:** operação opcional que combina adapter e base; só fazer após comparar adapter separado e merged.
- **Quantização de distribuição:** etapa posterior ao merge ou export definido; gerar quantizações separadas, preservar o master sem quantização e avaliar cada uma.

Para 27B parâmetros, apenas armazenar cada parâmetro em BF16 implica aproximadamente 54 GB decimais de pesos brutos (cerca de 50 GiB), sem overhead. Em 4-bit, o limite teórico simples seria aproximadamente 13,5 GB decimais, antes de metadados, scales e buffers. Isso **não** é estimativa de VRAM de treino: activations, optimizer states, contexto, batch, vision encoder, quantization metadata e framework acrescentam memória.

Não prometer que uma quantização Q4/Q5/Q8 preserva qualidade sem benchmark. `GGUF`, `AWQ`, `GPTQ`, `FP8` e outras formas não são intercambiáveis; o formato será escolhido por runtime de inferência, hardware, licença e suporte da arquitetura.

## 4. Pipeline proposto

### Etapa A — baseline do modelo-base

- Congelar revision/hash e tokenizer/template.
- Rodar a suíte de avaliação Lia antes do treino.
- Salvar métricas e casos de falha.
- Estimar hardware/time sem pagar recursos ainda.

### Etapa B — dataset de identidade e instrução

Construir exemplos de alta qualidade para:

- identidade e voz textual da Lia;
- português brasileiro natural;
- conversa cotidiana e suporte técnico;
- empatia sem bajulação excessiva;
- humor, curiosidade e personalidade em situações variadas;
- consistência de personagem entre sessões;
- respeito a instruções, incerteza, limites e segurança.

### Etapa C — SFT de Lia Core

Treinar primeiro SFT com dataset curado. Usar train/validation/test separados. Evitar duplicatas e leakage de prompts de avaliação. Começar com experimento pequeno e config de referência; depois aumentar dados/steps baseado em evidência.

### Etapa D — Tool-use / agentic SFT

Adicionar trajetórias estruturadas:

1. pedido do usuário;
2. decisão de usar ferramenta;
3. chamada tipada com argumentos;
4. resultado de ferramenta real/simulado;
5. interpretação do resultado;
6. continuação, retry seguro ou conclusão.

Cobrir ferramenta bem-sucedida, retorno vazio, erro, timeout, autorização negada, schema inválido, informação contraditória e tentativa de prompt injection. O modelo deve aprender a não inventar que executou.

### Etapa E — memória como comportamento

Ensinar operações de memória (extrair, consultar, atualizar, generalizar, esquecer, não salvar dado sensível), usando store simulado e fixtures. Não inserir a base pessoal real do usuário no treinamento.

### Etapa F — avaliação e preference alignment

Se houver pares de preferência confiáveis, testar DPO/ORPO ou método equivalente como experimento posterior. Não introduzir RLHF/DPO antes de SFT e métricas estarem estáveis.

### Etapa G — especialização multimodal

Só depois de Gate 0. Se a base for VLM, criar exemplos com imagens/screenshots e perguntas/ações ancoradas. Vídeo exige temporal alignment; não simular compreensão temporal apenas embaralhando frames independentes.

### Etapa H — especialização de jogos

Escolher primeiro um ambiente, obter state/action interface, construir trajetórias e benchmark reprodutível. Iniciar com behavior cloning/SFT de trajetórias; RL/GRPO só em sandbox controlado e depois de baseline.

### Etapa I — export e release

Testar adapter, merge e quantizações. Registrar exatamente base, adapter, config de export, tokenizer, template, runtime, hardware, métricas e checksums. Publicar somente após license gate.

## 5. Pilotos por incremento

| Experimento | Pergunta | Método | Critério de avanço |
|---|---|---|---|
| E0 | A base é compatível e licenciável? | Gate 0 documental/probe autorizada | GO formal |
| E1 | SFT pequeno melhora persona/pt-BR? | LoRA/QLoRA + SFT | ganho cego sem regressão inaceitável |
| E2 | Tool-use é robusto no runtime Lia? | SFT de chamadas + replay | schema pass e end-to-end pass |
| E3 | Memory ops evitam contaminação? | SFT de operações em store fake | extração/retrieval/forget correctness |
| E4 | Visão melhora contexto visual? | VLM SFT/LoRA se suportado | VQA + screenshot grounding |
| E5 | Um jogo é jogável? | Trajectory SFT / behavior cloning | sucesso em cenário holdout |
| E6 | Quantizações são aceitáveis? | Export/quantize + regressão | quality/latency gate por variante |

## 6. Hyperparameters: como registrar

Não fixar agora rank, alpha, learning rate, batch size ou epochs. São dependentes do modelo, target modules, dados, GPU e framework. Registrar no experiment card:

- rank/alpha/dropout;
- módulos alvo;
- learning rate/scheduler/warmup;
- batch e gradient accumulation;
- sequence length e packing;
- epochs/steps e stopping rule;
- optimizer/precision/quant config;
- gradient checkpointing;
- seed;
- avaliação antes/durante/depois.

## 7. Framework candidates

- Hugging Face Transformers + PEFT + TRL/SFTTrainer: caminho de referência para treinamento explícito e documentação reproduzível.
- Unsloth: candidato para experimentação, otimização de memória/velocidade e modelos Qwen/Gemma recentes. A página atual do projeto declara suporte a NVIDIA, AMD, Intel e backend Vulkan; isso precisa ser verificado para a GPU, driver, sistema operacional, arquitetura e variante específica antes de ser tratado como compatibilidade garantida.
- Outras ferramentas (Axolotl, LLaMA Factory, XTuner, Keras/JAX) devem ser avaliadas se melhorarem suporte real ao modelo candidato.

Não se comprometer com uma ferramenta antes do Gate 0 do modelo exato. O suporte anunciado para uma família não prova suporte a todos os tamanhos, encoders multimodais ou target modules.

## 8. Modelo treinado não é modelo publicado

O fim do treino gera um checkpoint experimental. Só após avaliação, licença, segurança, conformance e documentação ele vira release da família Lia.
