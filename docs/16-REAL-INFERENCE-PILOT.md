# 16 — Inferência local: contratos endurecidos, pesos ainda NOT-TESTED

> **Gate de capacidade após R2 (2026-11-01):** registry de arquitetura não é aprovação de execução. O preflight só dimensiona Qwen3 denso com config explícita e nomes/shapes canônicos; Qwen3.5 permanece bloqueado por sizing desconhecido. Exemplos abaixo são planejamento, não comandos autorizados nem executáveis para Qwen3.5 neste estado. Loader exige relatório limpo e correspondência com state_dict; única exceção é alias Qwen3 tied comprovado. Consulte as [correções R1–R6](18-FINAL-AUDIT.md). RAM cgroup desconhecida/ancestrais ocultos também bloqueia, sem fallback para host.

Estado v0.4.0: **software e API leve testados**, não inferência real aprovada. [ADR atual](adr/0003-INFERENCE-HARDENING.md), [validação](VALIDATION.md), [evidência do hardening](evidence/hardening-validation.json). Nenhum peso/tokenizer upstream, treinamento, aprovação operacional real ou qualidade de modelo nesta missão. A [readiness anterior](evidence/inference-readiness.json) é snapshot histórico, não inventário atualizado de dependências.

## Evidência por candidato e arquitetura

| Candidato exato | Contrato de carregamento implementado | Evidência e limites |
|---|---|---|
| `Qwen/Qwen3.5-0.8B` | config completo `model_type=qwen3_5`, `architectures=[Qwen3_5ForConditionalGeneration]`, text_config qwen3_5_text + vision_config; AutoProcessor/Qwen3VLProcessor e AutoModelForImageTextToText/Qwen3_5ForConditionalGeneration | Registries/AutoConfig TF5.22.1 verificados. Teste slow oficial desse ID documenta processor + conditional generation e caminho CausalLM textual distinto; **não executado aqui**. config.json/tokenizer/template/revision dos pesos não obtidos |
| `Qwen/Qwen3.5-4B` | Mesmo contrato somente se **o snapshot real declarar exatamente essa arquitetura** | Família documentada, registry executado. Config/revision específicos não consultáveis nos hosts autorizados; não presumir equivalência de arquivos, dimensões, kernels ou qualidade ao 0.8B |
| `Qwen/Qwen3-0.6B` | `qwen3` + `[Qwen3ForCausalLM]`; AutoTokenizer/Qwen2Tokenizer e AutoModelForCausalLM/Qwen3ForCausalLM | Registry/AutoConfig verificados. Não confundir com `Qwen/Qwen3-0.6B-Base`, usado pelos testes upstream consultados; não atribuir esses resultados ao checkpoint post-trained |

[Fontes versionadas](SOURCES.md). TF5.22.1 também registra AutoModelForCausalLM para qwen3_5 por compatibilidade VLM e qwen3_5_text; isso é **outro caminho**. Não escolhemos esse fallback só para evitar processor. O Lab carrega o VLM completo, mesmo para smoke textual; não promete remover encoder/memória. Texto puro é normalizado para content blocks de texto, sem carregar imagens/URLs. `AutoProcessor.from_pretrained` pode requerer componentes multimodais da instalação real: a construção completa do processor Qwen sem componentes não pôde ser validada sem stack Torch/vision. Instalação dessa stack é gate, não capacidade demonstrada.

Outros modelos continuam na [comparação](05-FOUNDATION-MODEL-COMPARISON.md), mas Gemma/qwen2/MoE/text-only exports/arquiteturas desconhecidas **não são executáveis por este loader**. Ele falha por ausência de model_type/architectures, classe divergente, auto_map ou pré-quantização. Nome comercial ou ID sozinho não seleciona classe nem prova autenticidade. Headers/hashes não autenticam a origem upstream.

### Template, tools, thinking e geração

Usar template nativo do frontend, com tools explícitas, add_generation_prompt=true e `enable_thinking=false` encaminhado ao Jinja. Isso não demonstra que o template **da revision exata** respeite o knob: templates/tokenizer_config/generation_config dos checkpoints continuam não adquiridos. Não confundir knobs 3.5 com reasoning_effort/preserve_thinking de releases 3.8. Hash de template efetivo por request; erro se não existir template default/não ambíguo.

Texto: tokenizer sem BOS adicional, padding/truncation=false. VLM: processor.apply_chat_template(tokenize=true, return_dict=true, return_tensors=pt), sem truncagem/padding implícitos. Contexto efetivo = menor do limite aprovado e limite declarado do modelo; um único batch não vazio. Saída é sliced a partir do input_count, remove somente EOS final para texto e preserva envelope de tool calls. Resposta vazia ou orçamento excedido falha. Schemas de tools recusam referências externas (URL/arquivo), sem fetch implícito de JSON Schema. Tools só são analisadas pelo [checker](../src/lia_lab/inference_protocol.py), **nunca executadas**; parser apenas envelope Qwen, outros formatos exigem revisão.

