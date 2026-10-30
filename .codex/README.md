# Perfis opcionais Codex

Sete perfis em `agents/*.toml`, com nome/descrição/instruções e skills explícitas. Sintaxe/referências verificadas localmente; execução real no Codex **NOT-TESTED**. Não há garantia de descoberta no Arena. `config.example.toml` é exemplo, não configuração ativa; copiar somente após revisar host/versão/custo. Não versionar configurações locais com segredos.

Todos os perfis são read-only por instrução, herdam permissões do principal e não criam sandbox. [Contrato e tabela de ownership](../docs/14-ORQUESTRACAO-DE-AGENTES.md); [skills](../.agents/skills/README.md). Sem subagentes disponíveis: leitura manual e execução sequencial pelo principal.
