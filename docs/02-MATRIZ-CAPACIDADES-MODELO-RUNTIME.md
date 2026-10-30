# 02 — Matriz: capacidades dos modelos versus runtime

> **Atualização Missão 001 (2026-10-30):** documento v1.0 preservado. Consulte o [índice da pesquisa e correções](README.md), a [auditoria](research/00-PROJECT-AUDIT.md) e as [fontes atuais](research/SOURCES.md). Afirmações históricas não comprovam validação nesta missão.

Esta é a matriz central do projeto. Ela impede que o Lab tente “resolver por pesos” funcionalidades que exigem software, dados mutáveis, APIs ou controle de hardware.

Legenda: **P0** = requisito do primeiro Lia Core; **P1** = próxima camada relevante; **P2** = especialização avançada; **P3** = visão futura. O nível é prioridade proposta, não status de implementação.

| Capacidade da Lia | Prioridade | O que o modelo/pesos precisam aprender | O que precisa existir fora dos pesos | Família/artefato provável | Como avaliar |
|---|---:|---|---|---|---|
| Conversa natural | P0 | Diálogo, contexto, tom, resposta útil, turnos e referências | Runtime de chat, histórico, streaming | Lia Core | Avaliação humana cega, qualidade em pt-BR, regressão |
| Português brasileiro | P0 | Fluência, naturalidade, gírias/contexto sem exagero, escrita e compreensão | Locale, UI, tradução de strings | Lia Core LoRA/SFT | Suite pt-BR, preferência humana, factualidade |
| Identidade e personalidade | P0 | Voz narrativa, humor, temperamento, consistência, limites e relações | Persona profile, config, policy e memória de preferências | Lia Persona adapter/LoRA | Persona consistency, testes de cenário longo |
| Instrução e raciocínio | P0 | Seguir instruções, decompor tarefas, planejar, reconhecer incerteza | Orchestrator, limite de passos, timeout e estado de tarefas | Lia Core | Multi-step benchmark, execução observada |
| Tool calling | P0 | Escolher ferramenta, construir argumentos válidos, interpretar retorno e decidir próximo passo | Tool registry, schema validation, auth, permission, executor | Tool-use SFT / adapter | Taxa de argumentos válidos, sucesso end-to-end, prompt injection tests |
| Saída estruturada | P0 | JSON/schema, ação tipada, estado emocional, plano | JSON Schema validator e compatibilidade de runtime | Lia Core | Schema pass rate, determinismo dentro do contrato |
| Skills/recipes | P1 | Reconhecer oportunidade de usar skill, seguir etapas, pedir dados faltantes | Skill registry, versionamento, aprovação e executor | Skill/tool-use dataset | Taxa de skill selecionada corretamente, conclusão, abort |
| Memória episódica | P1 | Identificar fatos de eventos, resumir, buscar por tempo e relevância | Banco de dados, indexação, retenção, consentimento e delete | Memory-operation adapter | Recall preciso, origem, no-memory leakage |
| Memória semântica/fatos | P1 | Extrair fatos estáveis, distinguir hipótese de fato e atualizar conflito | Store/versionamento/fonte/confiança | Memory-operation adapter | Precisão, atualização e esquecimento |
| Memória social/relacional | P1 | Reconhecer quem está falando, relação e contexto multiusuário | Identidade autenticada, ACL, consentimento e namespace por pessoa | Social-context SFT + memory skills | Isolamento entre usuários, atribuição correta |
| Visão de imagem | P1 | Descrever, comparar, contar, ler diagramas, interpretar screenshots | Upload, decoder, provider/model router, limite de imagem | Base VLM ou Lia Vision | VQA com gabarito, grounding, OCR/layout |
| Percepção de desktop/tela | P1 | Interpretar screenshot, janela ativa, UI, estado e mudança temporal | Captura consentida, redaction, app/window focus, computer-use tools | VLM + action planner | Tarefas de UI com screenshots e ação verificável |
| Vídeo/percepção temporal | P2 | Resumir sequência, ordem de eventos, reconhecer mudança | Captura, sampling/stream, temporal buffer e sincronização | VLM com vídeo/frames | Perguntas temporais e event ordering |
| Áudio de entrada (fala) | P1 | Compreender voz, interrupção, contexto e talvez prosódia | Microfone, VAD, STT/ASR, permission, streaming | ASR ou áudio multimodal | WER, latência, ruído, sotaque pt-BR |
| Wake word | P2 | Classificar palavra de ativação, se neural | Detector always-on, áudio local e opt-in | Modelo pequeno especializado | False accept/reject, latência e consumo |
| Identificação de locutor | P2 | Speaker embeddings/classificação, se necessário e consentido | Vault de embeddings, consentimento, segurança e apagar | Speaker model especializado | FAR/FRR e auditoria de privacidade |
| Voz de saída | P1 | Não é responsabilidade central do LLM; controle de intenção/prosódia é útil | TTS, vocoder, voice profiles, streaming e dispositivo de áudio | Lia Speech/TTS model | MOS/avaliação humana, intelligibility, latency |
| Prosódia e emoção vocal | P2 | Emoção, ritmo, pausa, intensidade e estilo de fala estruturados | TTS prosody controls, alinhamento e voice identity | TTS/voice adapter | Avaliação humana, consistência entre fala e persona |
| Discord texto | P1 | Conversa social, multiusuário, resposta por menção/DM, citar contexto correto | Bot, API Discord, intents, ACL por canal, rate limits | Lia Core + social/tool dataset | Testes em servidor sandbox, multi-user isolation |
| Discord voz | P2 | Conversa falada, escuta/turn taking, resposta apropriada | Gateway, STT, TTS, áudio em tempo real, consentimento | ASR + Core + TTS | Latência ponta a ponta, barge-in, transcrição |
| Telegram/outros canais | P2 | Portabilidade do diálogo e contexto por plataforma | Connectors e APIs específicas | Core + connector tool-use | Contract tests por plataforma |
| Minecraft | P2 | Percepção de estado do jogo, planejamento, skill selection, tool actions, feedback | Bot runtime, game protocol, world-state API, sandbox, safety | Lia Game adapter/agent | Taxa de objetivos concluídos em mundos de teste |
| Factorio/estratégia | P3 | Planejamento de produção, recursos, dependências e objetivos longos | Mod/server API, estado do jogo, executor e scenario harness | Strategy/game adapter | Taxa de sucesso, custo/tempo, recoveries |
| Outros jogos via tela | P3 | Visão temporal, grounding, ações discretas/contínuas e feedback | Captura FPS, input controller, sandbox, anti-cheat e safety | VLM + game policy | Completion rate, action precision, safety |
| Browser/web search | P1 | Saber quando pesquisar, formular query, comparar fontes e citar | Search API, browser, allowlist, cache e provenance | Core tool-use | Citações corretas, factuality, freshness |
| Computer use | P2 | Planejar click/type/scroll, ler resultado, recover e parar | Tool execution, desktop permissions, screenshot, confirmation, kill switch | VLM + computer-use adapter | Tasks, error rate, permission abuse tests |
| Artistry/imagem | P2 | Formular prompt, escolher ferramenta, refinar e avaliar resultado | Modelo de geração de imagem, fila e armazenamento | LLM tool adapter + image model | Prompt adherence, user rating, asset licensing |
| Stickers/emotes | P2 | Selecionar resposta visual relevante e sem excesso | Sticker library, UI e regras sociais | Core classifier/prompt | Precision, appropriateness |
| Home Assistant/smart home | P2 | Entender intenção, selecionar ação, validar estado e confirmar | Home Assistant integration, ACL, confirmation para ações sensíveis | Core tool-use | Simulações, policy tests e ação reversível |
| MCP | P1 | Seleção e argumentos; compreender retorno e risco | MCP client, allowlist, sandbox, secret boundaries e permission prompts | Tool-use SFT | Contract/conformance tests e adversarial tests |
| Automações/background tasks | P2 | Planejar job, sumarizar status, decidir se deve notificar | Scheduler, triggers, hidden sessions, concurrency, cancellation | Agent adapter | Replays de trigger, cancelamento e duplicidade |
| Beat sync / reações a som | P3 | Interpretação semântica opcional do evento | DSP, audio capture, beat detector e animation events | DSP ou classificador especializado | Precision/recall e latência |
| Avatar emotion/gaze/gesture | P1 | Converter estado de conversa em emoção/intensidade/ação tipada | Renderer, rig, visemes, animation graph e assets | Embodiment adapter ou tokens estruturados | Gesto disponível, timing, coerência emocional |
| Scene/model assets | P3 | Nenhum requisito central nos pesos | Asset pipeline, rig, renderer, licença | Não é LLM | Import, render, performance |
| Proatividade/persona persistente | P2 | Julgar interesse/relevância e formular aviso sem ser intrusivo | Scheduler, consentimento, limites, estado idle/active | Core + behavior adapter | False notification, precision e opt-out |