Geração greedy, seed42, max_new_tokens exato, num_beams1, use_cache=true, pad/eos nativos (preservando pad ID zero). Dtype explícito: CPU float32, CUDA/ROCm float16 ou BF16 somente se device/build declararem suporte. Sem device_map/offload silencioso, quantização, kernels baixados ou código remoto. Config BF16 de fornecedor não obriga CPU BF16 nem prova kernels. CUDA/ROCm/MPS, drivers, estabilidade numérica e desempenho com pesos continuam NOT-TESTED.

## Autorização: plano → operador → uso único

`approval_ref` foi removido da execução. `seal-model --license-review-ref` guarda **atestação de revisão legal**, não autoriza inferência nem aceita termos.

1. Após aquisição **separadamente autorizada**, selar snapshot local e gerar plan-inference. Nenhum destes comandos baixa algo ou executa modelo.
2. Humano, fora do agente, revisa plano completo, URL/model_id/revision, licença/hash do arquivo legal, manifesto SHA/bytes, suite/código, roots/ID, backend, perfil e limites.
3. No terminal do operador, approve-inference revalida os arquivos, imprime a operação exata e exige a frase `ALLOW LOCAL INFERENCE <SHA256-OPERAÇÃO>`. stdin/stdout TTY obrigatórios, sem --yes. Só então cria grant no store SQLite externo ao checkout/snapshot/roots de pesquisa/aprovados.
4. infer-local não interativo exige **store existente + approval-id**, não uma string livre. Transação BEGIN IMMEDIATE consome grant uma vez; worker também reivindica o grant externo uma vez, não aceita env flags como aprovação. Plano alterado, grant ausente/consumido/expirado/incompatível ou store inválido bloqueia antes de pesos. Tentativa bloqueada/falha/interrompida também queima o grant.

Vinculados: ação **local-inference apenas**, modelo/revision, SHA exato do manifesto, licença, suite, código e argumentos/paths completos. Limites: max output tokens/request, total de requests/tokens, contexto, duração e **zero custo externo USD**. Não há download, treino, publicação ou release permitido. TTL1..3600s (default900), não antes da confirmação; deadline = menor da duração aprovada e expiração restante. Preflight/hashes são preparação antes do claim; a duração de execução começa no claim e inclui setup/worker. Operador controla ambiente gratuito: não existe medidor/bloqueador de billing de um host pago escolhido fora do Lab.

Store em diretório administrado pelo operador, não criado pelo agente. POSIX verifica UID atual e permissões owner-only; Windows não tem essa verificação POSIX aplicada e requer ACL/revisão externa. Confirmação/store/ID **não provam identidade criptográfica ou civil**. Atacante com mesmo UID/controle de código/relógio/SQLite/TTY, cópia ou rollback do DB pode derrotar o gate. Modelo de ameaça: evitar acidente e permitir auditoria em host confiável, não combater administrador/host comprometido. SQLite local, não autorização distribuída/NFS. **Nenhuma aprovação real foi criada nesta missão**; testes usam grants temporários para checkpoint fictício.

```sh
.venv/bin/lia-lab doctor
# Somente após autorização de aquisição e revisão de arquivos reais; placeholders NÃO são comandos prontos:
.venv/bin/lia-lab seal-model /pesos/snapshot /pesos/manifest.json \
  --model-id Qwen/Qwen3.5-0.8B --revision REVISION_REAL_40_HEX \
  --license-id Apache-2.0 --license-file LICENSE --license-review-ref REVISAO_REAL

.venv/bin/lia-lab plan-inference --snapshot /pesos/snapshot \
  --snapshot-manifest /pesos/manifest.json --suite configs/inference-suite.json \
  --research-root /lab/research --approved-root /lab/approved --run-id baseline-001 \
  --device cpu --dtype float32 --repeats 2 --max-tokens 128 --context 2048 --timeout 600 \
  --containment linux-netns-rlimit --output /lab/research/plan.json

# OPERADOR HUMANO em terminal próprio, não agente/CI; store externo a todos os artefatos:
.venv/bin/lia-lab approve-inference /lab/research/plan.json --store /operator/grants.db --ttl 900
# Repetir os MESMOS argumentos do plano, agora em infer-local, mais:
# --approval-store /operator/grants.db --approval-id ID_REAL_RETORNADO
```

