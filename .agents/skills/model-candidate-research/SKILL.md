---
name: model-candidate-research
description: Comparar checkpoints abertos com fontes primárias e recomendação condicional.
---

# model-candidate-research

## Quando usar e entradas

Lista de checkpoints exatos, tarefa Lia, teto de memória/custo e modalidades. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [05-FOUNDATION-MODEL-COMPARISON.md](../../../docs/05-FOUNDATION-MODEL-COMPARISON.md)
- [SOURCES.md](../../../docs/SOURCES.md)

- [16-REAL-INFERENCE-PILOT.md](../../../docs/16-REAL-INFERENCE-PILOT.md)

## Procedimento

1. Conferir card/README/LICENSE oficiais; registrar URL, revision e data; separar parâmetros totais, ativos e footprint residente.
2. Comparar pt-BR, reasoning/tools, SFT/LoRA/QLoRA, processor/template e engines; DOCUMENTED não é teste local.
3. Estimar separadamente pesos, cache, ativações e optimizer. Não converter 4-bit teórico em VRAM garantida.
4. Propor candidato econômico, alternativa e motivos de exclusão; marcar revisions/probes desconhecidos.

## Saída e ownership

Tabela por candidato com fonte/data/estado, riscos e recomendação; não alterar a adoção da base. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Todos os critérios comparados ou UNKNOWN justificado; nenhuma modalidade herdada só do nome da família. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Compare Qwen3.5-4B e Qwen3.8-27B para piloto 2K/microbatch 1, sem baixar pesos.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
