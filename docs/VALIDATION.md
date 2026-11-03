# Validação atual — auditoria final e retificação documental (2026-10-31)

## Atualização posterior — preparação Qwen3.5-0.8B, 2026-11-02

- Windows x64/Python 3.11.0: `.venv\Scripts\python -m pytest -q`: **359 passed, 39 skipped**; `.venv-api\Scripts\python -m pytest -q`: **367 passed, 38 skipped**. Skips incluem plataformas/cgroups/namespaces indisponíveis, API ausente no ambiente base, symlink sem privilégio e módulo ML explicitamente opt-in.
- Testes específicos contrato/aquisição: **32 passed, 1 skipped**. Sem rede; respostas HTTP fictícias verificam retomada, restart, corrupção, tamanho, overwrite e disjunção de paths.
- Ambiente externo CPU fixado: `LIA_TEST_ML_RUNTIME=1`, snapshot explícito e flags offline; `python -m pytest tests/test_qwen35_ml_runtime.py -q`: **4 passed**. Loader com pesos **sintéticos**, alias por identidade Parameter e MTP não zero; frontend original nos cinco casos; modelo oficial em **meta**. Nenhuma geração ou carga de pesos originais.
- Inventário oficial adquirido/verificado: 12 arquivos/1769978895 bytes fora do Git. Headers reais: 488 tensores/873438784 elementos; contrato completo de shapes/dtypes/índice aprovado automaticamente. Grant/seal/plano reais ausentes; revisão humana da licença pendente.
- [Evidência com orçamento](evidence/qwen35-first-pilot.json): estado **blocked**, motivo `host RAM/commit below memory loading envelope with margin`; envelope 8084353423 bytes, política best-effort 10% + 10%. `doctor` sem orçamento não comprova capacidade do modelo. Requests reais 0; picos/latência/qualidade pt-BR e visão NOT-TESTED por bloqueio antes da execução.

Alteração revisada pelo principal, sem delegação independente. [ADR-0006](adr/0006-QWEN35-PINNED-CPU-PILOT.md) e [relatório](19-QWEN35-FIRST-PILOT.md) distinguem essa nova conformance da evidência histórica abaixo. CI e commit final são reportados na PR, sem autoatestação anterior à execução.

Retificação: histórico completo/API confirmam17 commits exclusivos em4eadfa3 e19 em9db718c; números antigos19/21 vieram de checkout shallow. Revisão independente **NOT PERFORMED**, sem mecanismo real de delegação. SHA/contagem/CI após a retificação são registrados na PR. Não houve alteração de código executável nesta correção.

Partida da auditoria anterior `4eadfa39860914ea1c84e19e0bc246933a44ae62`; baseline reproduzida **157 passed, 1 skipped**. Após correções: **197 passed, 1 skipped** na base e **205 passed** no ambiente API TF5.22.1 sem Torch. Os 40 casos adicionais cobrem lacunas descritas no [relatório de auditoria](18-FINAL-AUDIT.md); não são validação de modelo.

Instalação limpa adicional: wheel em terceiro venv, import de todos os módulos fora da árvore fonte, schemas empacotados, doctor/validate-data e ausência de Torch verificados. pip check em três ambientes, compileall e diff --check PASS. Manifesto regenerado/verificado após edições; parsers, links e hashes abrangem fontes mantidas, não arquivos de checkpoint. Estado remoto final é registrado na PR após push.

[Evidência estruturada](evidence/final-audit.json). Revisão sequencial, sem subagentes/revisão independente simulada. Licenças/código LFM3, pesos/tokenizers reais, treino e hardware continuam NOT-TESTED/BLOCKED; não houve autorização real ou merge. Relatórios abaixo são históricos, com contagens e alcance das respectivas missões, não estado final de testes.

---

# Relatório anterior — pesquisa LFM3 (2026-10-31)

Partida `d535f92845180f81af5acc5501481fe8319b4377`. Snapshot restaurado comparado byte a byte com remoto: **zero diferenças**, antes de alinhar HEAD/index sem modificar arquivos. A mesma PR permanece aberta, sem merge. Relatório anterior abaixo preserva o alcance específico do hardening.

