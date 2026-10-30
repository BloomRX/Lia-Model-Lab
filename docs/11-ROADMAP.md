# 11 — Roadmap com gates verificáveis

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Fases e dependências (sem datas/custos aprovados)

| Fase | Trabalho / entregável | Dependências / gate de saída |
|---|---|---|
| 0 — esta missão | Auditoria, inventário código, matriz, arquitetura, shortlist, planos e fontes | Revisão documental; sem capacidade validada ou base adotada |
| 1 — fundação offline | **Implementado:** schema v1 texto/tools, dedup/splits, integridade, registro de planos, scorer e export estrutural de adapter | Testes sintéticos locais; não há trainer/inferência/modelo validado |
| 2 — Gate 0 da base | Congelar 0.8B/4B e finalistas remotos, cards/licenças/processor; ambiente/hardware | Autorização de downloads e orçamento; load/forward/backward/save/reload e backend alvo |
| 3 — avaliação antes de dados | Suíte Lia v0 e baseline dos finalistas | Test selado, thresholds/poder estatístico e hardware declarados |
| 4 — dados piloto | Persona canônica aprovada, cards e proveniência, mistura curada | Licenças/consentimento, schema/dedup/leakage e auditoria humana |
| 5 — primeiros pesos | SFT LoRA/QLoRA pequeno, experiment card, checkpoint/adapter privado | Aprovação de GPU/custo, retomada e melhora sem regressão crítica |
| 6 — Agent/Memory/social | Trajetórias, replay, tool protocol, memória fake, simulações Discord | End-to-end, ACL/injection/forget/cancel; não só JSON válido |
| 7 — Vision/Voice/embodiment | Grounding, ASR/TTS autorizados e contrato de intenção corporal | Benchmarks por modalidade, identidade vocal/direitos e hardware |
| 8 — Game Minecraft | Perception/reflex/brain/action, world-state fixtures e servidor autorizado | Sucesso por seed, preempção, segurança e experiência offline curada |
| 9 — Factorio | Adapter server-side, state/action space, economia/produção | Sem adapter benchmark permanece bloqueado; sem prometer paridade Minecraft |
| 10 — release | Merge opcional, quantizações, model card, notices, hashes, rollback | Gates qualidade/licença/performance por variante e autorização de publicação |
| Futuro — Omni | Distillation, routing e eventual consolidação/MoE | Benefício mensurável superior à composição; novos ADRs e orçamento |

Fases de percepção/jogo podem ter pesquisa paralela, mas não furam gates de execução/custo. Minecraft é trilha prioritária de agente após ferramentas e contratos: não depende de treinar fala ou de construir Omni. Nenhuma fase exige oito modelos independentes.

## Próximas cinco tarefas após a consolidação

1. **Revisão de decisões e persona:** proprietário revisa PR, confirma escopo do primeiro Core e profile; aceite = ADRs propostos revisados, nenhuma hipótese promovida silenciosamente.
2. **Diagnóstico local e plano remoto:** reconciliar 4/8 GB, SO/driver/Vulkan; obter proposta de envelope/custo sem contratar; aceite = inventário datado e orçamento máximo para aprovação.
3. **Renderer de dados para treino:** chat template nativo, tool serialization e loss masking com fixtures; aceite = tokens e labels verificados sem misturar resultados de tools com fala do assistant. Event/action/memory/embodiment continuam contratos futuros, não implementados por estes testes.
4. **Gate 0 comparativo:** fixar revisions/licenças de Qwen3.5-0.8B/4B, Qwen3.8-27B e alternativa Gemma; planejar probes e downloads autorizados; aceite = checklist compatibilidade com PASS/FAIL/INCONCLUSIVE por operação.
5. **Runner de baseline + dados aprovados:** gerar predições reais após autorização e medir base no test selado; revisar cards/proveniência/mistura de treino. O scorer offline já existe, mas fixtures não substituem baseline de modelo. Só depois aprovar SFT LoRA/QLoRA e PEFT save/reload.
