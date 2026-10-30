# 04 — Arquitetura progressiva da família Lia

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Recomendação: família coordenada, inicialmente poucos pesos

Não criar oito checkpoints só por haver oito nomes. Começar com **Core adaptado + especialistas de prateleira + runtime independente**. Preservar possibilidade de VLM integrado; não treinar todos os módulos ao mesmo tempo.

| Nome conceitual | Papel e forma inicial | Evolução condicional |
|---|---|---|
| Lia Core | Base aberta instruction-tuned, persona/pt-BR/instruções; adapter SFT | Mais capacidade apenas com regressões controladas |
| Lia Vision | Encoder da base VLM, ou VLM roteado; inicialmente congelado | Adapter de tela/grounding se baseline falhar |
| Lia Voice | Percepção de áudio/ASR, VAD e identidade de falante em especialistas | Audio understanding; não chamar ASR de compreensão de som |
| Lia Speech | TTS independente, estilo e voz autorizados | Tuning vocal consentido; VC é outro experimento |
| Lia Agent | Comportamento de tools do Core, não executor | Adapter próprio se ablação mostrar vantagem |
| Lia Game | Policy/adapter por ambiente, com skills externas | RL em sandbox só após BC/SFT e ambiente verificável |
| Lia Memory | Política de consulta/escrita e embeddings/reranker | Não é um checkpoint que memoriza pessoas |
| Lia Omni | Nome do sistema multimodal coordenado | Consolidação opcional, não obrigação de modelo único |

## Três velocidades e autoridade única

```text
Eventos (desktop/voz/social/jogo) → normalização/ACL → estado + memória externa
  ├─ Reflex: VAD, parar fala, perigo, olhar (regras/classificador)
  ├─ Fast: Core pequeno, conversa e skill cotidiana
  └─ Deep: modelo maior/mesmo Core com budget maior, plano complexo
                 ↓ propostas tipadas
         árbitro de ações / permissões / budget
                 ↓
       tools, jogos, avatar, fala → resultados/eventos
```

Metas iniciais **não medidas**, dependentes de hardware: Reflex evento→decisão p95 <100 ms, Fast TTFT p95 <1,5 s no alvo remoto, Deep aviso de progresso <2 s e deadline explícito por job. Não prometer esses números em CPU/RX 580. Medir rede+fila+modelo+execução separadamente.

Reflex não precisa subir sequencialmente Fast→Deep; rotas paralelas somente em recursos independentes. Um árbitro mantém lease por recurso (voz, teclado, inventário, movimento), prioridade emergência>cancelamento>ação corrente>iniciativa. Deep não pode desfazer uma parada de segurança. Resultado atrasado com state_version antigo é descartado/revalidado.

## Contratos propostos v0 (documentais, não runtime implementado)

```json
{
  "schema_version": "0",
  "event_id": "fixture-event",
  "trace_id": "fixture-trace",
  "scope": {"owner": "fictional-user", "scene": "test-room"},
  "timestamp": "2026-10-30T00:00:00Z",
  "state_version": 7,
  "observation": {"kind": "game_state", "source": "test-adapter"},
  "proposal": {"tool": "inventory.inspect", "arguments": {}, "expected_state_version": 7},
  "deadline_ms": 1000
}
```

Envelope de resultado deve incluir action_id, status (`ok/error/denied/cancelled/stale`), evidência, duração e novo state_version. Permissão é calculada pelo runtime, nunca aceita de um campo emitido pelo modelo. Idempotency key impede replay de comandos com efeitos. Versionar schema e toolset; registrar model revision e profile revision na execução.

Embodiment separado de tool calls: `emotion`, `intensity`, `gaze_target`, `gesture`, `speech_style`, `ttl_ms`, `utterance_id`. Só enums/rig capabilities permitidos, intensidade limitada, decay para neutral e sincronização com áudio. Não gerar JavaScript/frames 3D para expressar emoção.

## Memória sem retreinamento por conversa

Event log episódico (experiência, pessoas autorizadas, jogo, tarefa) + fatos semânticos versionados + relações/preferências com escopo. Cada item: id, owner/scene ACL, tipo, fonte, event_time, valid_from/to, confidence, sensitivity, consent_ref, expiry, supersedes, content_hash, embedding_model_revision.

Fluxo: proposta de escrita → filtro de sensibilidade/consentimento → dedup/conflito → store; query → **ACL antes da busca** → busca lexical+vetorial → rerank → top-k com fonte/tempo → modelo responde com incerteza. Indexar por modelo/versão; reindexar ao trocar embedding. Resumos apontam aos episódios, não substituem originais sem política de retenção. Esquecer invalida fato, vetor, cache e propagação; backups têm prazo de purga explícito e não reintroduzem fatos após restore. Memória de grupo não pode expor conversa privada. Não usar speaker embedding como consentimento.

## Evolução sem reconstrução

1. Contratos/replay e baseline; Core pequeno e runtime mock.
2. Core persona + tools, ASR/TTS e memória externa; sem adapters em cadeia não avaliados.
3. Vision/Screen e Minecraft com interfaces estáveis; Factorio separado.
4. Routing por custo/capacidade; adapters especializados com testes de interferência.
5. Distillation para Fast/Reflex se direitos de teacher e dados permitirem.
6. Só consolidar Omni quando quality/latency/custo superarem composição.

MoE dentro de um modelo **não** equivale ao router entre modelos. Não converter arbitrariamente adapters em experts MoE. Shared representations exigem alinhamento/projeções e treino; compartilhar inicialmente IDs/eventos/schemas, não tensores incompatíveis. Ensemble custa latência e memória; usar para avaliação/desacordo antes de produção. Merge não é substituto de ablação. Distillation pode perder capacidades e reproduzir restrições do teacher.
