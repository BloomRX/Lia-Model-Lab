---
name: dataset-governance
description: Auditar direitos, privacidade, schema e isolamento dos dados.
---

# dataset-governance

## Quando usar e entradas

Metadados autorizados, card e manifest; não amostras privadas. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [07-DATASET-STRATEGY.md](../../../docs/07-DATASET-STRATEGY.md)
- [13-GOVERNANCA-DE-EXPERIMENTOS.md](../../../docs/13-GOVERNANCA-DE-EXPERIMENTOS.md)
- [15-IMPLEMENTATION-FOUNDATION.md](../../../docs/15-IMPLEMENTATION-FOUNDATION.md)

## Procedimento

1. Registrar origem, revision, licença, revisão de direitos, sintético/gerador, finalidade e restrições.
2. Bloquear PENDING, PII não autorizada, biometria sem consentimento, origem desconhecida. Revisão humana é gate separado do schema.
3. Validar JSONL e comparar fingerprints/grupos; separar fonte/conversa/pessoa/mundo antes do split.
4. Usar validate-data e verify-data apenas nos arquivos autorizados; documentar limites do dedup exato.

## Saída e ownership

Card com riscos/pendências, comandos executados e relatório por split. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Manifest hashes conferem, grupos não vazam, consent_ref quando necessário; desconhecido não vira autorização. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Audite tests/fixtures/pilot.jsonl como fixture fictícia, não dataset de produção.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
