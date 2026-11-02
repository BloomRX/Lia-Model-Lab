# 09 — Avaliação e benchmarks Lia

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Protocolo comum

Plano de benchmarks, **nenhum resultado** nesta missão. Quantidades e thresholds abaixo são propostas a congelar antes do baseline. Usar sempre (1) base original sem adapter, (2) adaptado não quantizado, (3) adaptado quantizado em cada formato; acrescentar merged se existir. Base QLoRA 4-bit não substitui o baseline original.

Mesmo split, profile/prompt, tool schemas, sampling/budget e runtime; respeitar chat template nativo e registrar diferenças entre famílias. Fixar seed/config/revisions/hardware/processor, limites de contexto/concurrency, input hashes e timestamp. Se runtime difere, medir equivalência e declarar confundimento. Não exigir cadeias privadas de pensamento como ground truth: verificar resposta/ações e resultados.

| ID | Domínio | Fixture proposta (não gerada) | Métrica objetiva | Gate proposto |
|---|---|---|---|---|
| CHAT | Conversa pt-BR | 120 diálogos holdout estratificados | preferência cega, naturalidade/utilidade 1–5 | ganho de preferência com IC; sem regressão por registro |
| PERSONA | Identidade/humor/consistência | 100 cenários + 30 diálogos longos | contradição, bordões, estilo, rubrica humana | >=95% identidade factual do profile; ganho cego, sem aumento de repetição |
| REASON | Raciocínio/calibração | 200 problemas verificáveis | accuracy, Brier/abstenção, tokens | não inferior à base além da margem aprovada |
| CODE | Código | 60 tarefas pequenas licenciadas | pass@1 em testes selados/sandbox | sem regressão significativa; sem acesso externo |
| TOOLS | Ferramentas/segurança | 200 episódios, >=50 adversariais | schema, seleção, args, E2E, falso sucesso | >=99% schema e >=90% E2E; zero execução não autorizada nos testes críticos |
| PLAN | Planejamento/jobs | 80 objetivos com falhas e cancel | success/steps, recovery, cancel | >=85% conclusão; zero ação após cancel confirmado |
| ROUTE | Routing/fallback | 50 fixtures provider/capability failures | rota válida, fallback explícito, timeout | 100% sem rota incompatível ou sucesso inventado |
| VISION | Imagem/objetos | 150 imagens licenciadas e negativos | VQA accuracy, box IoU, hallucination | melhora/retém base; reportar por categoria |
| SCREEN | Tela/desktop/computer use | 100 tarefas UI sandbox | target accuracy, task success, clique indevido | >=90% alvo; zero ação destrutiva sem confirmação |
| VIDEO | Temporal | 60 clips licenciados com ordem invertida | event ordering, temporal QA | >=85% ordem correta; não passar só com um frame |
| ASR | Reconhecimento pt-BR | 120 clips com ruído/sotaques autorizados | WER/CER, RTF, atribuição | WER <=15% limpo/<=25% ruído como hipótese; revisar por corpus |
| AUDIO | Som não verbal | 80 clips com eventos e desconhecidos | macro-F1, onset/offset, calibração | macro-F1 >=0.85; avaliar desconhecidos |
| VOICE | TTS/voz/prosódia | 100 frases + 30 contextos emocionais | MOS cego, inteligibilidade, identidade, RTF | MOS >=4/5 proposto; sem voz não autorizada, não só ASR re-transcription |
| MEM | Memória externa | 120 episódios fictícios multi-sessão | recall factual, conflito, update/forget/scope | >=90% fatos recuperáveis corretos; zero leakage/ressurreição nos casos testados |
| RETR | Retrieval pt-BR | 100 queries sobre corpus fictício | Recall@5, nDCG@10, latência | Recall@5 >=0.90; comparar lexical-only e híbrido |
| SOCIAL | Grupos/Discord | 80 cenas texto + 40 turnos de voz | atribuição, pertinência/silêncio, overlap | >=95% atribuição em fixtures; zero vazamento entre canais testados |
| GAME | Minecraft agente | 5 tarefas ×20 seeds holdout ×3 repetições | sucesso no estado, mortes, invalid actions, tempo | >=80% sucesso por tarefa e zero violação; reflex benchmark separado |
| FACTORY | Factorio agente | 5 mapas/objetivos ×20 seeds | throughput, energia, desperdício, goal completion | estado final verificável; meta numérica depende do adapter, bloqueado hoje |
| BODY | Embodiment/presença | 80 fala+rig/event fixtures | schema, intenção coerente, sincronismo A/V | 100% enums válidos, erro A/V p95 <100ms proposto |
| LAT | Latência/recursos | 30 runs warm + 5 cold por perfil | TTFT/p50/p95, tokens/s, RAM/VRAM pico, stop latency | metas Reflex/Fast/Deep por hardware; não ocultar cold start |
| PRIV | Privacidade/consentimento | 100 casos ACL/captura/delete/injection | violações e evidência de bloqueio | zero violação na suíte crítica; não promessa universal |

## Estatística, regressões e contaminação

Comparação pareada, IC 95% por bootstrap por conversa/episódio (não tokens correlacionados); Wilson para taxas de sucesso, McNemar quando adequado. No mínimo 3 seeds de geração/treino quando custo permitir. Avaliação humana cega e randomizada, >=3 avaliadores quando viável, registrar concordância e intervalos. O proprietário aprova a rubrica de identidade; um LLM judge não é único árbitro.

Não usar média global para compensar regressão: dashboard por capability, idioma, ruído, dificuldade, jogo, quant e hardware. Margem provisória de não inferioridade em qualidade geral: -2 pontos percentuais, a calibrar pelo poder estatístico; amostra inconclusiva não vira PASS. Melhoria em persona não autoriza regressão em memória, tools ou visão. Zero falhas numa suíte finita não é garantia de risco zero.

Testes selados por fonte/pessoa/mundo/seed/projeto; hashes e canários de contaminação, sem dados test em SFT, calibragem de quant ou seleção de hyperparams. Troca de benchmark exige versão nova e reavaliação das bases.

## Prova operacional para jogos e social

Minecraft: sobreviver a fome/perigo; coletar recurso; craft; navegar; cumprir instrução com interrupção. Medir world state e retorno do executor, não frase “concluí”. Ablar reflex-only, planner-only e combinado. Avaliar estado desatualizado, action denied, stuck e reset de inventário. Seeds de treino e avaliação separados.

Factorio: progresso de produção com energia/recurso finitos, bottleneck e recuperação de interrupção; sem adapter/servidor verificável, benchmark fica BLOCKED. Conversa sobre fábricas não conta.

Discord: participantes fictícios ou consentidos; mistura de menções, DM/canal, quem falou com quem, fala simultânea, canal proibido, recusa de gravação e cancelamento da resposta falada. Mocks aprovam conformance; validação real demanda servidor de teste e consentimento separado.

## Quantização e promoção

Medir BF16 master (FP16 apenas se validado), 8/6/5/4-bit com curvas de qualidade×RAM/VRAM×latência. Checar persona, pt-BR, schemas/argumentos, reasoning, visual grounding e memória em todas as variantes. Retirar variante que falha gate crítico, mesmo que menor/rápida. Quantização não suportada = N/A justificado, não PASS.

Relatório usa template AVALIACAO: métricas brutas/agregadas, IC, exemplos redigidos, falhas, hardware/runtime e hashes dos artefatos. Gates atuais: licença/base, dados, reprodutibilidade, qualidade e distribuição, conforme [governança](13-GOVERNANCA-DE-EXPERIMENTOS.md). Releases só no alcance testado.
