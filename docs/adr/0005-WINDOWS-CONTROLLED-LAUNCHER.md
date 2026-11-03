# ADR-0005 — Launcher Windows com Job próprio e criação suspensa

Data: 2026-11-02. Estado: **implementado e exercitado em Windows x64/Python 3.11**, infraestrutura para revisão. Implementa a etapa 2 do [ADR-0004](0004-WINDOWS-MEMORY.md); não autoriza modelos, inferência ou release.

## Contexto e pré-condições

PR #3 integrada por solicitação do proprietário em `2a3ed22b20e2667814c26319e963b114cf9537df`. Branch `codex/windows-controlled-launcher` criada desse merge, com working tree inicialmente limpa; main local alinhada. Windows nativo x64/Python 3.11.0 confirmado. A etapa 1 diagnosticava recursos, mas Windows encerrava só o filho direto. Evidência e limitações históricas daquele diagnóstico são preservadas.

## Decisão e sequência

`windows_launcher.py` controla ciclo de vida, sem consultar memória por conta própria e sem importar ML. Reutiliza apenas tipos/estruturas ABI do adaptador de observação. `containment.supervise` usa esse caminho no Windows; Linux mantém grupo POSIX, RLIMIT e namespace anteriores.

1. Criar Job **sem nome**, manter handle exclusivo no supervisor e limpar explicitamente a flag de herança.
2. Aplicar `KILL_ON_JOB_CLOSE`, limite de 16 processos ativos e cap agregado de commit quando calculável. Ler limites de volta e exigir correspondência.
3. Duplicar saída do log como handle herdável; stdin é NUL. `STARTUPINFOEXW` e `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` permitem somente stdin/stdout compartilhado com stderr. O Job não integra essa lista. Lista de atributos é destruída após criação; todos os handles próprios entram no registro de fechamento.
4. `CreateProcessW` recebe executável absoluto explícito, command line gravável com quoting Windows, ambiente Unicode filtrado e cwd explícito. Flags: `CREATE_SUSPENDED`, `CREATE_UNICODE_ENVIRONMENT`, `EXTENDED_STARTUPINFO_PRESENT`, `CREATE_NO_WINDOW`. Nenhuma flag de breakaway ou alteração de Jobs externos.
5. Associar processo suspenso, confirmar `IsProcessInJob` com handle **explícito do Job próprio**, verificar deadline e só então `ResumeThread`, cujo suspend count anterior precisa ser 1. Falha bloqueia sem fallback para processo desprotegido. Não há `Popen` no launcher nem uso de atributos privados para thread handles.
6. Aguardar saída do processo principal, guardar seu exit code e continuar consultando `ActiveProcesses` até zero. Descendentes permanecem sob o mesmo deadline, mesmo após saída do principal.

## Esvaziamento: ajuste técnico ao pedido

A documentação Microsoft só promete Job sinalizado no caso específico de término pelo limite de tempo do Job; não promete sinalização por qualquer esvaziamento natural. A implementação usa `WaitForSingleObject` no **processo** e consulta `JobObjectBasicAccountingInformation.ActiveProcesses` no **Job** a cada até 20 ms. Não presume que `WaitForSingleObject(job)` sinalize um término natural. Uma saída normal exige processo principal terminado e zero processos ativos no Job. [Fontes primárias](../SOURCES.md).

## Commit e autorização

O plano Windows inclui `containment.windows_launcher`: versão/método, 16 processos, kill-on-close, proibição de breakaway, janela de cleanup de 5 s, regra de commit e teto máximo em bytes. O teto é o envelope já calculado pelo Lab: `elements * dtype_bytes * 3 // 2 + snapshot_bytes + 1 GiB`. Arquitetura desconhecida mantém teto null e continua bloqueada pelo preflight; não há fallback para elementos armazenados em Qwen3.5.

Na execução, `commit_headroom = min(caller_commit_available, system_commit_limit - system_commit_used)`. A margem efetiva da avaliação autorizada reduz esse headroom. O limite seria `min(teto_aprovado, headroom_após_margem)`; headroom insuficiente para o envelope bloqueia antes da criação. Assim, cap aplicado não cresce com mais RAM/commit livre e nunca excede o teto do plano. **RAM física e working set não entram na fórmula de commit.** Faltando evidência adequada de commit, best-effort pode registrar `not-applied` com motivo e manter o diagnóstico anterior; balanced/strict continuam exigindo suas evidências antes do lançamento. Não há reserva nem garantia de alocação.

Alterações de método/limites/fórmula mudam a operação e seu hash/source hash, invalidando planos/grants antigos. O worker compara o contrato de contenção completo com a operação antes de reivindicar o grant. As três políticas e ambas as coletas do worker permanecem. Criar Job próprio não prova a cadeia ancestral completa nem permite enfraquecer balanced/strict; estas políticas ainda podem bloquear no worker se enxergarem cap agregado sem uso atual conhecido.

## Timeout, falhas e handles

Em timeout/interrupção/erro, `TerminateJobObject` atua somente no Job recém-criado, aguarda processo principal e accounting vazio por até 5 s e fecha todos os handles. Se a associação falhou, o processo ainda suspenso é terminado explicitamente por seu handle e reapado; ele não é retomado. Registros criados durante setup são recuperados mesmo se a chamada de setup falhar depois de adquirir um handle. Fechamento em ordem inversa deixa o handle do Job por último. `KILL_ON_JOB_CLOSE` é proteção adicional, não prova de cleanup: falha de terminação, espera/consulta ou fechamento produz `cleanup_complete=false` e falha de execução, nunca sucesso. Não se tenta alterar ou terminar Job externo.

`windows-launcher.json` é escrito pelo supervisor a partir de recibo **em memória**, ligado ao hash do request e da operação. Guarda método, PID, ID local do Job sem nome, flags lidas de volta, limites/motivos, associação/retomada, exit code, contagens, pico de commit (não uso atual), motivo de saída, resultado da terminação e cada fechamento. Supervisor valida recibo e fórmula antes de aceitar resultados; arquivo de recibo forjado pelo worker não substitui o objeto do supervisor. Hash não protege contra administrador/mesma conta que adultere código/host.

## Evidência e limites

[Validação](../VALIDATION.md) separa testes simulados, nativos, API leve e CI. Nativos demonstraram instrução-marcador ausente antes da retomada, associação explícita, descendente associado ao Job, principal encerrado com descendente ainda ativo, espera do esvaziamento, timeout/interrupção da árvore, kill por último handle, whitelist de handles, argumentos/cwd Unicode, logs e exit code. Falhas nas cinco APIs de setup foram injetadas no Windows real para exercitar cleanup sem primeira instrução; não equivalem a todas as possíveis recusas do kernel.

Windows x86, Windows mais antigos, todos os limites de Jobs de terceiros e conteúdo hostil continuam NOT-TESTED. Job não isola arquivos, rede, credenciais, identidade ou VRAM; mesma conta/administrador e criação por serviços externos não são um perímetro de segurança. Nenhum teste envolve processo externo, OOM, pesos, Torch/CUDA/ROCm, inferência, treino ou gasto pago. API leve Transformers é exercitada sem Torch/modelos. Revisão pelo principal, sem delegação ou revisão independente simulada.