## 1. Quais capacidades entram nos primeiros pesos?

### Lia Core v1 — obrigatório

- Português brasileiro e conversa natural.
- Identidade/persona base da Lia, com consistência em conversas longas.
- Seguir instruções, raciocínio prático e planejamento multi-etapas.
- Tool calling e saída estruturada.
- Interpretar respostas de ferramentas, erro, retry e conclusão.
- Saber quando não sabe, quando precisa de fonte atual e quando não deve agir.
- Segurança contra prompt injection e tentativa de desviar ferramentas.

### Lia Core v1 — não deve prometer

- Gerar áudio diretamente.
- Identificar pessoa por voz.
- Controlar um jogo sem adapter e treinamento de ambiente.
- Acessar Discord, navegador, arquivos ou desktop sem serviços e permissões.
- Persistir memórias sem store externo.
- Mover ou animar um avatar sem renderer e assets.

## 2. Como representar o contrato de uma ferramenta

Toda ferramenta deve ter contrato versionado e descrição compreensível pelo modelo:

```json
{
  "name": "discord.send_message",
  "description": "Envia uma mensagem em um canal autorizado.",
  "input_schema": {
    "type": "object",
    "required": ["channel_id", "content"],
    "properties": {
      "channel_id": { "type": "string" },
      "content": { "type": "string" }
    }
  },
  "risk": "external_communication",
  "requires_confirmation": true,
  "permission_scope": "discord.channel.write"
}
```