## Separação de processo, contenção e sandbox são coisas diferentes

Worker herda permissões OS do usuário. O supervisor filtra variáveis de ambiente (não repassa tokens/API keys comuns), mas isso **não impede leitura de arquivos/segredos pelo mesmo UID**. HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE são flags de bibliotecas, não firewall. trust_remote_code=false e safetensors não eliminam vulnerabilidades de parsers/dependências/kernels. Conteúdo hostil e dados privados exigem sandbox/VM/container avaliado externamente.

| Perfil obrigatório escolhido pelo operador | Controles implementados | Não aplicado / limites |
|---|---|---|
| portable-process | subprocesso, deadline, logs/resultados separados; kill do grupo POSIX ao expirar/interromper | OS CPU/AS/FSIZE/NOFILE/NPROC e rede **não aplicados**; Windows mata somente worker, sem Job Object; não impede processos escapando do grupo |
| linux-rlimit | Linux CPU somente: CPU timeout×4, AS8GiB, arquivo64MiB por arquivo, 128 FDs, NPROC128; efetivos registrados, erro ao aplicar bloqueia | AS é espaço virtual, não RSS; sem hard limit VRAM; NPROC é por UID e pode ser ignorado por privilegiados; sem namespace PID, rede/FS/IPC |
| linux-netns-rlimit | Os limites anteriores + unshare user/net; worker confirma inode de namespace diferente antes de carregar modelo | Somente Linux CPU com suporte real. Erro de unshare ou mesmo inode = falha, sem fallback. Isola rede IP, **não** filesystem ou Unix sockets compartilhados; não é sandbox completo |

`containment.json` registra controles efetivamente aplicados mesmo se faltar Torch. Perfil Linux solicitado em Windows/macOS/GPU é rejeitado. Políticas de rede/FS/VRAM ausentes aparecem como not-applied. API de rlimit e namespace foram testadas em Python descartável neste Linux, não com modelo. CI pode bloquear user namespaces: teste verifica recusa explícita, não simula aplicação. Nenhuma promessa de proteção equivalente em Windows/macOS/AMD.

## Métricas v2 e resultados parciais

- runtime_import_seconds: imports de topo Torch/Transformers; imports lazy de classes ficam nos estágios seguintes.
- frontend_load_seconds: from_pretrained do tokenizer/processor.
- weights_load_and_device_transfer_seconds: pesos + model.to/eval + sincronização.
- generation_seconds_including_prefill: generate + sync; **não** tempo puro de decode.
- output_tokens_per_second_including_prefill: tokens de saída incluindo EOS divididos por esse tempo.
- generation_process_cpu_seconds: CPU do processo durante geração/sync, não utilização total da máquina.
- process_rss_after_load_bytes/process_rss_after_bytes e process_sampled_peak_rss_bytes (50ms): processo, não RAM total; pico amostrado pode perder transitórios.
- torch_gpu_peak_allocated_bytes/reserved_bytes: allocator Torch CUDA/ROCm, não VRAM total/driver/outros processos. MPS não medido.
- prefill_seconds, ttft_seconds, decode_only_tokens_per_second: **null**, sem streaming/instrumentação separada. Potência/utilização GPU não medidas.
- repeat_text_consistency e checks por caso não substituem estatística de estabilidade, revisão humana pt-BR ou benchmark de qualidade.

Resultados recebem completed=false até todos os requests e verificação final. Cada geração concluída é registrada antes de validar texto; resposta vazia pode deixar geração parcial sem request bem-sucedido. Supervisor verifica schema, hash do request, modelo/revision, contagens, ordem, texto não vazio, budgets de entrada/saída, métricas obrigatórias e identidade do perfil de contenção, não apenas um número de sucessos. Estados distintos: blocked, failed, timed-out, interrupted, completed-not-quality-approved. Parciais malformados/lista/JSON quebrado/hash errado não mascaram a falha. Marca de origem em JSON não é assinatura contra adulteração pelo mesmo usuário. Código de saída 0 significa execução completa, **não qualidade/release**.

## Preparação SFT e o que a API real ensinou

Reutilizar Dataset Factory/dedup/splits/grupos/verify-data e planos/resume/export estruturais. `hf_messages` converte tool_calls para type=function/function{name,arguments}, mantém arguments objeto, content=null quando apropriado, adiciona name/tool_call_id aos resultados e exige schema/argumentos/IDs/ordem/retornos consistentes. Não confundir texto afirmando ação com resultado real.

