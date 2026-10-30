# 14 — Skills e orquestração sem delegação fictícia

## Suporte observado e limites

Codex documenta skills e perfis TOML com `name`, `description`, `developer_instructions`. Fontes oficiais consultadas em 2026-10-30: [skills](https://developers.openai.com/codex/skills/), [subagents](https://developers.openai.com/codex/subagents/) (redirecionou ao Learn), [config](https://developers.openai.com/codex/config-reference/). Os campos do [exemplo opcional](../.codex/config.example.toml) correspondem à seção `[agents]` consultada; parse TOML é testado, invocação real Codex **NOT-TESTED**. Config não é ativada automaticamente.

A documentação [Arena](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode) consultada descreve terminal/sandbox/GitHub/PR, não garante descoberta de `.agents/skills/` ou execução de `.codex/agents/`. Nesta sessão não há ferramenta real de spawn/wait de subagentes exposta. O principal executou as atividades sequencialmente, com consultas de fonte em paralelo; **não houve subagentes nem revisão independente simulada**.

## Registro e divisão de responsabilidades

| Skill | Revisor read-only por instrução | Escopo de saída; principal integra |
|---|---|---|
| model-candidate-research | model-researcher | Fatos de checkpoint e comparação, não aprovação de base |
| capability-mapping | capability-architect | Responsabilidades A/B/C/D e testes E2E |
| dataset-governance | dataset-auditor | Origem/direitos/privacidade/splits; não coleta dados |
| finetuning-plan | training-planner | Hparams/budget/probes de treino; não inicia jobs |
| experiment-reproducibility | training-planner | Integridade/retomada; separado do desenho de treino |
| model-evaluation | evaluation-reviewer | Comparabilidade/holdout/regressões; não altera resultados |
| model-license-release-review | license-reviewer | Obrigações por artefato; não aceita termos nem publica |
| multi-agent-orchestration | principal | Disponibilidade real, ownership, síntese e conflitos |
| lia-brand-consistency-review | brand-reviewer | Nome/limites/identidade e alegações; não redefine marca |

As nove skills não são nove agentes adicionais. Planejamento de treino difere de reprodutibilidade; coleta de licença na pesquisa difere do gate de direitos de cada artefato no release. Mantidas por terem saídas e condições de conclusão diferentes, sem multiplicar estruturas redundantes.

## Contrato de delegação

Antes de delegar, principal define objetivo, entradas/fontes autorizadas, skill, estado de evidência esperado, formato de saída, budget/custo, condição de parada e arquivos de escrita exclusivos (padrão: nenhum). Revisores não editam arquivos. README, AGENTS, configs, SOURCES, manifest e documentos compartilhados ficam com o principal. Se nova ferramenta oferecer subagentes, não assumir que perfis do disco foram carregados: verificar invocação e retorno reais; limitar concorrência conforme a necessidade/custo, não iniciar sete por padrão.

Saída obrigatória: achado, arquivo/linha ou fonte/data/revision, classificação fato/hipótese/desconhecido, risco, sugestão e validação executada/NOT-TESTED. Principal confere fontes e semântica antes de integrar. Instruções read-only **não** criam isolamento nem substituem sandbox/permissões herdadas. Subagentes nunca aprovam compute, dados privados, download grande, upload, termos ou publicação.

## Fallback sequencial reproduzível

1. Ler AGENTS e índice de skills manualmente.
2. Selecionar skill por tarefa e seguir entradas/procedimento/critério.
3. Marcar papel assumido pelo principal, sem dizer “o revisor aprovou”.
4. Executar checks locais autorizados e registrar outputs, limitações e arquivos.
5. Principal consolida e abre/atualiza PR, sem merge automático.

## Checks locais

`python scripts/verify_repository.py` faz parse real de frontmatter YAML/TOML, confere nove skills, sete perfis, seções mínimas, identidade e caminhos explícitos de skill em cada perfil. Testes de software não comprovam comportamento de um agente em outro host. [Índice de skills](../.agents/skills/README.md) e [fundação técnica](15-IMPLEMENTATION-FOUNDATION.md).
