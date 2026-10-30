# 16 — Primeiro piloto real: infraestrutura pronta, inferência ainda bloqueada

Estado: **código e contratos offline testados; checkpoint real NOT-TESTED**. Nenhum peso baixado ou modelo carregado nesta fase. [ADR-0002](adr/0002-LOCAL-INFERENCE.md), [registro observado](evidence/inference-readiness.json), [validação](VALIDATION.md).

## Pesquisa e seleção, 2026-10-30

Reconsultados repositórios oficiais [Qwen3.5, hoje redirecionado para Qwen3.8](https://github.com/QwenLM/Qwen3.8/tree/2ea10dc725823bf7c3e21ce8557cbe15245132ae), [Qwen3](https://github.com/QwenLM/Qwen3/tree/7a2f61ffc7a20d47efcd2bf97f6f2bf52729042e), [Gemma](https://github.com/google-deepmind/gemma/tree/9e1f74131ba9d45e5fe6ae7bb3941d9f2abb39c3), [SmolLM](https://github.com/huggingface/smollm/tree/438be18dae658a638f3a6976fdf5190bb6d68619), Transformers, PEFT, bitsandbytes e llama.cpp. O README atual da família Qwen distingue releases 3.5/3.6/3.8: não renomear um checkpoint 3.5 para 3.8 nem extrapolar MoE aos densos pequenos.

**Limitação de pesquisa desta fase:** hosts de pesos Hugging Face/ModelScope e ai.google.dev não estão na allowlist de rede do ambiente. Os cards consultados na consolidação estão registrados em [05](05-FOUNDATION-MODEL-COMPARISON.md) e [fontes](SOURCES.md); aqui não alegamos nova consulta aos arquivos individuais de pesos. SHA upstream de checkpoint, listagem/bytes exatos, licença/notices e hashes de tokenizer/template continuam **PENDING**. Commit do repositório de código não é revision dos pesos. Nenhum campo foi preenchido com SHA inventado.

| Checkpoint exato proposto | Arquitetura/escopo | Direitos/formato e compatibilidade documental | Decisão e limites |
|---|---|---|---|
| `Qwen/Qwen3.5-0.8B` | denso híbrido Gated DeltaNet/atenção + visão; tamanho nominal 0.8B | Safetensors/Transformers, templates da família e tools documentados; licença de pesos Apache declarada na pesquisa anterior, confirmar arquivo exato; GGUF precisa provenance própria | **Primeiro smoke recomendado da arquitetura 3.5**, não qualidade Core; encoder/cache aumentam footprint; PEFT/QLoRA ainda sem probe |
| `Qwen/Qwen3.5-2B` | denso híbrido VLM, nominal 2B | Mesma investigação por checkpoint; não herdar módulos/tokenizer de 0.8B | Intermediário, sem vantagem medida que justifique dobrar o primeiro download |
| `Qwen/Qwen3.5-4B` | denso híbrido VLM, nominal 4B | Safetensors e Transformers; modelos auto mapeados no código atual; quantização/LoRA/QLoRA condicionais | **Candidato de capacidade Lia Core**, não alvo BF16/FP32 adequado a sandbox de 4 GB |
| `Qwen/Qwen3.5-9B` | denso híbrido VLM, nominal 9B | Release confirmado pelo README, artefatos exatos pendentes | Adiado: custo maior sem necessidade para provar infraestrutura |
| `google/gemma-4-E2B-it` | 2.3B efetivos, ~5.1B com embeddings conforme card anterior; multimodal/PLE | JAX oficial `GEMMA4_E2B_IT`, Transformers atual tem `gemma4`; licença Apache declarada no card anterior, arquivo de pesos ainda gate | Não confundir E2B com residente 2B; pouca vantagem de memória no piloto |
| `google/gemma-4-E4B-it` | 4.5B efetivos, ~8B com embeddings conforme card anterior | Checkpoint JAX IT distinto de PT; safetensors HF e template exato precisam inventário | Adiado pelo footprint/complexidade; áudio futuro não é requisito do Core textual |
| `Qwen/Qwen3-0.6B` | denso texto, nominal 0.6B, atenção convencional | README oficial declara Apache-2.0 para pesos, Transformers/template thinking e tools; quantizações precisam revisão separada | **Controle de engenharia alternativo**, mais simples que híbrido VLM; não escolher como identidade final por caber |
| `HuggingFaceTB/SmolLM3-3B` | denso texto, nominal 3B; receita pública | Repo oficial confirma checkpoint distinto de `-Base`; licença/artefatos de pesos e pt-BR precisam card exato | Vantagem concreta: transparência de treinamento e stack textual simples; não menor que smoke 0.8B, sem vantagem pt-BR medida; loader desta fase não o permite |

Qwen anuncia 201 idiomas/dialetos para a família 3.5; isso não demonstra domínio de pt-BR em cada tamanho. Qwen3 declara 100+. Para Gemma/SmolLM, não extrapolar português de benchmarks multilíngues gerais. Todos os candidatos: pt-BR/persona/instruções/tools locais **NOT-TESTED**. Pesos abertos não autorizam dados/voz/marca. Apache-2.0 permite uso, modificação e distribuição com condições (licença/notices/alterações); a allowlist do CLI é política de piloto, não interpretação jurídica nem aceite pelo usuário.

## Proposta de download — não autorização

Fonte de pesos: organização oficial Hugging Face de cada ID acima, **não adquirida aqui**. Somente após acesso aos metadados: congelar revision de 40 hex, inventário e tamanho exato; revisar licença/notices; apresentar ao proprietário para autorização específica. Não usar estimativa como tamanho confirmado.

| Alvo | Pesos BF16 nominais, limite inferior decimal | CPU FP32 residente nominal | Orçamento exploratório de ambiente, não mínimo validado |
|---|---|---|---|
| Qwen3.5-0.8B | ~1.6 GB, sem encoder/metadata | ~3.2 GB, sem extras | 8–12 GB RAM, >=6 GB disco; GPU opcional ~4 GB livres a investigar |
| Qwen3.5-2B | ~4 GB, sem extras | ~8 GB, sem extras | 16–24 GB RAM, >=12 GB disco; GPU ~8 GB a investigar |
| Qwen3.5-4B | ~8 GB, sem extras | ~16 GB, sem extras | 32 GB RAM, >=24 GB disco; GPU ~12–16 GB livres a investigar |
| Qwen3-0.6B | ~1.2 GB, sem extras | ~2.4 GB, sem extras | 8 GB RAM preferível, >=4 GB disco; sem garantia no host de 4 GB |
| Gemma4 E2B/E4B | >=10.2/16 GB pelas contagens com embeddings, encoders podem acrescentar | >=20.4/32 GB | Não dimensionar como denso 2B/4B; obter inventário antes de reservar ambiente |

São hipóteses conservadoras para contexto curto/uma requisição, não medições/cotações ou requisitos oficiais. Staging, cache de pacotes, shard duplicado e conversão podem exigir mais disco. GPU remota: custo desconhecido, **não provisionado**; CPU local não envolve tarifa de GPU, mas tempo/energia não medidos. Para GGUF Q4, 0.8B × 0.5 ≈ 0.4 GB é apenas piso aritmético: scales, pesos não quantizados, tokenizer/projector/cache e engine acrescentam memória. Não há repositório/revision/bytes de GGUF aprovados; não baixar quant comunitário pelo nome parecido.

## Implementação e fronteiras

- `environment.py`: RAM disponível/cgroup v2, CPU, disco, nós de dispositivos, versões de pacotes sem importar Torch. RAM não suportada retorna null e bloqueia sizing, em vez de supor capacidade. cgroup v1/Windows/macOS não têm medição validada aqui.
- `checkpoints.py`: `seal-model` e verificação de snapshot local independente, sem symlinks/código/pickle. Inventário completo e headers safetensors reais, índice de shards, modelo explicitamente permitido (`qwen2`, `qwen3`, `qwen3_5`, `gemma4`), revisão/atestações/licença. Rejeita quantização prévia não implementada. Não autentica upstream offline nem prova compatibilidade de cada variante.
- `inference.py`: novo registro `kind=inference` sob o mesmo `research_root/experiments`, sem modificar registro de planos SFT existente. Estados started/blocked/failed/completed-not-quality-approved; falhas, timeout e execuções parciais preservados. Hashes de snapshot, suite, request, resultados, código/lock e estado Git; duração observada, custo null se não medido. ID novo, raiz aprovada nunca escrita.
- `inference_worker.py`: subprocesso separado, Transformers local-only/offline, trust_remote_code=false, safetensors, template nativo e codificação sem BOS duplicado, greedy/seed, sem truncagem implícita ou execução de tools. A referência carrega o VLM inteiro para texto, **não** promete reduzir encoder. CPU float32; CUDA/ROCm/MPS explícitos, kernels realmente verificados somente ao executar.
- Sem implementação atual GGUF, quantização, API externa, vLLM, streaming ou trainer. A fronteira de subprocesso/request/result permite backend novo sem acoplar dados, identidade, memória ou avatar.

Métricas previstas no worker: tempo tokenizer/model load (exclui import de dependências), latência de geração **incluindo prefill**, tokens gerados incluindo EOS por essa duração, CPU seconds, RSS após carga/requests e pico amostrado a 50 ms, picos allocated/reserved do alocador Torch CUDA/ROCm, repetição e resultados por caso. São amostras/RSS de processo e allocator, não total de RAM/VRAM/potência do sistema. TTFT, throughput decode-only, utilização GPU/potência e VRAM MPS ficam null/não medidos. A primeira requisição é fria, explicitada por repeat=0; sem warmup escondido. Textos crus permanecem em armazenamento local; uma falha não é removida nem substituída por fixture.

## Executar após autorização e artefatos reais

```sh
# Diagnóstico sem pesos e sem Torch:
.venv/bin/lia-lab doctor --storage /caminho/lia-research

# Em venv de runtime separado, escolher wheel Torch CPU/CUDA/ROCm conforme hardware.
# Versões candidatas e gates: configs/runtime-stack.proposal.yaml (NÃO lock testado de ML).
# pip install -e '.[inference]' instala Transformers opcional, não escolhe wheel Torch.

# Materializar snapshot oficial revisado SEM symlinks, guardado fora do Git.
# LICENSE deve ser o arquivo real revisado; placeholders abaixo NÃO devem ser executados literalmente.
.venv/bin/lia-lab seal-model /pesos/snapshot /pesos/snapshot-manifest.json \
  --model-id Qwen/Qwen3.5-0.8B --revision REVISION_REAL_40_HEX \
  --license-id Apache-2.0 --license-file LICENSE --approval-ref APROVACAO_REAL

.venv/bin/lia-lab infer-local --snapshot /pesos/snapshot \
  --snapshot-manifest /pesos/snapshot-manifest.json --suite configs/inference-suite.json \
  --research-root /caminho/lia-research --approved-root /caminho/lia-approved \
  --run-id baseline-qwen35-08b-001 --approval-ref APROVACAO_REAL \
  --device cpu --dtype float32 --repeats 2 --max-tokens 128 --context 2048 --timeout 600
```

O CLI não valida a existência jurídica da referência de autorização: o operador precisa da aprovação efetiva, não inventar texto para desbloquear. Não há download sequer com flags de execução. CPU tem envelope host de 1.5 × elementos armazenados × bytes do dtype + 1 GiB; conservador e não garantia contra OOM. GPU verifica também memória livre via Torch, 1.25 × residente + 512 MiB. Driver/versão/kernel incompatível deve produzir failed, não fallback silencioso. O timeout limita o subprocesso (import/load/generation/verificação final), não o hash/preflight anterior; a duração total registrada pode ser maior. Comando retorna 2 para blocked/failed e 0 só para execução completa, **não aprovação de qualidade**.

## Casos e comparação de resultados

[Suite original](../configs/inference-suite.json): pt-BR com restrição de orçamento fictícia (humano), selo exato PONTE-47, objeto JSON de biblioteca, conversa multi-turn cor da caixa, chamada fictícia consultar_estante. Dois repeats mínimos medem estabilidade de execução/texto, não variância estatística suficiente para benchmark. Não pontuar personalidade por string exata. Parser de tool-call reconhece somente envelope Qwen; saída Gemma/outro formato deve ser revista crua, não lida como ferramenta realmente executada.

O contrato antigo `compare` exige base e adapter, e não é substituído por este smoke. Os resultados ricos de inferência **não são automaticamente convertidos para exact-match-v1**: essa comparação precisa dataset/test_hash/protocolo/gabaritos selados comuns e variantes reais. Testes de software/safely-failing worker não entram como resultados de qualidade. Não ajustar treinamento com estes prompts nem usar o teste holdout para escolher hiperparâmetros.

## Preparação SFT implementada versus pendente

Reutilizar Dataset Factory, separação por grupos, verify-data, plano, registro, verify-resume e export estrutural existentes. `training_prep.py` converte tool calls canônicas para o formato HF, exige schema explícito, renderiza assistant-only labels com máscara **nativa de generation spans**, falha se inexistente/inválida ou se a sequência exceder limite. Não inventa fronteiras de loss por substring, não trunca trajetórias e não inicia treinamento. `assert_no_suite_overlap` detecta igualdade normalizada de prompts de usuário contra esta suite; **não** detecta paráfrases/near-dedup semântico. Runner futuro deve chamar o gate em todos os splits de treino antes de renderizar.

Os testes do renderer usam um tokenizer sintético declarado, somente para verificar contrato/máscara. Templates reais de Qwen/Gemma podem não conter generation spans: será necessário template de treino auditado, hash próprio e teste de limites com tokenizer real. Não anunciar essa preparação como tokenizer Qwen validado.

Proposta pequena em [runtime-stack](../configs/runtime-stack.proposal.yaml): LoRA primeiro, 30 passos, seq512, microbatch1, acumulação4, rank8/alpha16/dropout0.05, LR1e-4; tudo ajustável após probe e dados aprovados, não valores ótimos. Worker apenas inventaria módulos Linear reais quando carregar; não aprova targets nem cria adapters. QLoRA NF4/double-quant exige probe de versão/wheel/backend/gradientes, não apenas sucesso de inferência.

Antes do treino: baseline completo e revisão pt-BR, direitos/persona/dados, máscara real, forward/backward finito e PEFT save/reload equivalentes, optimizer/scheduler/RNG + config/data/código/lock para retomada. Gate de melhoria: menos falhas em validação independente de JSON/instrução sem regressão de pt-BR/tools, comparação pareada e teste selado não usado em tuning. Salvamento/export estrutural jamais prova melhoria. Métricas/checkpoints reais continuam ausentes.

## Identidade técnica

Checkpoint-base ≠ Lia Core. Adapter futuro é artefato versionado separado; persona/política e prompt têm aprovação própria; template é formatação técnica. Memória, execução e permissões de ferramentas, orquestração, visão/áudio, voz e avatar continuam fora dos pesos. Neste piloto o modelo não recebe uma persona “Lia” ficticiamente aprovada, não persiste memória e não executa ações. Trocar base/adapter/template não obriga reconstruir a aplicação.
