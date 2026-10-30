# Lia Model Lab

Laboratório independente para construir e avaliar os primeiros pesos/adapters **Lia Core**, com evolução progressiva para percepção, fala, agentes e jogos. Não é um chatbot renomeado nem o runtime da aplicação Lia.

## Estado — fundação e piloto de inferência, 30/10/2026

Pesquisa e skills integradas em uma única documentação oficial; marca e governança preservadas. Já há **código offline funcional e testes** para Dataset Factory texto/tools, splits/dedup, integridade, planos reproduzíveis, avaliação de predições e exportação estrutural local de adapters.

**Hardening v0.4:** autorização operacional externa/temporária/uso único, classes Qwen explícitas, processor VLM, métricas v2 e máscaras validadas por turno. API real TF5.22.1 executada apenas com tokenizer original de teste e sem Torch. Perfis Linux de recursos/namespace não são sandbox completo. [Piloto, comandos e gates](docs/16-REAL-INFERENCE-PILOT.md). PR #1 continua aberta; este trabalho não está presumido integrado à main.

**Ainda não existe modelo adaptado Lia validado.** Não houve download de checkpoints/datasets grandes, treino, inferência real, GPU/API paga, uso de dados pessoais ou publicação de pesos.

## Começar

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_repository.py
.venv/bin/lia-lab validate-data tests/fixtures/pilot.jsonl
.venv/bin/lia-lab doctor
```

Windows: usar executáveis em `.venv\Scripts\`; essa plataforma ainda não foi testada. [Guia técnico e comandos](docs/15-IMPLEMENTATION-FOUNDATION.md) explica outputs, limites e gates. Dependências pequenas de ferramentas foram instaladas para validar software; não uma stack de ML com modelos.

## Documentação oficial

- [Índice único](docs/README.md), [AGENTS](AGENTS.md) e [marca](docs/BRAND-STANDARDS.md).
- [Auditoria e comparação das branches](docs/00-PROJECT-AUDIT.md), [ADR de consolidação](docs/adr/0001-CONSOLIDATION.md).
- [Inventário AIRI](docs/01-AIRI-CAPABILITY-INVENTORY.md), [matriz de capacidades](docs/02-LIA-CAPABILITY-MATRIX.md).
- [Pesos versus runtime](docs/03-WEIGHTS-VS-RUNTIME.md), [família Lia](docs/04-MODEL-FAMILY-ARCHITECTURE.md).
- [Comparação e recomendação de bases](docs/05-FOUNDATION-MODEL-COMPARISON.md).
- [Treino](docs/06-TRAINING-STRATEGY.md), [dados](docs/07-DATASET-STRATEGY.md), [hardware](docs/08-HARDWARE-INFRASTRUCTURE.md), [benchmarks](docs/09-BENCHMARK-STRATEGY.md).
- [Governança](docs/13-GOVERNANCA-DE-EXPERIMENTOS.md), [skills/subagentes](docs/14-ORQUESTRACAO-DE-AGENTES.md), [fundação implementada](docs/15-IMPLEMENTATION-FOUNDATION.md).
- [Fontes](docs/SOURCES.md), [validação executada](docs/VALIDATION.md), [roadmap](docs/11-ROADMAP.md) e [decisões abertas](docs/12-OPEN-DECISIONS.md).

## Direção técnica

**Recomendação de candidato, não adoção aprovada:** Qwen3.5-4B para primeiro piloto útil; 0.8B para conformance econômica; Qwen3.8-27B para comparação remota de qualidade. Qwen3.5-27B é controle histórico; Gemma 4 é alternativa por variante. Português, persona, tools, treinamento/export e custo real ainda exigem medições pareadas. Uma base aberta não é um modelo Lia adaptado.

Core primeiro; Vision, Hearing, Speech, Game, Reflex e Omni são papéis/direções, não obrigação de sete treinos. Agent/Memory são comportamentos/contratos e serviços externos quando necessário. AIRI é referência técnica. Memória mutável, permissões e execução de ferramentas nunca são substituídas por fine-tuning.

## Limites

`infer-local` pode carregar somente snapshots locais após grant humano externo vinculado à operação exata, com runtime opcional e limites; nesta entrega não foi executado com checkpoint real. CLI não inicia treino, não baixa pesos, não faz upload e não promove artefatos à aplicação. `register-plan` exige paths explícitos de pesquisa e modelos aprovados, disjuntos; template PENDING deve falhar. `compare` pontua predições existentes, não executa inferência. `export-adapter` verifica/copia artefatos locais, não faz merge nem aprova release. Fixtures são fictícias, não dados de produção. Ver [testes e NOT-TESTED](docs/VALIDATION.md).
