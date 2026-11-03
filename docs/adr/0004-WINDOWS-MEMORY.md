# ADR-0004 — Diagnóstico de memória Windows por política

Data: 2026-11-02. Estado: **implementado para revisão**, com testes simulados e APIs Windows reais; sem execução de modelo. Continuidade do [ADR-0003](0003-INFERENCE-HARDENING.md), sem substituir autorização externa.

## Contexto

O proprietário solicitou integrar a PR #1 e implementar diagnóstico Windows útil. Merge confirmado em `25ab213de09c65630d35b7bbac529ee1c4104558`; branch desta implementação criada desse commit. RAM desconhecida para todo Windows impedia preparar o piloto. Disponibilidade global, commit e restrições de processos/Jobs precisam ser avaliados separadamente.

## Decisão

- `windows_memory` consulta Win32 por ctypes, com tipos fixos/pointer-sized, alinhamento nativo, assinaturas e erros Win32. Sem `_pack_`, ML, ferramentas externas, alteração de Jobs ou rede ao importar. Pseudo handle do processo não é fechado; handle opcional de Job é emprestado, com associação verificada e fechamento pelo chamador.
- `memory_resources.observe/assess/compare` separa observação, decisão e diferenças. Linux conserva a descoberta completa cgroup-v2 e seu orçamento anterior, sem fallback para RAM do host; as novas margens aplicam-se ao Windows.
- Windows usa mínimo das disponibilidades calculáveis de RAM física, commit do chamador, commit global e headroom por processo. `PrivateUsage` só é subtraído do limite por processo; nunca de `ullAvailPageFile`. Working set não substitui commit privado. Limite agregado sem uso atual é um teto separado, não headroom inventado. Pico não é consumo atual.
- `best-effort` é padrão: margens 10% + 10 pontos percentuais quando existe incerteza secundária. `balanced` usa 20% + adicional, exige commit global, commit privado, associação e limites do Job consultado; uso agregado desconhecido bloqueia se houver cap agregado. Cobertura parcial da cadeia continua como aviso. `strict` usa 30% + adicional e bloqueia qualquer restrição exigida desconhecida, incluindo cadeia não enumerada. RAM física/commit do chamador desconhecidos, observações inconsistentes e orçamento excedido bloqueiam em todas.
- Percentuais inteiros configuráveis, soma máxima 90; adicional aplicado uma vez, sem percentual fictício de confiança. Margem reduz capacidade observada: `usable = floor(min(headrooms) * (100-margin)/100)`. Tetos conhecidos também precisam comportar orçamento e margem. Não há reserva nem garantia de alocação.
- Política e ambas as margens normalizadas entram nos argumentos e na operação exata autorizada. Plano antigo exige regeneração; trocar política/margens exige novo grant humano. Gate de licença, hashes e arquitetura permanece. Qwen3.5 continua sem sizing e bloqueado.
- Supervisor registra observação/avaliação; worker mede depois de aplicar contenção, antes de importar runtime e novamente imediatamente antes dos pesos. Relatório separado inclui hash do request; supervisor reavalia seu conteúdo, registra diferenças e recusa sucesso sem relatório válido. Observação falha do worker é preservada, sem promover inferência inexistente.

## Jobs: evidência e limites

`IsProcessInJob(NULL job)` identifica associação. A documentação Microsoft descreve `QueryInformationJobObject(NULL)` como consulta ao Job imediato; isso não enumera a cadeia. Neste host, filho associado ao Job descartável tinha associação confirmada por handle explícito e limite 256 MiB, mas a consulta NULL retornou flags `12288` de um Job herdado, sem esse cap. O teste registra cobertura parcial, sem presumir que o Job consultado seja a única restrição aplicável. Handle explícito conhecido lê o cap e também não comprova a cadeia inteira. `best-effort` aceita essa incerteza com aviso; `strict` bloqueia.

Não usamos classes não documentadas para consumo agregado, nem soma de working sets, nem pico. Limites ancestrais não desaparecem ao criar outro Job. Esta etapa entrega diagnóstico, não launcher nem sandbox. [Fontes Microsoft](../SOURCES.md) e [validação](../VALIDATION.md).

## Segunda etapa: launcher controlado (PLANEJADO)

Exige desenho separado: criar Job próprio, limites em bytes vinculados ao plano, handle não herdável mantido pelo supervisor, criação suspensa ou lista de Jobs em atributos de criação, associação antes de executar Python/pesos, retomada só após sucesso e cleanup em todos os erros/deadlines. Não usar janela de associação posterior do teste cooperativo como contenção de produção. Considerar Jobs herdados, recusa sem fallback, callbacks/completion port, accounting final, morte da árvore e handles. Não alterar Jobs externos ou remover restrições herdadas. Testes desta etapa usam filhos cooperativos aguardando stdin, sem alegação de launcher atômico.

## Limites de evidência

Windows x64/Python 3.11 com filhos descartáveis e fixtures minúsculas; sem OOM ou pesos reais. x86, outras versões Windows, launcher/ACL do store e execução ML permanecem NOT-TESTED. SQLite agora fecha conexões explicitamente para liberar handles Windows; fixtures UTF-8 e skips por capacidade do SO não alteram gates do produto. Revisão feita pelo principal, sem delegação ou revisão independente simulada.

## Atualização da etapa 2 — 2026-11-02

O planejamento e os limites acima registram a etapa 1. A etapa 2 foi implementada e testada com APIs Windows reais no [ADR-0005](0005-WINDOWS-CONTROLLED-LAUNCHER.md): criação suspensa, associação explícita antes de retomar, Job próprio sem herança de handle, controle de descendentes, limites e cleanup confirmado. Estado atual e contagens em [VALIDATION](../VALIDATION.md). A limitação histórica de consulta NULL e a falta de enumeração completa da cadeia continuam válidas; não há aprovação de inferência nem sandbox.
