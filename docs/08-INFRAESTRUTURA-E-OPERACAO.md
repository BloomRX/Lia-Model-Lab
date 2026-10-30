# 08 — Infraestrutura, hardware e operação

## 1. Situação de hardware conhecida

Um relatório de benchmark do `Lia-Project` de 29/09/2026 registrou aproximadamente:

- CPU AMD Ryzen 5 5500 (6 cores / 12 threads);
- RAM total de 15,9 GiB;
- GPU AMD Radeon RX 580 2048SP;
- VRAM reportada: aproximadamente 4 GiB.

Isto é um snapshot de uma execução anterior, não uma telemetria atual garantida. Antes de decidir treinamento local, reexecutar diagnóstico de hardware e driver. A placa é apropriada para desenvolvimento do repo e testes pequenos, mas não deve ser tratada como alvo realista para treino local de um modelo 27B. Mesmo inferência de 27B pode ser muito limitada com 4 GiB de VRAM.

## 2. Estratégia de infraestrutura

### Desenvolvimento local

Usar o PC para editar código, criar datasets pequenos, validar schema, executar unit tests e avaliar modelos muito pequenos. Não bloquear arquitetura na marca de GPU.

### Treinamento remoto

Planejar treino 27B em GPU remota/cloud ou infraestrutura própria adequada, selecionada após estimativa técnica. Antes da execução: custo/hora, VRAM, duração, armazenamento, transferência, região, retenção, privacidade e desligamento automático devem estar documentados e aprovados.

### Inferência local

Investigar runtimes diferentes por hardware: CUDA, ROCm, Vulkan e CPU. Não afirmar que um backend AMD suporta o modelo só porque o framework diz suportar AMD em geral. Conferir arquitetura da GPU, versão do driver, kernels, formato de quantização, VLM vision encoder e contexto.

## 3. Estimativa de memória

Separar as estimativas:

- armazenamento do checkpoint;
- VRAM de inferência;
- VRAM de QLoRA;
- VRAM de LoRA em BF16/FP16;
- VRAM de full fine-tuning;
- KV cache por contexto/concurrency;
- RAM do host e disco temporário.

Para um modelo de 27B, 27 bilhões × 2 bytes (BF16) ≈ 54 GB decimais apenas para pesos brutos. A regra teórica de 4 bits dá cerca de 13,5 GB antes de overhead. Treinamento inclui activations e outros buffers; não usar esses números como promessa de VRAM total.

## 4. Arena.ai Agent Mode

A documentação da Arena atualizada em 08/10/2026 descreve Agent Mode como ambiente de workflow com pesquisa, upload, coding assistance, bash/sandbox, escrita de arquivos e execução/iteração; ao conectar GitHub, cria cópia sandbox do repo, mostra diffs, executa checks e pode criar commit/PR.

Limites operacionais que afetam o fluxo:

- uma sessão de chat suporta atualmente um único PR;
- quando PR é mesclado ou fechado, a sessão não consegue continuar enviando código para o GitHub; guardar todo o trabalho antes do merge;
- o modelo orquestrador do Agent Mode não é revelado na documentação consultada;
- não presumir GPU, memória, persistência de artefatos grandes, acesso a dados privados ou orçamento de treino no sandbox;
- o Agent Mode deve desenvolver o laboratório, e não ser confundido com a infraestrutura que executará treino de modelos.

## 5. Workflow recomendado com Arena

1. Sessão de research: audit model cards, licenses, training compatibility. Só pesquisa.
2. Sessão de design: propor arquitetura/datasets e gerar ADR.
3. Sessão de implementation: scripts e validators com dados pequenos/fakes.
4. Sessão de training pilot: somente depois de aprovar GPU, orçamento e download.
5. Sessão de evaluation: rodar benchmark nas variantes e abrir PR de resultados.

Cada sessão deve ter objetivo e PR bem delimitados. Não misturar refactor geral, downloads grandes e treino caro em uma única sessão.

## 6. Armazenamento dos artefatos

Usar Git para:

- código e config;
- documentação;
- manifest e hashes;
- logs pequenos, redacted;
- métricas agregadas;
- model/dataset cards.

Usar armazenamento próprio/versionado aprovado (por exemplo, Hugging Face Hub privado, object storage ou artifact registry) para:

- checkpoint base quando autorizado;
- adapters e merges;
- datasets grandes;
- checkpoints temporários;
- outputs multimodais grandes.

Nunca publicar dataset ou weights sem revisão de licença, privacidade e acesso.

## 7. Identidade de cada experimento

Um experimento precisa ter ID, timestamp, git commit, modelo base revision, dataset revision/hash, config, seed, hardware, framework versions, run logs, metrics, artifact hash e status. Resultados sem estes dados são notas, não resultados reproduzíveis.

## 8. Compatibilidade de runtime e distribuição

Para cada release, manter matriz por:

- Windows/Linux/macOS se pretendido;
- CUDA/ROCm/Vulkan/CPU;
- inference engine;
- BF16/FP16/FP8/GGUF/AWQ/GPTQ ou formato realmente testado;
- text/vision/audio/video;
- contexto e concurrency.

Não exportar toda variante só para preencher tabela; priorizar o que tiver uso real.