- **157 passed, 1 skipped** na suíte base; **165 passed** no ambiente API Transformers5.22.1 real, sem Torch. Incluem testes anteriores e 14 novos casos de catálogo/gates; nenhum teste carrega LFM3.
- Novo schema/verificador exige 13 identidades distintas, contratos research-only, licença pendente e ausência de execução; decisão não pode ser rotulada como conversa. Testes confirmam recusa das seis combinações de arquitetura/tipo LFM3/d1 pelo loader atual e recusa da LFM Open License pelo seal.
- `pip check` em ambos os ambientes, compileall e `git diff --check`: PASS. Ambientes leves recriados a partir dos locks existentes, sem novas dependências ou Torch.
- Fontes oficiais GitHub, receitas e conversor/template consultados como texto, não executados. Cards HF, LICENSE/NOTICE individuais e texto vinculante completo não foram adquiridos; guia oficial não substitui auditoria jurídica.
- Nenhum peso/GGUF/tokenizer upstream/dataset, inferência real, treinamento, recurso pago, aceite ou grant operacional real. Compatibilidade LFM3 e hardware permanecem **NOT-TESTED**.
- Manifesto regenerado e verificado após edições. Estado remoto será verificado no HEAD final e registrado na PR, sem depender de CI histórico.

[Pesquisa e decisão](17-LFM3-RESEARCH.md) · [evidência estruturada](evidence/lfm3-research.json).

---

# Relatório anterior — hardening v0.4.0

Data: 2026-10-30. Partida: `2cb652353e1429ae75dd647e824edc107019babd`, PR #1 OPEN e main não integrada. Antes de editar, comparação byte a byte do snapshot com o remoto, alinhamento do HEAD/index restaurados e execução dos **84 testes anteriores PASS**. Nenhum trabalho recente remoto sobrescrito; sem force push/merge.

## Executado

| Procedimento real | Resultado e alcance |
|---|---|
| Suíte base `.venv/bin/python -m pytest -q` | **143 passed, 1 skipped**. Skip é o módulo TF opcional, executado no ambiente abaixo; não é inferência faltante mascarada |
| Ambiente separado `.cache/api/.venv`, lock requirements-api.lock | **151 passed**, com **Transformers5.22.1 real e sem Torch**. Config/registry/API Jinja/tokenizer WordLevel próprio, não tokenizer/modelo Qwen |
| `pip check` em ambos os ambientes | Sem dependências quebradas; conflito safetensors corrigido para0.8.0 |
| Compilação `python -m compileall -q src scripts` | PASS |
| CLI doctor/help e recusa approve-inference não interativo | Executados/testados, sem criar grant real |
| Autorizações em testes | Stores temporários de checkpoint fictício, confirmação TTY simulada declarada, limites/modelo/revision/hash/suite/código/paths/ação, expiração/futuro/TTL, concorrência, consumo, worker claim, finalização e replay. Nenhuma autorização operacional real |
| Backend em testes | Mocks de Auto classes, frontend, from_pretrained/offline/dtype, processor textual, contexto, output slicing/EOS, texto vazio, tools opacas; mocks não comprovam pesos |
| API real HF5.22.1 | AutoConfig e mappings; assistant_masks, multi-turn, tool calls/retornos, EOS e spans ruins com tokenizer original. Nenhum forward/backward/modelo instanciado |
| Processo real sem Torch | Worker com grant sintético falha por dependência; worker sem grant recusa mesmo com flags offline. Nenhum resultado de linguagem gerado |
| Linux recursos/rede | RLIMITs aplicados/consultados em Python descartável; unshare user/net aplicado e inode diferente confirmado neste host. Timeout real de filho descartável testado. Não teste de proteção de Windows/macOS/GPU nem sandbox completo |
| Resultados/falhas | Stubs sintéticos testam completed, incomplete, failed, timed-out, interrupted, parciais, hash/model/order divergentes, respostas vazias, JSON/listas corruptos e não sobrescrever ID. São contratos, não métricas de modelo |
| Verificador e manifest | JSON/YAML/TOML/frontmatter/schema, links locais, cobertura/bytes/SHA, perfis/skills e symlinks realmente verificados; regenerado e repetido sem flag. Contagens finais no output do verificador/PR |
| Marca e whitespace | BRAND-STANDARDS igual à main consultada; git diff --check limpo |

Correções decorrentes de falhas reais durante desenvolvimento: pin safetensors antigo não satisfazia TF5.22.1; máscara nativa com whitespace final podia incluir tool/user posterior; gate antigo de falha sem Torch precisou exigir grant sintético antes de alcançar import, mantendo também teste explícito de recusa sem grant. Teste do próprio verificador detectou link de evidência ainda não criado durante a edição; artefato foi criado e testes repetidos. Não ocultar esses resultados intermediários como PASS.

