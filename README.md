# Lia Model Lab

**Documentação fundadora — v1.0 — 30 de outubro de 2026**  
**Idioma:** português brasileiro  
**Objetivo:** criar e evoluir modelos/pesos próprios para o ecossistema Lia.

> **Em uma frase:** o Lia Model Lab é o laboratório independente responsável por pesquisar, adaptar, treinar, avaliar, versionar e empacotar a família de modelos da Lia — começando pelo **Lia Core** e evoluindo, com evidência, para capacidades multimodais, agentes e especializações.

## Estado desta documentação

- Visão e arquitetura: **documentadas**.
- Catálogo de capacidades AIRI: **levantamento documental** baseado no manual oficial AIRI 0.13.0 e na estrutura do fork existente dentro de `Lia-Project`.
- Capacidades/modelos que precisam de pesos: **mapeadas** na matriz.
- Modelo-base: **não escolhido definitivamente**.
- Treinamento: **plano aprovado conceitualmente**; nenhum treinamento foi executado por este pacote.
- Datasets: **a construir e licenciar**.
- Infraestrutura de treinamento: **a validar**.
- Pesos próprios: **ainda não existem neste pacote**.

Este ZIP contém documentação, políticas e templates. Não contém código de treinamento, datasets, checkpoints ou pesos de modelos.

## Comece por aqui

1. `AGENTS.md` — regras para Arena.ai Agent Mode e outros agentes.
2. `docs/00-VISAO-E-ESCOPO.md` — missão, limites e princípio de arquitetura.
3. `docs/01-CATALOGO-CAPACIDADES-AIRI.md` — inventário das funções AIRI que servem como referência.
4. `docs/02-MATRIZ-CAPACIDADES-MODELO-RUNTIME.md` — o que deve ser aprendido nos pesos e o que precisa existir fora deles.
5. `docs/03-ARQUITETURA-ALVO.md` — família de modelos e runtime ao redor.
6. `docs/04-SELECAO-MODELO-BASE.md` — shortlist e gates de decisão.
7. `docs/05-PLANO-DE-TREINAMENTO.md` — LoRA, QLoRA, SFT, avaliações e exportação.
8. `docs/06-DATASETS-E-GOVERNANCA.md` — dados, consentimento, licenças e privacidade.
9. `docs/07-AVALIACAO-E-GATES.md` — como provar que um modelo melhorou.
10. `docs/08-INFRAESTRUTURA-E-OPERACAO.md` — hardware, execução remota, Arena e artefatos.
11. `docs/09-ROADMAP.md` — fases de implementação.
12. `docs/10-DECISOES-REGISTRADAS.md` — decisões iniciais e pontos ainda abertos.

## Relação com os repositórios existentes

A inspeção de 30/10/2026 encontrou:

- `BloomRX/Lia-Project`: aplicação principal. A branch de trabalho consultada foi `arena/01a10290-lia-project`, HEAD `eb38005d4c63a584d1fae345e82ff9a4bb8ef7a2`.
- `BloomRX/Lia-Model-Lab`: **o repositório já existe no GitHub**. A branch `main` tinha apenas `README.md` (`# Lia-Omni`) e `docs/Lia_Model_Blueprint.md` no inventário consultado. Este pacote evolui essa documentação sem apagar a ideia original.
- `moeru-ai/airi`: referência técnica externa. A regra de produto registrada em `Lia-Project/AGENTS.md` é que Lia seja independente; AIRI não é a arquitetura final nem uma dependência permanente.

**Não foi feita nenhuma alteração, commit ou push em nenhum repositório.** O ZIP é o pacote para você revisar e incorporar ao `BloomRX/Lia-Model-Lab`.

## Estrutura

```text
Lia-Model-Lab/
├── README.md
├── AGENTS.md
├── .gitignore
├── configs/
│   ├── model-candidates.yaml
│   └── capability-requirements.yaml
├── docs/
│   ├── 00-VISAO-E-ESCOPO.md
│   ├── 01-CATALOGO-CAPACIDADES-AIRI.md
│   ├── 02-MATRIZ-CAPACIDADES-MODELO-RUNTIME.md
│   ├── 03-ARQUITETURA-ALVO.md
│   ├── 04-SELECAO-MODELO-BASE.md
│   ├── 05-PLANO-DE-TREINAMENTO.md
│   ├── 06-DATASETS-E-GOVERNANCA.md
│   ├── 07-AVALIACAO-E-GATES.md
│   ├── 08-INFRAESTRUTURA-E-OPERACAO.md
│   ├── 09-ROADMAP.md
│   ├── 10-DECISOES-REGISTRADAS.md
│   └── 11-FONTES-E-EVIDENCIAS.md
└── templates/
    ├── ADR.md
    ├── DATASET-CARD.md
    ├── EXPERIMENTO.md
    ├── MODEL-CARD.md
    └── AVALIACAO.md
```

## Princípios inegociáveis

- Não treinar um foundation model do zero na primeira geração.
- Não escolher o modelo-base apenas por número de parâmetros ou benchmark público.
- Não colocar memória pessoal, segredos, ferramentas ou estado mutável dentro dos pesos.
- Não confundir “o modelo sabe solicitar uma ação” com “a aplicação executou a ação com segurança”.
- Não declarar uma capacidade concluída sem teste direcionado e evidência reproduzível.
- Não publicar pesos/adapters derivados de modelos sem revisar a licença da base e dos dados.
- Não iniciar download grande, treinamento pago, inferência paga, upload público ou uso de credenciais sem autorização explícita.
- Preservar uma referência reproduzível para cada experimento: base, commit, dados, configuração, seed, métricas e hashes.