Renderer usa `return_assistant_tokens_mask=true`, campo **assistant_masks** confirmado em TF5.22.1. Suporta sequência única plana de tokenizer ou batch unitário de processor; rejeita batches múltiplos/máscara vazia/full-prompt/inválida/seq longa. Usa máscara nativa, não procura substring nem inventa limites de loss. Renderiza prefixes com a mesma API e exige tokens/máscaras prefix-stable: todo assistant (texto/tool call/fim de turno conforme template) supervisionado, nenhum system/user/tool. Se a template depender do último turno ou BPE/offsets não permitirem provar isso, falha e exige variante de treino auditada.

A simples presença de generation tag não basta: o teste real com tokenizer WordLevel original detectou que span com whitespace final em TF5.22.1 podia estender máscara aos turnos seguintes (end offset sem token). Não corrigimos máscara silenciosamente nem copiamos template para Qwen: renderer rejeita; template local de teste termina a span no token de fim. Testes também cobrem multi-turn, tool call/retorno/continuação, EOS, escopos incorretos e sequência longa. Tokenizer WordLevel/API Jinja reais **não são tokenizer/template Qwen**; processor Qwen completo e forward/backward continuam NOT-TESTED.

`assert_no_suite_overlap` cobre substring normalizada NFKC/casefold/whitespace de prompts da suite em todas as mensagens; não é detecção semântica de paráfrases nem auditoria de direitos/PII. Ainda faltam dados/persona aprovados, baseline real, template/máscaras nativas reais, targets PEFT, save/reload e avaliação pareada antes do treino. Não há treinador nesta fase.

## Hardware, download e próximo gate

Manter Qwen3.5-0.8B para smoke da família, Qwen3.5-4B para capacidade, Qwen3-0.6B como controle textual. Cards/licenças de artefatos, revisions imutáveis e bytes exatos ainda pendentes: hosts HF/ModelScope fora da allowlist. 0.8B×2≈1.6GB e 4B×2≈8GB BF16 são pisos aritméticos **sem** encoder/metadata/cache, não tamanhos de download. Planejamento exploratório: 0.8B em 8–12GB RAM/>=6GB disco; 4B em 32GB RAM/>=24GB disco, sem validação ou cotação. A observação histórica de ~4GB RAM sem GPU não define telemetria atual nem torna 4B não quantizado um alvo seguro; RAM desconhecida no doctor bloqueia o preflight.

[Stack proposta](../configs/runtime-stack.proposal.yaml) não é lock ML validado. [Lock API leve](../requirements-api.lock) serve apenas API sem Torch. Próximo gate: obter metadados exatos em ambiente com acesso autorizado, proposta específica de aquisição/licença/tamanho, aprovação humana fora do agente, ambiente adequado, baseline e revisão. Não houve download de pesos, API/GPU paga, aceitação de termos, dados pessoais ou publicação de adapters/datasets.

Checkpoint-base ≠ Lia Core. Adapter/persona/prompt/template são versionados e aprovados separadamente; memória, ferramentas/permissões, orquestração, percepção, voz e avatar continuam externos, sem acoplamento AIRI.

## Exclusão explícita LFM3

A [pesquisa LFM3](17-LFM3-RESEARCH.md) não altera este piloto. LFM3/d1/custom Python e GGUF continuam sem backend autorizado; LFM Open License v1.0 não está na allowlist Apache. Nenhum registro research-only pode ser convertido em aprovação por string de catálogo. Decisão tipada, geração áudio e auxiliares exigem protocolos específicos antes de suporte executável.

## Preflight Windows por política — 2026-11-02

O [ADR-0004](adr/0004-WINDOWS-MEMORY.md) acrescenta diagnóstico Win32 ao contrato comum. Linux conserva os gates cgroup-v2 anteriores. Windows não depende de Torch/PowerShell/WMI para consultar memória; `ctypes` lê RAM física, commit, processo e limites de Job acessíveis. `best-effort` é padrão; `balanced` e `strict` são opcionais, com requisitos e margens descritos em [hardware](08-HARDWARE-INFRASTRUCTURE.md).

```powershell
.venv\Scripts\python -m lia_lab.cli doctor --memory-policy best-effort
.venv\Scripts\python -m lia_lab.cli doctor --memory-policy balanced --memory-margin-percent 25
.venv\Scripts\python -m lia_lab.cli doctor --memory-policy strict
```

Acrescentar os mesmos `--memory-policy`, `--memory-margin-percent` e `--memory-uncertainty-margin-percent` a `plan-inference` e `infer-local`. O plano normaliza defaults e inclui as três opções em `arguments`, além de `memory_policy` na operação. Qualquer mudança invalida o grant exato. Planos anteriores precisam ser regenerados e revisados pelo operador; nenhuma política concede autorização. `approve-inference` continua exclusivamente humano em terminal próprio.