## Reprodução sem pesos

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_repository.py
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src scripts
.venv/bin/lia-lab doctor

# Ambiente API separado: somente libs pequenas, sem Torch/modelos/tokenizers upstream.
python -m venv .cache/api/.venv
.cache/api/.venv/bin/pip install -r requirements-api.lock
.cache/api/.venv/bin/pip install --no-build-isolation --no-deps -e .
.cache/api/.venv/bin/python -m pytest -q
.cache/api/.venv/bin/python -m pip check
```

CI tem jobs separados base e lightweight-api; ambos não adquirem pesos. Estado remoto deve ser consultado no HEAD final, não inferido dos testes locais. Em CI com user namespaces proibidos, teste verifica recusa explícita, não registra namespace aplicado. Regenerar manifest após últimas edições; verificador não valida anchors Markdown, todas as URLs externas nem autenticidade/legalidade de conteúdo por hashes.

## NOT-TESTED / desconhecido

- Config.json, LICENSE, revision, tokenizer_config, template e geração originais dos checkpoints: hosts de pesos fora da allowlist. Fonte oficial de código/tests não substitui artefato exato. Qwen3.5-0.8B é citado por teste slow upstream, **não rodado**; para0.6B o teste consultado é **-Base**, não post-trained.
- Inferência real, qualidade pt-BR/persona/tools, RAM/VRAM/latência/throughput de modelo: nenhum checkpoint, runtime Torch ou GPU. Todos sem resultado real; não há modelo Lia aprovado.
- Processor Qwen completo com seus componentes, dtype/kernels/driver CUDA/ROCm/MPS/CPU com pesos, proteção em Windows/macOS/AMD/GPU e robustez contra conteúdo hostil: sem execução específica. RLIMIT/namespace não provam segurança de modelos.
- PEFT, forward/backward, treinamento, reload/merge/quant/export equivalentes e melhoria mensurável de adapter: não realizados. Renderer validado com API leve não aprova template Qwen real ou dados/persona.
- Revalidação/execução upstream AIRI e descoberta/delegação real de agentes: não realizadas; fallback sequencial, sem revisão independente simulada.

## Custos e governança

Zero pesos/datasets externos adquiridos, zero GPU/API paga, zero dados pessoais, zero licença aceita, zero publicação de pesos/datasets/adapters. Somente dependências pequenas de desenvolvimento/API foram instaladas. Grants dos testes são fictícios/temporários; operador humano deve confirmar uma operação real em terminal próprio e store externo. JSON/SQLite/TTY não autenticam identidade criptográfica; código/relógio/host e conta local são fronteiras de confiança.

[Guia atual](16-REAL-INFERENCE-PILOT.md), [ADR](adr/0003-INFERENCE-HARDENING.md), [evidência](evidence/hardening-validation.json). Histórico de relatórios permanece no Git, sem coleções documentais paralelas.

## Correções R1–R6 — 2026-11-01

Partida: `395241b73a3357aa8610086068d70ee5145a40a0`. Resultados atuais desta missão substituem, mas não apagam, contagens históricas acima:

| Verificação | Resultado |
|---|---|
| `pytest tests/test_review_resources.py tests/test_review_loading.py tests/test_review_whitespace.py -q` | 58 passed; cenários sintéticos, sem inferência |
| Suíte base | 255 passed, 1 skipped (API opcional) |
| Suíte API leve TF5.22.1 sem Torch | 263 passed |
| pip check base/API | Sem dependências quebradas |
| compileall src/scripts/tests | PASS |
| Verificador + PACKAGE-MANIFEST | PASS após regeneração; 110 arquivos mantidos |
| `git diff --check` e comparação explícita main...HEAD | PASS após remoção da linha extra de conftest |
| Gate CI | `python scripts/check_whitespace.py`, revisões explícitas do payload GitHub; histórico completo |

Antes de corrigir foram reproduzidos R1–R5; R6 foi confirmado no diff commitado completo. Um teste CLI novo inicialmente omitiu a opção obrigatória --containment e falhou em argparse; corrigido o comando do teste e repetidas as suítes, sem relaxar a CLI. Os novos testes cobrem limites/ancestrais desconhecidos, aliases tied comprovados, parâmetros ausentes/inesperados/shape/materialização, arquivo especial/crescimento/linha, refs progressivas/circulares/exponenciais, symlinks nas raízes/componentes e whitespace em commits apesar de worktree limpa.

R2 é corrigido **com mocks e headers sintéticos**, não com checkpoint/Torch real. Dimensionamento Qwen3.5 e variantes não implementadas é desconhecido e bloqueia execução. R1 só fornece capacidade para hierarquia v2 completa reconhecida; cgroup v1, raiz virtual/ancestrais ocultos ou ambiente sem identificação devolvem null. Nenhum fallback para RAM total do host. Memória observada não é reserva contra alocações concorrentes.

Para whitespace local sem evento GitHub:

```sh
git diff --check
git diff --check 20f1883ad1671139d7c023eff42b72c6bca96525 HEAD
```

No workflow, o checker examina merge-base..head em pull_request, before..after em push e árvore vazia..head em primeiro push; não usa apenas mudanças não commitadas. SHA final e runs de push/PR ficam na descrição da PR/relatório após consulta remota. Os testes locais não são evidência de CI remota, inferência ou compatibilidade de pesos. Revisão independente continua **NOT PERFORMED**.

## Adaptador Windows — 2026-11-02

Partida: PR #1 integrada por pedido explícito do proprietário em `25ab213de09c65630d35b7bbac529ee1c4104558`; implementação em `codex/windows-memory-adapter`. Ambiente desta execução: Windows real x64, Python 3.11.0, venv local, sem Torch/Transformers. [Observação sanitizada e avaliações das três políticas](evidence/windows-memory-validation.json), [decisão/limites](adr/0004-WINDOWS-MEMORY.md).

| Comando executado no Windows | Resultado |
|---|---|
| `.venv\Scripts\python -m pytest tests/test_windows_memory.py -q` | 34 passed: chamadas simuladas/contratos |
| `.venv\Scripts\python -m pytest tests/test_windows_memory_native.py -q` | 6 passed: Win32 real, filhos/Jobs descartáveis |
| `.venv\Scripts\python -m pytest -q` | 260 passed, 37 skipped |
| `.venv\Scripts\python -m pip check` | Sem dependências quebradas |
| `.venv\Scripts\python -m compileall -q src scripts tests` | PASS |
| `.venv\Scripts\python scripts/verify_repository.py --write-manifest`, depois sem flag | PASS após edições finais; manifesto regenerado, sem pesos/cache/venv |
| `git diff --check` | PASS |

Simulados: RAM abundante/escassa, commit escasso, sem Job, cap por processo, cap agregado com uso desconhecido, erros de cada API/erro 5, dados inconsistentes, conversão de páginas, working set diferente de commit privado, cobertura incompleta da cadeia, três políticas, margens inválidas/configuráveis, alteração de política/margens recusada pelo grant e pelo worker, bloqueio e diferenças supervisor/worker, relatório de memória adulterado e import sem ML/rede. Fixtures de autorização temporárias só para tensores zero minúsculos; nenhum grant real criado.

Nativos: tamanhos/offsets ABI x64, métricas globais e do próprio processo, associação a Job, criação descartável com 256 MiB por processo/384 MiB por Job, leitura do cap, filho cooperativo associado antes da coleta, dois níveis de Jobs de teste, handle aberto sem direito QUERY retornando WinError 5 real, fechamento de handles e consulta do handle fechado retornando WinError 6, helper de preflight do worker em filho real bloqueado em strict antes de importar ML. Não houve alocação até o limite, OOM ou interrupção de processo externo. Filho aguarda stdin; esta sincronização de teste não implementa launcher atômico.

Limitação nativa observada: no host desta sessão, a consulta NULL não expôs o cap do Job de teste recém-associado, mas consulta por handle explícito e `IsProcessInJob` confirmaram o cap/associação. A cadeia não é enumerada; ausência de flags na consulta não prova ausência de outros limites. Cap agregado não tem uso atual medido nesta etapa. Pico nunca vira consumo atual. Best-effort pode permitir preparação com aviso e margem adicional; strict bloqueia a cobertura incompleta, mesmo quando a RAM global é abundante. Balanced bloqueia secundárias críticas ausentes/cap agregado sem consumo atual, mas tolera cadeia parcial com aviso.

Os 37 skips são explícitos: 19 fixtures Linux/mountinfo em paths POSIX; 11 casos de symlink sem privilégio Windows (erro 1314); 5 testes exclusivos de Linux/POSIX (rlimit, namespace, FIFO); 1 socket Unix indisponível nesse ambiente; 1 módulo API Transformers opcional. Os testes Linux continuam no job Ubuntu; não foram executados nativamente nesta sessão Windows. A conta não recebeu elevação nem privilégio de symlink. UTF-8 das fixtures foi explicitado, conexões SQLite passaram a ser fechadas além do commit/rollback, colorama Windows foi pinado.

Primeiro verificador antes de regenerar apontou manifest desatualizado. Investigação dos 110 registros originais encontrou 85 cujo único desvio era CRLF do checkout (`core.autocrlf=true`): normalizar esses bytes para LF reproduziu os hashes originais. `.gitattributes` agora fixa LF para texto e entra no escopo do manifesto; fontes mantidas foram normalizadas antes do hash final. Isso evita manifesto específico do checkout Windows sem esconder corrupção. Conteúdo da marca permanece idêntico ao blob Git original.

A primeira CI do commit `4abd482` passou os testes Ubuntu (289 passed, 7 skipped), mas falhou no manifesto: os bytes/hashes dos 118 blobs estavam corretos, porém `WindowsPath` ordenava nomes sem distinguir caixa e `PosixPath` usava ordem distinta. Reproduzido no Windows com `README.md`, `Z.md`, `a.md`; corrigido o sort para strings relativas POSIX, com regressão automatizada. A suíte local ganhou esse teste (260 passed); contagens da primeira CI são históricas, não resultado do HEAD corrigido.

**NOT-TESTED:** Windows x86/outras versões; ausência real de qualquer Job neste host (caso coberto por mock, sem remover Job herdado); cadeia completa/uso agregado atual; launcher controlado de produção, reserva de memória, ACL do store ou sandbox; API ML opcional nesta venv; inferência/Torch, pesos, qualidade, GPU, treino ou release. Nova job Windows no workflow exercita testes nativos em futuras execuções; resultado remoto não é presumido por este relatório local.

Instaladas somente dependências pequenas do lock de desenvolvimento e pacote local editável; nenhum checkpoint/GGUF/dataset, Torch/CUDA/ROCm ou serviço pago. Nenhuma licença aceita, allowlist alterada, LFM3 habilitado ou trust_remote_code ativado. Qwen3.5 continua bloqueado sem sizing. Revisão pelo principal, sem subagentes ou alegação de revisão independente. Job próprio do supervisor fica como etapa 2 planejada no ADR.

## Etapa 2: launcher Windows controlado — 2026-11-02

PR #3 integrada por pedido do proprietário em `2a3ed22b20e2667814c26319e963b114cf9537df`; branch `codex/windows-controlled-launcher`. Ambiente local: Windows nativo x64 10.0.26200, Python 3.11.0. [ADR-0005](adr/0005-WINDOWS-CONTROLLED-LAUNCHER.md) e [evidência sanitizada](evidence/windows-launcher-validation.json). Nenhuma conclusão abaixo comprova inferência ou sandbox.

| Verificação local executada | Resultado |
|---|---|
| `.venv\Scripts\python -m pytest tests/test_windows_launcher.py -q` | 50 passed, simulados/contratos; inclui 5 cenários de relatório ausente/adulterado/incoerente na supervisão |
| `.venv\Scripts\python -m pytest tests/test_windows_launcher_native.py -q` | 13 passed, Windows real com processos descartáveis; 5 casos injetam erro na chamada Win32 para exercitar cleanup |
| `.venv\Scripts\python -m pytest tests/test_windows_memory_native.py -q` | 6 passed, APIs reais de memória e Jobs da etapa 1 |
| `.venv\Scripts\python -m pytest -q` | 325 passed, 37 skipped |
| `.venv-api\Scripts\python -m pytest -q` com HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE=1 | 333 passed, 36 skipped, TF5.22.1 sem Torch/modelos |
| `python -m pip check`, nas duas venvs | Sem dependências quebradas |
| `.venv\Scripts\python -m compileall -q src scripts tests` | PASS |
| Verificador, `--write-manifest`, verificador novamente | PASS após edições finais, manifesto de fonte sem ambientes/pesos/cache |
| `git diff --check` e diff da base integrada ao HEAD | PASS |

Casos nativos: ABI x64; aplicação/readback de 256 MiB de commit agregado e 16 processos; marcador inexistente enquanto o processo permanece suspenso; associação por handle explícito antes de ResumeThread; processo principal e descendente associados; saída do principal com descendente ainda ativo; supervisão continuada até accounting zero; timeout e interrupção terminando árvore; último handle do Job encerrando pai/filho; criação sob dois Jobs próprios aninhados; whitelist impedindo herança de evento alheio; argumentos com espaços/aspas/backslash/vazio, cwd e ambiente Unicode, stderr/stdout e exit code 7 preservados. Processos abertos para observação pertencem aos próprios testes; não foram usados processos de terceiros ou stress/OOM.

Falhas nativas injetadas de CreateJobObjectW, SetInformationJobObject, CreateProcessW, AssignProcessToJobObject e ResumeThread mantiveram o marcador ausente, sem fallback e com fechamento dos handles/contagem de handles revalidada. São chamadas interceptadas para falhar no Windows real, não alegação de reproduzir toda recusa possível do kernel. Os simulados também cobrem query/wait/exit-code, erro de cleanup e CloseHandle; cleanup não comprovado gera falha, sem falso sucesso. Testes de grants/worker recusam alteração do contrato de contenção; arquivos de recibo forjados não substituem a observação em memória do supervisor.

A evidência pública registra duas novas execuções sem ML: saída natural e timeout, ambas com cap de 268435456 bytes, cinco processos totais contabilizados, zero ativos ao terminar e `cleanup_complete=true`. Pico de commit é métrica de pico; máximo de processos amostrado é nomeado como amostrado. PID/UUID/caminhos temporários e linha de comando de exceções foram omitidos da cópia pública. Relatórios locais do pipeline preservam PID/ID e hashes de request/operação. Não há grant real ou resultado ML nesse artefato.

Desvio técnico documentado: Job sinalizado não equivale a todo esvaziamento normal; a fonte Microsoft só promete sinalização no caso específico do limite de tempo do Job. Assim, usa-se WaitForSingleObject no processo principal e ActiveProcesses no Job para confirmar zero. O teste nativo demonstra que o supervisor espera descendentes e que a limpeza termina a árvore.

Os 37 skips da suíte base conservam os motivos da etapa 1 (Linux/POSIX, symlink sem privilégio e módulo API opcional); a API leve executa esse módulo e mantém 36 skips do SO. Skips não contam como testes passados. CI Windows/Ubuntu/API leve do HEAD final é consultada remotamente e registrada na PR; testes locais não antecipam seu resultado. Linux nativo não foi executado neste PC; regressão Linux ocorre no CI Ubuntu.

No primeiro push de `829fc51`, os testes Ubuntu passaram (341 passed, 20 skipped) e os três jobs da PR passaram, mas o checker de push comparou árvore vazia com toda a branch nova e rejeitou duas quebras Markdown históricas da marca. A marca não foi alterada. O caso foi corrigido para primeiro push de branch de trabalho usar merge-base da branch padrão remota, com ref validada e histórico completo; primeiro push da branch padrão e fixtures sem metadados continuam cobrindo árvore inteira. Regressão prova que whitespace novo na feature ainda falha. A mudança de escopo complementa o registro histórico R6 acima, sem eliminar seu gate para mudanças commitadas. Resultado do HEAD corrigido fica na PR.

**NOT-TESTED:** Windows x86/versões antigas, todas as configurações de Jobs/ACL externas, resistência a administrador/mesma conta/serviços externos, isolamento de arquivos/rede/identidade/VRAM, inferência e uso real de memória dos modelos, reserva/garantia de alocação. Cap próprio não elimina restrições ancestrais; balanced/strict ainda podem bloquear por cobertura/uso agregado desconhecidos. Cleanup tem grace de 5 s para verificar processos já terminados; falha de API/fechamento impede sucesso.

Instaladas apenas dependências do lock de API leve em venv própria ignorada e pacote editável, sem Torch/CUDA/ROCm, checkpoints, datasets ou tokenizers upstream. Sem grant operacional real, licença aceita, LFM3/remote-code habilitado, treino, adapter real, publicação de pesos ou serviço pago. Estado da etapa 1 e sua evidência permanecem acima; etapa 2 não reescreve aprovações passadas. Revisão do principal, sem subagentes/revisão independente.