O modelo aprende a selecionar e preencher o contrato. O runtime verifica schema, identidade, permissão, confirmação e limites. A execução não é um efeito colateral da geração de texto.

## 3. Discord e jogos são casos especiais

### Discord

Para “falar no Discord”, o modelo precisa saber conversar como Lia em um contexto social com várias pessoas, manter separação entre interlocutores, entender menções/DMs, adaptar o tom e não divulgar memórias de uma pessoa a outra. O bot, intents, gateway, tokens, permissões e transporte de voz são código externo. Não treinar mensagens privadas do usuário sem consentimento e governança específicos.

### Jogos

Para “jogar”, o modelo precisa de percepção do estado e um protocolo de ações. Um chat model que sabe escrever “vou minerar madeira” não consegue executar essa intenção. Minecraft pede integração de mundo e bot; Factorio pede estado e ações de produção; jogo por tela pede VLM, captura e controle de input. Treinamento de jogo deve usar demonstrações/trajectories e testes em ambiente isolado; RL só depois de baseline supervisionado seguro.

## 4. Memória não é fine-tuning contínuo

O treinamento pode ensinar a Lia a:

- reconhecer uma informação potencialmente memorável;
- classificar se é preferência, fato, evento, tarefa, hipótese ou dado sensível;
- propor um resumo e uma referência de origem;
- consultar memória antes de responder;
- atualizar ou esquecer quando solicitado;
- diferenciar “lembro porque está salvo” de “apareceu no contexto desta conversa”.

Mas o conteúdo pessoal e mutável fica no armazenamento da aplicação, com namespace, origem, data, confiança, retenção e mecanismo de apagar. Nunca faça fine-tuning de cada conversa do usuário como forma de memória.
