---
name: multi-agent-orchestration
description: Coordenar revisões independentes com fallback sequencial real.
---

# multi-agent-orchestration

## Quando usar e entradas

Tarefa, capacidades expostas pelo host, arquivos e custo/token budget. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [14-ORQUESTRACAO-DE-AGENTES.md](../../../docs/14-ORQUESTRACAO-DE-AGENTES.md)
- [15-IMPLEMENTATION-FOUNDATION.md](../../../docs/15-IMPLEMENTATION-FOUNDATION.md)

## Procedimento

1. Verificar se há ferramenta real de spawn/wait; não inferir suporte da existência de perfis TOML.
2. Se ausente, ler skills manualmente e trabalhar em sequência; relatar sem delegação, sem revisores simulados.
3. Delegar preferencialmente leitura; cada contrato tem objetivo, fontes, ownership exclusivo, saída, stop e limites.
4. Agente principal valida fontes/conflitos e edita arquivos compartilhados; não autorizar GPU/download/upload por delegação.

## Saída e ownership

Plano de ownership e síntese com fatos/hipóteses/desconhecidos atribuídos a evidências reais. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Sem escrita sobreposta; todas as tarefas devolvidas/encerradas ou bloqueadas explicitamente. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Pesquisador e licenças leem fontes; somente principal altera comparação e SOURCES.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
