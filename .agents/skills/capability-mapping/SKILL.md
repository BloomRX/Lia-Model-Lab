---
name: capability-mapping
description: Separar pesos, especialistas, runtime, integrações e critérios operacionais.
---

# capability-mapping

## Quando usar e entradas

Cenário, entrada/saída, ambiente e referência de código ou requisito. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [02-LIA-CAPABILITY-MATRIX.md](../../../docs/02-LIA-CAPABILITY-MATRIX.md)
- [03-WEIGHTS-VS-RUNTIME.md](../../../docs/03-WEIGHTS-VS-RUNTIME.md)
- [04-MODEL-FAMILY-ARCHITECTURE.md](../../../docs/04-MODEL-FAMILY-ARCHITECTURE.md)

## Procedimento

1. Classificar A/B/C/D e atribuir owner por estado/ação; memória persistente e autorização nunca pertencem aos pesos.
2. Definir quem solicita, valida, autoriza, executa e devolve o resultado.
3. Mapear dados e benchmark E2E; considerar erro, cancelamento, estado obsoleto e injection.
4. Distinguir capacidade AIRI de requisito e execução real na Lia.

## Saída e ownership

Linha completa de matriz + contrato e casos de falha sugeridos. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Há dataset/runtime/teste para cada resultado prometido; falar sobre uma ação não conta como execução. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Mapeie navegação Minecraft: observação, policy, executor, sucesso no world state.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