O orçamento continua `resident * 1.5 + bytes_snapshot + 1 GiB`, condicionado ao contrato de arquitetura existente. A avaliação exige que o orçamento caiba nas disponibilidades e nos caps conhecidos após margem; não confunde físico com commit ou working set. Falha de consulta é desconhecimento, jamais limite ilimitado. `doctor.assessment.allowed` indica suficiência das observações para a política, sem orçamento de modelo; não é licença, grant ou autorização de execução.

`experiment.json.memory_supervisor` contém observação e avaliação preliminar. O worker repete depois da contenção e antes do import ML, e novamente imediatamente antes de carregar pesos. `memory-worker.json` preserva a última avaliação, inclusive bloqueio, com hash do request; o supervisor registra `memory_worker` e `memory_differences` (antes/depois/delta). Relatório ausente/inválido impede promoção a sucesso; se o worker não chegou à coleta, registra motivo. Comparação não atribui causalidade às mudanças. Aprovação/licença/integridade/arquitetura continuam gates separados; Qwen3.5 permanece bloqueado por sizing não implementado.

Há suporte diagnóstico opcional a handle explícito emprestado de Job já conhecido, com associação verificada; a CLI usa consulta NULL e não recebe nem cria handles de terceiros. Uso agregado atual permanece null com fonte null. Cadeia não enumerada aparece em warnings e pode impedir `strict`. Handle explícito também não comprova a cadeia completa. Nenhum desses resultados reserva memória ou garante alocação; alocações concorrentes e fragmentação ainda podem falhar.

O supervisor Windows continua `portable-process`, sem Job próprio de contenção, sem isolamento de arquivos/rede/VRAM. Criar/associar/retomar worker atomicamente e acompanhar accounting requer o launcher planejado no ADR. Os Jobs descartáveis dos testes não são esse launcher nem sandbox. Não houve inferência real, instalação Torch/CUDA/ROCm ou aquisição de pesos.

## Etapa 2 Windows: supervisão controlada da árvore — 2026-11-02

O parágrafo anterior descreve o estado da etapa 1. O [ADR-0005](adr/0005-WINDOWS-CONTROLLED-LAUNCHER.md) implementa o Job próprio no caminho Windows de `containment.supervise`, mantendo o perfil `portable-process` sem promessa de sandbox. Linux/RLIMIT/namespace permanecem inalterados. Não há nova flag para optar por lançamento Windows desprotegido.

`CreateProcessW(CREATE_SUSPENDED)` precede associação e sua confirmação por handle explícito; `ResumeThread` só ocorre depois. `STARTUPINFOEXW` limita handles herdados à entrada NUL e saída/erro em worker.log. Handle do Job é exclusivo do supervisor. O processo principal é reapado e seu código preservado, mas sucesso só ocorre com `ActiveProcesses=0` no Job. Job não sinaliza todo término natural, portanto accounting é a evidência de esvaziamento. Timeout/interrupção/erro termina Job e descendentes, verifica saída/esvaziamento e fecha handles; falhas ficam explícitas e não promovem sucesso.

O plano inclui `containment.windows_launcher`, com método/versão, kill-on-close, 16 processos e teto/regra de commit. Planos e grants antigos precisam de regeneração/revisão humana, sem contorno automático. Com arquitetura conhecida, teto é o envelope do modelo e só pode ser aplicado quando cabe no menor commit disponível após margem. Sem métricas apropriadas, cap é not-applied com motivo; best-effort não inventa valor. Balanced/strict conservam bloqueios; Job próprio não comprova ausência de limites ancestrais. Não usar RAM física ou pico do Job como commit disponível.

Supervisor grava `windows-launcher.json` e `experiment.json.windows_launcher`, vinculados ao SHA do request e da operação. O recibo em memória, flags, fórmula, processo terminado, Job vazio e handles fechados são verificados antes de aceitar resultados; recibo ausente/incoerente ou arquivo forjado não libera sucesso. Pico é nomeado `peak_job_commit_bytes`, sem claim de consumo atual. A coleção de memória do worker antes dos imports e antes dos pesos, comparação supervisor/worker, licença/hashes, grant de uso único e bloqueios Qwen3.5/LFM3 continuam obrigatórios.

Testes reais Windows x64 usam filhos descartáveis e nenhuma alocação de stress. [VALIDATION](VALIDATION.md) separa mocks, APIs reais, skips e limites. Sem sandbox de filesystem/rede/identidade, reserva de memória, aquisição de pesos, Torch/GPU, inferência ou treino. Versões/arquiteturas Windows não exercitadas permanecem NOT-TESTED.
