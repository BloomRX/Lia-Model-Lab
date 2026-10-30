---
name: model-license-release-review
description: Revisar direitos por artefato sem aceitar termos ou publicar.
---

# model-license-release-review

## Quando usar e entradas

Cards, LICENSE/NOTICE por revision, linhagem e manifest de export. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [13-GOVERNANCA-DE-EXPERIMENTOS.md](../../../docs/13-GOVERNANCA-DE-EXPERIMENTOS.md)
- [BRAND-STANDARDS.md](../../../docs/BRAND-STANDARDS.md)
- [15-IMPLEMENTATION-FOUNDATION.md](../../../docs/15-IMPLEMENTATION-FOUNDATION.md)

## Procedimento

1. Separar código, base, adapter, merge, quantização, dados, voz, assets e marca.
2. Checar treino/uso comercial/redistribuição/atribuição; revalidar termos da versão exata, não só metadata de família.
3. Inspecionar adapter local e hashes; integridade estrutural não prova equivalência de inferência ou direito de publicação.
4. Registrar blockers e pedir revisão responsável quando houver ambiguidade; nunca aceitar termos em nome do usuário.

## Saída e ownership

Matriz artefato→direitos/obrigações/evidências/bloqueios. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Nenhum UNKNOWN aprovado; export é local, sem upload nem release automático. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Revise adapter LoRA e notices; não confunda Apache da base com direitos da personagem.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
