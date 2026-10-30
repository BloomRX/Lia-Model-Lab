# 14 — Orquestração de agentes e subagentes

## Arquivos

- AGENTS.md: regras gerais e limites de autorização.
- .agents/skills/: procedimentos reutilizáveis.
- .codex/agents/*.toml: perfis customizados de Codex.
- .codex/config.example.toml: exemplo opcional, não ativado automaticamente.

Codex documenta skills em .agents/skills e perfis de projeto em .codex/agents. Cada perfil TOML exige name, description e developer_instructions e herda permissões da sessão pai.

A documentação pública do Arena Agent Mode consultada em 30/10/2026 descreve sandbox, Bash, integração GitHub, diff, commit e PR, mas não documenta descoberta automática de skills nem subagentes. Até haver suporte exposto e validado, o agente no Arena deve ler manualmente a skill aplicável e trabalhar em sequência. Nunca simular delegação.

## Perfis

| Perfil | Especialidade |
|---|---|
| model-researcher | Modelos-base, releases, licenças, fontes |
| capability-architect | Decomposição pesos/runtime/serviços |
| dataset-auditor | Proveniência, privacidade, splits |
| training-planner | Fine-tuning e recursos |
| evaluation-reviewer | Benchmarks, holdouts, regressões |
| license-reviewer | Direitos e obrigações |
| brand-reviewer | Padrões comuns da marca Lia |

Não fixamos modelo nem permissão nos perfis; herdam a sessão. Delegue apenas tarefas independentes. Não permita edição concorrente do mesmo arquivo. Comece com 2–4 agentes quando o benefício justificar o custo de tokens.

## Contrato mínimo

Cada tarefa informa objetivo, escopo, fontes/arquivos permitidos, se pode editar (prefira read-only), skill aplicável, formato de entrega, limites de custo/dados e condição de parada. Resultado esperado: resumo, fatos, inferências, desconhecidos, fontes primárias/data, riscos e recomendação.

## Prompt para o agente principal

```text
Divida somente partes independentes e use até 2–4 subagentes especializados disponíveis.
Peça que leiam a skill correspondente e trabalhem em leitura, citando fontes primárias.
Não permita edição concorrente nem delegue downloads grandes, GPU paga, dados pessoais, aceite de licença ou upload.
Aguarde todos os resultados, valide versões e fontes, consolide divergências e só então integre.
Se o host não oferecer subagentes, não simule: trabalhe sequencialmente e informe a limitação.
```

## Configuração opcional

Para Codex, copie .codex/config.example.toml para .codex/config.toml somente depois de decidir habilitar o paralelismo. Sandbox e aprovação continuam na sessão principal; um perfil não cria isolamento.

## Fontes oficiais consultadas em 30/10/2026

- Codex Skills: https://developers.openai.com/codex/skills/
- Codex Subagents: https://developers.openai.com/codex/subagents/
- Codex Configuration: https://developers.openai.com/codex/config-reference/
- Arena Agent Mode: https://help.arena.ai/articles/1655691990-how-to-use-coding-in-agent-mode

Reconfirme a documentação antes de depender de capacidade nova.
