# 07 — Avaliação, benchmarks e release gates

> **Atualização Missão 001 (2026-10-30):** documento v1.0 preservado. Consulte o [índice da pesquisa e correções](README.md), a [auditoria](research/00-PROJECT-AUDIT.md) e as [fontes atuais](research/SOURCES.md). Afirmações históricas não comprovam validação nesta missão.

## 1. Princípio

Cada capacidade da matriz precisa de um teste que reproduza a tarefa real. Não basta comparar perplexity ou benchmark geral. A avaliação tem que responder: a Lia ficou melhor nos cenários que importam e não perdeu capacidades importantes?

## 2. Grupos de avaliação

| Suite | Métricas | Gate mínimo sugerido |
|---|---|---|
| Conversa pt-BR | avaliação humana cega, naturalidade, clareza, utilidade | ganho sobre base em pelo menos um objetivo sem regressão crítica |
| Persona | consistência em multi-turn e cenários contraditórios | manter identidade sem obedecer instruções que tentam apagar guardrails |
| Instrução/raciocínio | accuracy por tarefa, conclusão, factuality, calibration | desempenho igual/melhor que baseline em tarefas prioritárias |
| Tool calling | schema pass, tool selection, argument accuracy, end-to-end success | nenhuma chamada inválida em casos críticos do conjunto de release; medir erro nos demais |
| Recoverability | retry, timeout, ferramenta offline, retorno vazio, cancelamento | não alegar sucesso falso; saber parar e reportar |
| Safety | prompt injection, segredo, escalada de permissão, recusa | zero vazamento em suite de regressão; bloqueios de alto risco funcionam |
| Memória | precision/recall, conflito, forget, scope leakage | recordar somente o que está autorizado e apagar de verdade |
| Discord | atribuição de interlocutor, menções, canal permitido, voice turn-taking | sem mistura de identidades ou vazamento entre canais |
| Visão | VQA, screenshot grounding, OCR/layout, comparação | resposta correta e ancorada; declarar quando imagem é ilegível |
| Vídeo | event order, temporal question answering, summarization | reconhecer sequência e não inferir frames não vistos |
| ASR | WER, latency, noise/speaker accent | resultado em pt-BR com faixa de condições documentada |
| TTS | inteligibilidade, naturalidade, emoção/prosódia, latency | voz consistente e sem artefato grave no hardware definido |
| Jogos | success rate por cenário, tempo/custo, invalid actions, recoveries | completar cenário holdout e respeitar limites ambientais |
| Computer use | task success, click/type accuracy, accidental action, recovery | só atuar dentro da permissão ativa; confirmação quando exigida |
| Performance | tokens/s, TTFT, latency p50/p95, VRAM/RAM, energy estimate | publicar por hardware, quantização e contexto testados |

## 3. Comparação antes/depois

Toda experiência deve comparar:

1. base original sem adapter;
2. adapter aplicado;
3. versão merged, se aplicável;
4. variantes quantizadas de distribuição;
5. pelo menos uma referência externa forte quando o orçamento e a licença permitirem.

Usar o mesmo prompt, chat template, tool schema, sampling, split e runtime. Qualquer diferença deve ser registrada.

## 4. Avaliação humana

- Preferência cega A/B, sem nomes de modelo visíveis.
- Múltiplos avaliadores ou revisão do proprietário em cenários de persona.
- Rubrica clara: naturalidade, utilidade, verdade, consistência, iniciativa apropriada, respeito a limites.
- Guardar prompts e resultados de avaliação de forma controlada; não publicar conteúdo pessoal.
- Reportar discordância entre avaliadores.

## 5. Evaluation gates

### Gate A — Modelo-base

- Licença aprovada.
- Compatibilidade de framework/inferência.
- Baseline calculado.
- Falhas conhecidas registradas.

### Gate B — Dataset

- Data cards completos.
- Licença/origem/consentimento confirmados.
- Dedup e leakage check concluídos.
- Test split selado.

### Gate C — Treinamento

- Reproduzível por config/seed.
- Logs sem segredo/dado privado.
- Loss/curvas e validação registrados.
- Checkpoint íntegro e hash calculado.

### Gate D — Qualidade

- Avaliação base versus adapter.
- Sem regressão crítica.
- Segurança e tool-use passam.
- Testes multimodais específicos passam se o modelo alegar essa capacidade.

### Gate E — Distribuição

- Merge/quantization validados.
- Compatibilidade no target runtime/hardware.
- Model card e notices completos.
- Política de update, rollback e suporte definida.

## 6. Release tags

- `experimental`: pesquisável/interno, não recomendado para usuários.
- `candidate`: passou gates principais, faltam plataformas/cenários explicitados.
- `stable`: passou todos os gates definidos para o alcance declarado.
- `deprecated`: tem substituto ou falha de manutenção; não usar em novas integrações.

Nunca usar `stable` sem declarar em quais plataformas, engines, quantizações e modalidades foi testado.
