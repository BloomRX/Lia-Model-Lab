# 08 — Hardware e infraestrutura

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Três ambientes que não devem ser confundidos

1. **PC do proprietário:** Ryzen 5 5500, ~16 GB RAM, RX 580 2048SP ~4 GB aparecem no contexto e na v1.0, que atribui esses números a benchmark histórico não recuperado nesta missão; documentos arquiteturais Lia falam RX 580 8 GB. Não houve acesso ao PC: **configuração atual não confirmada**.
2. **Sandbox observado historicamente em 2026-10-30:** Linux x86_64 6.1.158+, Python 3.11.2, 2 CPUs visíveis, MemTotal 4.034.452 kB (~3,85 GiB), disco ~21,8 GB total/~20,7 GB livres antes das cópias. Sem `/dev/dri`, `/dev/kfd`, `/dev/nvidia0`; nvidia-smi/rocminfo/vulkaninfo ausentes. **Nenhuma GPU utilizável evidenciada**. São observações da sessão, não limites garantidos Arena.
3. **Treino remoto:** ainda não escolhido/aprovado. Precisa de GPU/VRAM, região, privacidade, quotas, armazenamento, custo máximo, duração e desligamento definidos antes de execução.

## Compatibilidade real versus anunciada

| Stack | Uso | Evidência / conclusão |
|---|---|---|
| PyTorch/Transformers/PEFT/TRL | CPU tests, SFT LoRA/QLoRA remoto | Documentados; nenhum modelo/kernels carregado nesta missão. Pin exato obrigatório |
| ROCm | Treino/inferência em AMD suportada | Matriz AMD oficial consultada não lista RX 580/gfx803; **não planejar suporte oficial**. Patches comunitários não equivalem a suporte validado |
| Vulkan + llama.cpp | Inferência local CPU/GPU e offload parcial | README upstream lista Vulkan/HIP/CPU e Qwen3.5-0.8B; RX 580/driver, projector visual e quant específico precisam de teste no PC |
| llama.cpp CPU | Fallback independente de CUDA | Candidato inicial de inferência pequena; tokens/s não medidos. Não confundir engine de inferência com pipeline QLoRA PyTorch |
| Unsloth | Otimização de treino e ferramentas de execução | README anuncia AMD/Intel/CPU/Vulkan; notebook Qwen3.5-4B Vision. Isso **não comprova treino Vulkan na RX 580**, nem suporte ao candidato 3.8 exato. Core e UI têm licenças distintas |
| Axolotl / LLaMA Factory | Orquestração de treino | Alternativas condicionadas a suporte da arquitetura/processor; não eliminam dependências do backend |
| JAX Gemma oficial | FT/LoRA Gemma | Código/documentação disponíveis; suporte de uma variante não valida todas |
| ASR/TTS CPU | Voz desacoplada | faster-whisper/Piper candidatos; licença de voz e RTF no CPU real pendentes |

Fontes: framework snapshots e matriz AMD em [SOURCES](SOURCES.md). Não instalar stack CUDA de vários GB em PC sem CUDA. Não usar env override para fingir suporte de GPU. Hardware AMD novo suportado pode ser opção remota, mas não basta “é AMD”.

## Plano operacional sem depender só de CUDA

- Local: editor/Git, schema/dedup do piloto em memória limitada (16 MiB/10.000 linhas; streaming futuro), manifests, testes mocks/replay, modelos pequenos autorizados em CPU; depois Vulkan opcional. Com ~16 GB RAM evitar carregar corpora/mídia inteiros.
- Remoto: container/env lock com backend apropriado, smoke test e medição pico antes do job; checkpoints periódicos e recuperação por hash. NVIDIA ou AMD suportada são alternativas, sem impor dependência arquitetural de CUDA ao produto.
- Avaliação: mesma suíte/config por variante; hardware distinto implica resultados de performance separados, não comparação direta enganosa.
- Conversão/quantização: processo offline por architecture/converter suportados; ter RAM/disco para base+merge+quant+temporários simultâneos; validar round trip e modalidade visual/áudio.
- Distribuição: adapters/masters/quantizações em armazenamento aprovado privado até release gate; Git só manifest, checksums, configs e métricas redigidas.

## Dimensionamento e custos

