---
name: model-evaluation
description: Comparar base, adapter e quantização sem ocultar regressões.
---

# model-evaluation

## Quando usar e entradas

Protocolo selado, predições com origem e variantes pareadas. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [09-BENCHMARK-STRATEGY.md](../../../docs/09-BENCHMARK-STRATEGY.md)
- [15-IMPLEMENTATION-FOUNDATION.md](../../../docs/15-IMPLEMENTATION-FOUNDATION.md)

## Procedimento

1. Verificar IDs, gabarito, test hash, base revision e protocolo idênticos; diferenças de ambiente devem ser relatadas.
2. Rodar compare só sobre predições autorizadas; exact match não avalia persona nem executa inferência.
3. Reportar métricas por capability e regressões; LLM judge não substitui rubrica humana.
4. Distinguir fixture de resultado real; não ajustar no holdout nem promover release pela média.

## Saída e ownership

Tabela por capacidade/variante, falhas e limitações, comandos e evidência. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Base e adapter presentes; quantizado quando alegado; sem IDs faltantes/duplicados ou test usado em tuning. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Compare fixtures base/adapter/adapter-quantized; explique por que isso não prova qualidade Lia.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
