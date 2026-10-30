# Lia Model Lab

**Documentação fundadora — v1.0 — 30 de outubro de 2026**  
**Idioma:** português brasileiro  
**Objetivo:** criar e evoluir modelos/pesos próprios para o ecossistema Lia.

> **Em uma frase:** o Lia Model Lab é o laboratório independente responsável por pesquisar, adaptar, treinar, avaliar, versionar e empacotar a família de modelos da Lia — começando pelo **Lia Core** e evoluindo, com evidência, para capacidades multimodais, agentes e especializações.

## Estado desta documentação

- Visão e arquitetura: **documentadas**.
- Padrão comum de marca e vocabulário: `docs/BRAND-STANDARDS.md`.
- Governança de experimentos e artefatos: `docs/13-GOVERNANCA-DE-EXPERIMENTOS.md`.
- Catálogo de capacidades AIRI: **levantamento documental** baseado no manual oficial AIRI 0.13.0 e na estrutura do fork existente dentro de `Lia-Project`.
- Capacidades/modelos que precisam de pesos: **mapeadas** na matriz.
- Modelo-base: **não escolhido definitivamente**.
- Treinamento: **plano aprovado conceitualmente**; nenhum treinamento foi executado por este pacote.
- Datasets: **a construir e licenciar**.
- Infraestrutura de treinamento: **a validar**.
- Pesos próprios: **ainda não existem neste pacote**.

Este repositório contém documentação, políticas e templates. Não contém datasets privados, checkpoints ou pesos de modelos.

## Agentes e skills

- AGENTS.md define os limites e o fluxo.
- .agents/skills/ contém procedimentos especializados.
- .codex/agents/ contém perfis de subagentes Codex.
- docs/14-ORQUESTRACAO-DE-AGENTES.md explica delegação, compatibilidade com Arena e limites.

## Comece por aqui

1. `AGENTS.md` — regras para Arena.ai Agent Mode e outros agentes.
2. `docs/BRAND-STANDARDS.md` — identidade, linguagem, limites entre produtos e vocabulário comum.
3. `docs/00-VISAO-E-ESCOPO.md` — missão, limites e princípio de arquitetura.
4. `docs/01-CATALOGO-CAPACIDADES-AIRI.md` — inventário das funções AIRI que servem como referência.
5. `docs/02-MATRIZ-CAPACIDADES-MODELO-RUNTIME.md` — o que deve ser aprendido nos pesos e o que precisa existir fora deles.
6. `docs/03-ARQUITETURA-ALVO.md` — família de modelos e runtime ao redor.
7. `docs/04-SELECAO-MODELO-BASE.md` — shortlist e gates de decisão.
8. `docs/05-PLANO-DE-TREINAMENTO.md` — LoRA, QLoRA, SFT, avaliações e exportação.
9. `docs/06-DATASETS-E-GOVERNANCA.md` — dados, consentimento, licenças e privacidade.
10. `docs/07-AVALIACAO-E-GATES.md` — como provar que um modelo melhorou.
11. `docs/08-INFRAESTRUTURA-E-OPERACAO.md` — hardware, execução remota, Arena e artefatos.
12. `docs/09-ROADMAP.md` — fases de implementação.
13. `docs/10-DECISOES-REGISTRADAS.md` — decisões iniciais e pontos ainda abertos.
14. `docs/13-GOVERNANCA-DE-EXPERIMENTOS.md` — proveniência, custo, reprodutibilidade e ciclo de promoção de artefatos.
15. `docs/14-ORQUESTRACAO-DE-AGENTES.md` — perfis, skills e delegação segura.

## Relação com os repositórios existentes

- `BloomRX/Lia-Project` é a aplicação principal/companheira virtual e está em processo de desacoplamento. AIRI é uma referência técnica e fonte de comparação, não uma dependência arquitetural permanente desejada.
- `BloomRX/Lia-Model-Lab` é o laboratório independente de pesos, datasets, treinamento e avaliação. Ele produz artefatos que podem ser integrados à aplicação por contratos documentados; não assume memória, ferramentas, permissões ou UI.
- `BloomRX/LiaVoiceStudio`, `BloomRX/Lia-Studio`, `BloomRX/Lia-Go` e `BloomRX/Lia-Forge` são projetos relacionados, mas mantêm escopos e ciclos próprios. Consulte seus repositórios para estado real e não presuma integração só por compartilharem a marca.

O blueprint original `docs/Lia_Model_Blueprint.md` foi preservado como referência e complementa a documentação numerada.

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
│   ├── 11-FONTES-E-EVIDENCIAS.md
│   ├── BRAND-STANDARDS.md
│   └── 13-GOVERNANCA-DE-EXPERIMENTOS.md
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