Fórmulas e tabela de pesos em [05](05-FOUNDATION-MODEL-COMPARISON.md). Não usar N×0,5 byte como VRAM QLoRA. Incluir encoders, KV/estado recorrente, contexto, batch/concurrency, ativação, optimizer, staging RAM e buffers do driver. 27B Q4 teórico 13,5 GB já ultrapassa VRAM histórica e deixa pouca RAM de 16 GB para OS/cache; **não recomendar como alvo local inicial**.

Antes de contratar: custo_total = horas_GPU×tarifa + storage×tempo + transferências + margem; definir limite e auto-stop, não orçamento aberto. Fazer download/treino só após aprovação específica de tamanho/custo/dados; nenhuma tarifa inventada nesta missão.

Diagnóstico futuro no PC: SO, CPU/RAM, PCI ID/modelo real/VRAM, driver, Vulkan devices/capabilities, ROCm matrix e logs de inferência pequena autorizada. Reconciliar 4/8 GB por evidência datada, não por suposição da marca RX 580.

## LFM3 local: CPU primeiro como hipótese; Vulkan separado

[Análise GGUF/llama.cpp](17-LFM3-RESEARCH.md): tag b11960 fixado em8642541b255bfb5dc39cd351a178be09013a55d6 contém código LFM3/mtmd/d1; não foi compilado nem executado. Documentação Audio/d1-Omni pede v0.8.0/b11960+, mas mínimo Omni do card GGUF ainda não pôde ser reconsultado. Não usar tabela antiga b7075/LFM2 como prova de suporte LFM3.

Ryzen5 5500/16GB/RX5802048SP ~4GB é referência histórica, não telemetria. CPU é candidato a probe portável, sem promessa de velocidade. Vulkan AMD depende de driver, operações, offload de encoder/codec e build exatos; ROCm/RX580 não aprovado. Quantização nominal não inclui KV/cache/buffers/mmproj/codec/contexto/OS. Windows documentado não significa contenção equivalente ao Linux. Sem downloads/builds/pesos/stack GPU nesta missão.

Na auditoria de 2026-10-31, o sizing do doctor retornava RAM null quando não encontrava layout cgroup v2 reconhecido. Linux continua sem substituir esse desconhecido pela RAM do host; cgroup v1/macOS ou hierarquias não cobertas bloqueiam. Windows recebeu o adaptador abaixo em 2026-11-02. A observação histórica acima não é telemetria atual.

## Diagnóstico Windows — 2026-11-02

[ADR-0004](adr/0004-WINDOWS-MEMORY.md) define a avaliação multidimensional, testada em Windows real x64/Python 3.11. `doctor.memory` separa RAM física, commit global/chamador, commit privado e working set. Fontes Win32, erros, cobertura do Job, estimativa e margens aparecem no JSON. `ram` permanece como resumo de compatibilidade; no Windows seu available é o mínimo das disponibilidades calculáveis antes da margem, nunca RAM total.

| Política Windows | Margem padrão | Evidência exigida |
|---|---|---|
| best-effort | 10% + 10 pontos quando parcial | RAM física e commit do chamador; secundárias desconhecidas avisam, caps conhecidos insuficientes bloqueiam |
| balanced | 20% + 10 pontos quando parcial | Também commit global, commit privado, associação e limites do Job consultado; cap agregado sem uso atual bloqueia; cadeia parcial avisa |
| strict | 30% + 10 pontos quando parcial | Todas as anteriores e cadeia de Jobs coberta; cadeia não enumerada bloqueia |

`--memory-margin-percent` e `--memory-uncertainty-margin-percent` configuram inteiros não negativos, soma <=90. Adicional é aplicado uma vez se houver incerteza; não mede confiança. As margens Windows não mudam o contrato Linux/cgroup. Menor headroom calculável limita a estimativa; cap agregado desconhecido não vira headroom e é avaliado separadamente como teto. Memória observada não está reservada e pode mudar antes da alocação.

Neste host, a consulta NULL do filho em Job aninhado não expôs o cap do Job de teste, apesar da associação confirmada e da leitura por handle explícito. Registrar cadeia não enumerada evita prometer visibilidade completa. Não coletamos uso agregado por API não documentada nem por pico. [Validação nativa e limites](VALIDATION.md); launcher com Job próprio permanece segunda etapa planejada, sem alterar Jobs externos.
