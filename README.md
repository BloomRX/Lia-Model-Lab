# Lia Model Lab

Laboratório independente para pesquisar, adaptar, avaliar e distribuir a família de modelos da **Lia**: uma personagem multimodal com identidade, memória externa, voz, corpo virtual e capacidade de agir — não apenas um chatbot personalizado.

## Estado — Missão 001 / Fase 0 (30/10/2026)

- Auditoria documental e pesquisa estática de código AIRI **v0.13.0**, com referência **v0.12.0-beta.5** e snapshot separado do Lia Project.
- Matriz de capacidades com separação entre **pesos, especialistas, runtime e sistemas híbridos**.
- Arquitetura progressiva Core/Vision/Voice/Speech/Agent/Game/Memory/Omni e três velocidades cognitivas **propostas para revisão**.
- Modelo-base **não escolhido**; rankings são ordem de avaliação, não resultados de benchmark.
- **Nenhum treino, pesos próprios, dataset de produção, serviço pago ou runtime alterado nesta missão.**
- Compatibilidade de treino/export, hardware atual do proprietário, licenças específicas de especialistas e benchmarks permanecem gates abertos.

## Comece por aqui

1. [AGENTS.md](AGENTS.md) — políticas de execução, dados, evidência e aprovação.
2. [Índice navegável completo](docs/README.md) — documentos da missão, v1.0, blueprint e templates.
3. [00 — Auditoria do projeto](docs/research/00-PROJECT-AUDIT.md) — contradições e estado verificado.
4. [01 — Inventário técnico AIRI](docs/research/01-AIRI-CAPABILITY-INVENTORY.md) — referências de código por commit.
5. [02 — Matriz de capacidades Lia](docs/research/02-LIA-CAPABILITY-MATRIX.md).
6. [03 — Pesos versus runtime](docs/architecture/03-WEIGHTS-VS-RUNTIME.md).
7. [04 — Arquitetura da família](docs/architecture/04-MODEL-FAMILY-ARCHITECTURE.md).
8. [05 — Comparação de modelos](docs/model-selection/05-FOUNDATION-MODEL-COMPARISON.md).
9. [06 — Treinamento](docs/research/06-TRAINING-STRATEGY.md), [07 — Dados](docs/research/07-DATASET-STRATEGY.md) e [09 — Benchmarks](docs/research/09-BENCHMARK-STRATEGY.md).
10. [08 — Hardware](docs/research/08-HARDWARE-INFRASTRUCTURE.md), [10 — Arena workflow](docs/research/10-ARENA-AGENT-WORKFLOW.md), [11 — Roadmap](docs/research/11-ROADMAP.md), [12 — Decisões abertas](docs/research/12-OPEN-DECISIONS.md).
11. [Fontes e limites da pesquisa](docs/research/SOURCES.md).

## Autoridade, histórico e independência

O [blueprint original](docs/Lia_Model_Blueprint.md) está **preservado integralmente**. A [v1.0](docs/00-VISAO-E-ESCOPO.md) e suas [decisões](docs/10-DECISOES-REGISTRADAS.md) continuam disponíveis. A missão acrescenta evidências e correções datadas; não transforma hipóteses em decisões aprovadas. Em especial, o card atual do Gemma 4 declara Apache 2.0; as referências anteriores a termos próprios foram corrigidas explicitamente.

A documentação do Lab é a autoridade interna. **AIRI é referência técnica, não dependência arquitetural obrigatória**. Funcionalidades encontradas no AIRI não são automaticamente funcionalidades implementadas/validadas na Lia. A documentação nova distingue `DOCUMENTED`, `CODE-PRESENT`, `EXPERIMENTAL` e `NOT-TESTED`; nenhum teste de runtime upstream foi executado nesta missão.

## Caminho recomendado (pendente de aprovação)

Contratos e mocks → licença/hardware/compatibilidade → benchmark da base → dados curados → SFT LoRA/QLoRA → adapter → merge opcional → quantização → regressão → publicação autorizada.

Piloto econômico: estudar Qwen3.5-0.8B para conformance e 4B como Core candidato. Avaliação remota de qualidade: Qwen3.8-27B, controle Qwen3.5-27B e alternativas Gemma 4. Voz, memória e jogo têm especialistas e testes próprios; não são “cobertos” por uma boa resposta textual.

## Limites operacionais

- Sem treinamento do zero na primeira geração; sem pesos/dados brutos no Git.
- Sem memória pessoal mutável ou segredos nos pesos.
- Sem dados privados, voz ou conversas de terceiros sem autorização específica.
- Sem GPU/API paga, grande download ou publicação de artefatos sem aprovação.
- Git versiona docs, código, configs, cards, manifests e métricas pequenas. Artefatos de ML exigem armazenamento aprovado, proveniência e checksums.

Este repositório é o laboratório de modelos; não modifica nem substitui o runtime da aplicação Lia. O próximo passo é revisar os gates e as [cinco tarefas recomendadas](docs/research/11-ROADMAP.md).
