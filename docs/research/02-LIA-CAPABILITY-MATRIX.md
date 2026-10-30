# 02 — Matriz de capacidades Lia

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Como interpretar

Cruzamento do [inventário](01-AIRI-CAPABILITY-INVENTORY.md) com requisitos Lia. Todas as linhas são **desejadas / NOT-TESTED na Lia nesta missão**. A/B/C/D definidos em [03](../architecture/03-WEIGHTS-VS-RUNTIME.md). P0 = primeiro Core; P1 = próximo incremento prioritário (inclui Minecraft); P2 = evolução; P3 = opcional. Prioridades propostas, não cronograma aprovado. IDs de benchmark estão em [09](09-BENCHMARK-STRATEGY.md). “Dataset” significa plano, não autorização de coleta.

| ID | Funcionalidade AIRI | Capacidade desejada Lia | Classe | Requisitos do modelo | Dataset necessário | Runtime necessário | Especialista necessário | Benchmark | Prioridade |
|---|---|---|---|---|---|---|---|---|---|
| chat | Consciousness / LLM | Conversa pt-BR e identidade | D(A+C) | linguagem/instruções | persona, ptbr | context builder, provider | Core | CHAT | P0 |
| stream | Streaming / conversa contínua | Resposta incremental cancelável | D(A+B+C) | turnos e retomada | turnos/interrupções | SSE, fila, cancel | ASR/VAD | LAT | P0 |
| reason | Reasoning | Raciocínio verificável | A | resolver/calibrar incerteza | problemas com verificadores | budget/verificadores | Core/Deep | REASON | P0 |
| plan | Planejamento / agentes | Decompor e replanejar | D(A+C) | planos com feedback | trajetórias multi-step | job state/replay | Core/Agent | PLAN | P0 |
| tools | Tool calling / execução | Escolher, encadear e interpretar | D(A+C) | schemas/erros/stop | tool trajectories | registry, ACL, executor | Agent (adapter) | TOOLS | P0 |
| route | Seleção de modelos / fallback | Rotas por capacidade e falha explícita | C | nenhum obrigatório | fixtures de rotas | capability registry, circuit breaker | não obrigatório | ROUTE | P0 |
| context | Context management | Contexto relevante sem mistura | D(A+C) | seleção/sumarização grounded | context-window tasks | token budget, compactação | reranker opcional | MEM | P0 |
| vision | Imagem / objetos | VQA e grounding sem alucinação | D(A+B+C) | visão e incerteza | imagens licenciadas/boxes | processor e anexos | Vision/VLM | VISION | P1 |
| screen | Screenshots / interfaces | OCR/layout/alvo de ação | D(A+B+C) | grounding de UI | telas sintéticas/licenciadas | captura+accessibility | Vision | SCREEN | P1 |
| capture | Screen capture / webcam | Capturar apenas com consentimento | C | nenhum | fixtures de permissão | OS capture, indicador, retenção | nenhum | PRIV | P1 |
| video | Vídeo / contexto temporal | Ordem de eventos e estado atualizado | D(A+B+C) | temporal grounding | clips/frames timestamps | amostragem, cache, TTL | Vision/video | VIDEO | P2 |
| desktop | Percepção desktop | Estado da janela sem acesso excessivo | D(A+B+C) | observation fusion | screen + eventos | foco, redaction, acessibilidade | Vision | SCREEN | P2 |
| asr | STT / reconhecimento | Transcrição pt-BR | B | acústica/linguagem | fala consentida + texto | mic, resample, VAD | ASR | ASR | P1 |
| sound | Compreensão áudio / eventos | Detectar alarme, fala e contexto | B | eventos não verbais | eventos com onset/offset | captura e timestamps | audio classifier/Omni | AUDIO | P2 |
| tts | TTS / resposta falada | Fala inteligível com identidade Lia | D(B+C) | texto→voz/prosódia | voz licenciada/consentida | chunking/playback | Speech/TTS | VOICE | P1 |
| voice | Voz personalizada / conversão | Identidade vocal autorizada | D(B+C) | speaker/style conversion | gravações autorizadas | voice registry, consent ledger | TTS/VC | VOICE | P2 |
| emotionvoice | Prosódia / emoção na voz | Emoção apropriada sem exagero | D(A+B+C) | style-conditioned speech | fala+emoção/intensidade | speech style mapping | TTS | VOICE | P2 |
| barge | Interrupções / tempo real | Parar fala e ceder turno | D(A+B+C) | turn-taking | overlap/turnos | echo control, cancel, VAD | VAD/ASR | LAT | P1 |
| speaker | Voiceprint / participantes | Atribuir fala sem falsa certeza | D(B+C) | speaker embeddings | vozes consentidas | identidades/ACL | speaker model | SOCIAL | P2 |
| history | Histórico / conversas | Persistência e replay por sessão | C | nenhum | fixtures de histórico | DB/session store | nenhum | MEM | P0 |
| episodic | Memória de atividades/experiências | Episódios com fonte e tempo | D(A+B+C) | extração e retrieval | episódios fictícios | event log+índice+ACL | embedding/reranker | MEM | P1 |
| semantic | Memória semântica/contextual | Fatos atuais, conflito e proveniência | D(A+B+C) | buscar e usar fatos | query/fact/conflict | versioned facts store | embedding | MEM | P1 |
| relation | Memória relacional | Relações com scope e consentimento | D(A+C) | atribuição/não inferir sensível | relações fictícias | namespace social/retention | Core | MEM | P1 |
| embed | Embeddings / recuperação | Recall relevante sem vazamento | D(B+C) | representação semântica | pares query/doc | vector+lexical index | embedding/reranker | RETR | P1 |
| summary | Sumarização / longa duração | Compactar sem inventar | D(A+C) | resumo fiel | história→resumo+evidências | budget/links ao original | Core | MEM | P1 |
| persona | Cards / Character V3 / identidade | Lia reconhecível em contextos diversos | D(A+C) | estilo, humor, reações | persona multi-turn | profile versionado | Core persona adapter | PERSONA | P0 |
| social | Humor / preferências / continuidade | Interação natural em privado/grupo | D(A+C) | pragmática/limites | social e emotion | preferências mutáveis externas | Core | SOCIAL | P1 |
| spontaneous | Reações / espontaneidade | Iniciativa com cooldown e quiet hours | D(A+C) | decidir se falar | speak/silent pairs | scheduler/policy | Core/Reflex | SOCIAL | P2 |
| bodies | Live2D / VRM / MMD / Spine / Tachie | Corpos intercambiáveis | C | nenhum para importar | fixtures de rigs/assets | loaders/renderers/licenças | nenhum | BODY | P1 |
| embody | Expressões / gaze / movimentos / gestos | Intenção→corpo com coerência | D(A+C) | intenção afetiva estruturada | contexto→emotion/gaze/gesture | rig map, arbiter, TTL | classifier opcional | BODY | P1 |
| lips | Lip sync / visemes | Sincronização fala/boca | D(B+C) | fonemas/alinhamento se usado | fala com alinhamento | clock, rig, DSP | aligner opcional | BODY | P1 |
| discordtext | Discord texto/canais | Conversar respeitando contexto | D(A+C) | multiuser/social | diálogos fictícios de canal | Discord connector, ACL | Core | SOCIAL | P1 |
| discordvoice | Discord voz/multiusuário | Ouvir e responder ao grupo | D(A+B+C) | turnos/atribuição | simulações consentidas | voice transport, jitter/consent | ASR/TTS/speaker | SOCIAL | P2 |
| telegram | Telegram / demais sociais | Mensagens contextualizadas | D(A+C) | social/tool use | conversas simuladas | connector, rate limits | Core | SOCIAL | P2 |
| mcpercept | Minecraft Perception / world state | Sinais estruturados atuais | D(B+C) | detector opcional | estado/eventos | Mineflayer ou adapter próprio | classifier opcional | GAME | P1 |
| mcreflex | Minecraft Reflex | Sobreviver a perigo/fome | D(A+C) | policy leve opcional | state→reaction | priority/preemption | Reflex ou regras | GAME | P1 |
| mcplan | Minecraft Consciousness / estratégia | Concluir objetivos com feedback | D(A+C) | policy/planejamento | trajectories seedadas | goal state/observações | Game adapter | GAME | P1 |
| mcaction | Minecraft Action / inventário / navegação | Executar skills válidas | D(A+C) | skill selection/args | ações+resultados | executor, pathfinder, inventory | Game | GAME | P1 |
| gamelearn | Aprendizado por experiência | Melhorar policy offline mensurável | D(A+C) | credit assignment posterior | replays/resultados | logs/curadoria/simulador | Game | GAME | P2 |
| factorio | Factorio / produção / estratégia | Economia e plano executável | D(A+C) | produção/recursos | state/action/reward | adapter server-side a criar | Game Factorio | FACTORY | P2 |
| mcp | MCP / plugins / APIs | Uso seguro de tools dinâmicas | D(A+C) | schema induction | tool traces/injections | MCP host, sandbox | Agent | TOOLS | P1 |
| search | Web Search | Buscar/citar/verificar atualidade | D(A+C) | query/source synthesis | buscas com evidência | search connector | Core | TOOLS | P1 |
| browser | Browser / computer use | Agir em UI com permissão | D(A+B+C) | grounding/planejamento | DOM+screen/actions | browser sandbox/OS input | Vision/Agent | SCREEN | P2 |
| systemtools | Filesystem / terminal | Operações limitadas ao workspace | D(A+C) | escolha e interpretação | tool errors/deny | sandbox, allowlist, confirmação | Agent | TOOLS | P1 |
| jobs | Automation / background / eventos | Tarefas canceláveis e limitadas | D(A+C) | plano e relato de resultado | jobs/timeouts | scheduler/durable jobs | Agent | PLAN | P2 |
| ui | Stage / tray / mobile / temas | Presença contínua e UX | C | nenhum | fixtures de ciclo de vida | UI/OS/update/renderer | nenhum | BODY | P2 |
| art | Artistry / stickers / beat sync | Expressividade contextual | D(A+B+C) | escolha relevante | contexto→asset/event | assets, DSP, provider | gerador de imagens opcional | BODY | P3 |
| home | Home Assistant / dispositivos | Ação com confirmação de risco | D(A+C) | tool-use | ações permitidas/negadas | connector/permissão por dispositivo | Agent | TOOLS | P3 |

Cobertura é demonstrada pelo benchmark operacional: GAME exige mudança de estado no jogo; TOOLS exige resultado no executor; MEM exige retrieval/isolamento/deleção; BODY exige sinal no rig. Resposta textual plausível não conta como sucesso.
