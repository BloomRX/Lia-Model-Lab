---
name: experiment-reproducibility
description: Verificar identidade, hashes, ambientes e retomada sem executar workloads.
---

# experiment-reproducibility

## Quando usar e entradas

Plano/config, manifest de dados, record e artefatos locais autorizados. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [13-GOVERNANCA-DE-EXPERIMENTOS.md](../../../docs/13-GOVERNANCA-DE-EXPERIMENTOS.md)
- [15-IMPLEMENTATION-FOUNDATION.md](../../../docs/15-IMPLEMENTATION-FOUNDATION.md)

## Procedimento

1. Verificar revisions imutáveis, dataset/code/config hashes, seed, dependências exatas e ambiente observado versus planejado.
2. Garantir pesquisa e armazenamento aprovado disjuntos; CLI exige ambos explicitamente.
3. Registrar plano sem sobrescrever ID; duração/custo reais permanecem null até execução comprovada.
4. verify-resume verifica adapter/optimizer/scheduler/RNG e compatibilidade config/dados; não retoma treino.

## Saída e ownership

Relatório de integridade e retomabilidade com comandos, discrepâncias e bloqueios. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Todos os artefatos acessíveis conferem por hash; não inventar valores de artifacts indisponíveis. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Confira um checkpoint manifesto alterado: deve bloquear, não tentar continuar.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
