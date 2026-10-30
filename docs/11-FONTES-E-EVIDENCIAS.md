# 11 — Fontes, evidências e snapshots

> **Atualização Missão 001 (2026-10-30):** documento v1.0 preservado. Consulte o [índice da pesquisa e correções](README.md), a [auditoria](research/00-PROJECT-AUDIT.md) e as [fontes atuais](research/SOURCES.md). Afirmações históricas não comprovam validação nesta missão.

**Data da pesquisa:** 30/10/2026. Links devem ser rechecados antes de decisões de download, treinamento ou distribuição; model cards e documentação mudam.

## Fontes AIRI

- AIRI overview: https://airi.moeru.ai/docs/en/docs/overview/
- AIRI desktop manual (0.13.0, 28/10/2026): https://airi.moeru.ai/docs/en/docs/manual/tamagotchi/setup-and-use/
- AIRI quick start: https://airi.moeru.ai/docs/en/docs/manual/tamagotchi/
- AIRI provider configuration: https://airi.moeru.ai/docs/en/docs/manual/config/
- AIRI voice input/output: https://airi.moeru.ai/docs/en/docs/manual/config/audio
- AIRI Discord integration: https://airi.moeru.ai/docs/en/docs/integrations/discord
- AIRI repository: https://github.com/moeru-ai/airi
- AIRI Agent Guide: https://github.com/moeru-ai/airi/blob/main/AGENTS.md
- AIRI ADR — skills, automations and long-term memory (10/10/2026): https://github.com/moeru-ai/airi/blob/main/docs/ai/adr/2026-10-10-skills-automations-and-memory.md

## Fontes de modelos

- Qwen3.8-27B model card: https://huggingface.co/Qwen/Qwen3.8-27B
- Qwen3.8 official repository/docs: https://github.com/QwenLM/Qwen3.8
- Qwen3.5-27B model card: https://huggingface.co/Qwen/Qwen3.5-27B
- Google Gemma model overview: https://ai.google.dev/gemma/docs
- Gemma releases: https://ai.google.dev/gemma/docs/releases
- Gemma terms: https://ai.google.dev/gemma/terms
- Gemma tuning guide: https://ai.google.dev/gemma/docs/tune

## Treinamento e ferramentas

- QLoRA paper, NeurIPS 2023: https://proceedings.neurips.cc/paper_files/paper/2023/hash/1feb87871436031bdc0f2beaa62a049b-Abstract.html
- Hugging Face TRL SFTTrainer: https://huggingface.co/docs/trl/sft_trainer
- Hugging Face PEFT: https://huggingface.co/docs/peft/index
- Unsloth repository: https://github.com/unslothai/unsloth

## Arena.ai

- Arena Agent Mode help: https://help.arena.ai/articles/5432423882-how-to-use-agent-mode (last updated 08/10/2026 in the source consulted)
- Arena coding in Agent Mode: https://help.arena.ai/articles/1655691990-how-to-use-coding-in-agent-mode (last updated 26/08/2026 in the source consulted)
- Arena blog: https://arena.ai/blog/coding-in-agent-mode

## Evidências internas do Lia-Project

Snapshot remoto consultado pelo GitHub connector em 30/10/2026:

- Repositório: https://github.com/BloomRX/Lia-Project
- Branch: `arena/01a10290-lia-project`
- HEAD consultado: `eb38005d4c63a584d1fae345e82ff9a4bb8ef7a2`
- `AGENTS.md`: https://github.com/BloomRX/Lia-Project/blob/arena/01a10290-lia-project/AGENTS.md
- Estado operacional: https://github.com/BloomRX/Lia-Project/blob/arena/01a10290-lia-project/docs/project/CURRENT-STATE.md
- Runtime de provider Lia (30/10): https://github.com/BloomRX/Lia-Project/blob/arena/01a10290-lia-project/docs/architecture/LIA-PROVIDER-RUNTIME-2026-10-30.md
- Independência AIRI (28/10): https://github.com/BloomRX/Lia-Project/blob/arena/01a10290-lia-project/docs/architecture/AIRI-INDEPENDENCE-2026-10-28.md
- Plano de desacoplamento: https://github.com/BloomRX/Lia-Project/blob/arena/01a10290-lia-project/docs/architecture/AIRI-DECOUPLING-PLAN-2026-10-28.md
- Arquitetura de voz personalizada: https://github.com/BloomRX/Lia-Project/blob/arena/01a10290-lia-project/docs/product/M1-PERSONAL-VOICE-ARCHITECTURE.md

## Evidências internas do Lia-Model-Lab

- Repositório existente: https://github.com/BloomRX/Lia-Model-Lab
- Branch principal consultada: `main`, commit `6b711ad3663e97dece7d57960f457363d56469d9`
- README atual consultado: `# Lia-Omni`
- Blueprint existente: https://github.com/BloomRX/Lia-Model-Lab/blob/main/docs/Lia_Model_Blueprint.md

## Limites desta pesquisa

- O manual oficial AIRI declara que pode estar incompleto e que a tradução inglesa é derivada do chinês; confirmar comportamento no app/source correspondente.
- A manual/documentation 0.13.0 é posterior ao fork `0.12.0-beta.5` registrado no Lia-Project; não inferir paridade.
- O inventário é uma combinação de documentação upstream e leitura da árvore/arquivos do fork. Nem todos os flows foram executados neste trabalho.
- A shortlist de modelos é documental. Não houve download, benchmark, treino ou teste de hardware no âmbito desta documentação.
- Nenhum modelo ou dataset recebeu aprovação final de licença para distribuição; revalidar termos na data de cada release.
