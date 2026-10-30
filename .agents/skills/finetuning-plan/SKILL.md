---
name: finetuning-plan
description: Planejar SFT LoRA/QLoRA sem executar treinamento.
---

# finetuning-plan

## Quando usar e entradas

Base revision, dataset manifest, hparams, backend/hardware e limite de custo. Se faltarem metadados, registrar BLOCKED/UNKNOWN, sem completar com suposições.

## Leituras

- [06-TRAINING-STRATEGY.md](../../../docs/06-TRAINING-STRATEGY.md)
- [08-HARDWARE-INFRASTRUCTURE.md](../../../docs/08-HARDWARE-INFRASTRUCTURE.md)
- [15-IMPLEMENTATION-FOUNDATION.md](../../../docs/15-IMPLEMENTATION-FOUNDATION.md)

## Procedimento

1. Exigir baseline e objetivo mensurável, módulos alvo inspecionados, tokenizer/template/hashes.
2. Comparar LoRA BF16 e QLoRA NF4; planejar save/retomada e probe de kernels, não declarar suporte por família.
3. Preencher configs/sft-pilot.template.yaml com valores reais somente quando conhecidos; placeholders devem falhar no registro.
4. Definir budget/stop; Vulkan não é backend de treino validado aqui. Não iniciar job por haver configuração.

## Saída e ownership

Plano não executado com custo/alternativas, gates e validação de config quando completa. Em subagente: somente leitura e retorno ao principal; não editar arquivos compartilhados. No fallback sequencial, o principal assume esta skill explicitamente, sem alegar revisão independente.

## Critério de conclusão

Status planned explícito, custos assumidos, provas faltantes listadas; nenhum treino, aceite ou download. Separar decisão aprovada, proposta, hipótese, plano, execução e resultado testado. Citar fonte/data/versão e comando realmente executado; caso contrário NOT-TESTED.

## Exemplo de tarefa

> Planeje SFT de persona em 4B; cite o que ainda impede o primeiro job.

## Limites

Sem GPU/API paga, download grande, treino longo, dados pessoais, aceite de termos, upload ou publicação. Não apagar/modificar artefatos do usuário. Ferramentas executam só no escopo autorizado; esta skill não concede permissões.
