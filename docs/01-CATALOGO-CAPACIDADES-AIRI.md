# 01 — Catálogo de capacidades AIRI como referência

**Snapshot documental:** manual oficial do AIRI 0.13.0, publicado/atualizado em 28/10/2026.  
**Snapshot do fork em Lia-Project:** `airi/apps/stage-tamagotchi/package.json` declara `0.12.0-beta.5` na branch `arena/01a10290-lia-project` consultada em 30/10/2026.  
**Regra:** este catálogo mapeia capacidades a estudar; não declara que todas estão implementadas, estáveis ou aprovadas na Lia.

## 1. Como ler os estados

- **AIRI documentado:** o manual 0.13.0 descreve a capacidade.
- **AIRI experimental/limitado:** a própria documentação aponta maturidade incompleta, dependência de source service, teste limitado ou ausência de implantação pronta.
- **Lia — base/legado:** a capacidade aparece na árvore AIRI incorporada ao `Lia-Project`; continua dependente de componentes legados até migração própria.
- **Lia — parcial próprio:** há código/contratos da Lia em andamento, mas não significa validação completa de produto.
- **Lia — não comprovado:** não foi possível comprovar um runtime próprio completo no snapshot usado.
- **Model Lab:** indica se existe requisito de aprendizado nos pesos; não significa que o recurso será executado por pesos apenas.

## 2. Aplicação, presença e interface

| Capacidade AIRI | O que significa | Como tratar na Lia | Participação dos pesos |
|---|---|---|---|
| Desktop companion / Stage | Personagem persistente na área de trabalho, janela principal, controles e chat | Reproduzir a experiência com Stage e ciclo de vida próprios; o Stage atual do fork ainda é AIRI | Nenhuma obrigatória; avatar/estado emocional usa saídas estruturadas do modelo |
| Web / mobile | Superfícies Web e mobile, com diferenças de recursos | Definir plataformas próprias e parity gradual | Nenhuma direta |
| Tray / controle de janelas | Mostrar, esconder, redimensionar, alinhar, abrir settings/chat e encerrar | Runtime/UI desktop | Nenhuma |
| Spotlight / quick actions | Atalho global para solicitar ações rápidas e receber notificação | Integração de desktop, permissões e UX | Tool-use/planning pode ser necessário |
| Floating/classic chat | Janela flutuante ou clássica, histórico, anexos e controles | Chat UX próprio | Conversa, multimodalidade e tool-use |
| Várias conversas/cartões | Conversas vinculadas a personagens/cards, troca e histórico | Persistência e seleção no produto | O modelo usa contexto; armazenamento é externo |
| Character Card | Identidade, scenario, greeting, behavior, system prompt e preferências por módulo | Perfis/persona configuráveis da Lia | Sim: adapter/persona SFT para consistência; configuração continua externa |
| Themes / scenes | Temas e fundos visuais | UI/assets | Não |
| Character model import | Live2D, Spine 2D, VRM 3D, MMD e Tachie | Renderer, loader, assets e licenças | Não; só sinais de animação/emotion podem vir do modelo |
| Godot Stage | Renderer alternativo experimental focado em VRM | Estudar apenas se fizer sentido para Stage próprio | Não |
| Model animation | Idle, blinking, gaze, tracking, expressões, skins, animações, parâmetros e boca sincronizada | Rig/renderer/animation engine; corpo digital da Lia | Modelo pode emitir emoção, gaze/gesture intent; animação em si é externa |

## 3. Conversa, cérebro e comportamento

| Capacidade AIRI | O que significa | Como tratar na Lia | Participação dos pesos |
|---|---|---|---|
| Consciousness/chat | Seleção do provedor e modelo principal de conversa | Brain/runtime próprio com roteamento por capacidades | **Central**: linguagem, instrução, diálogo e raciocínio |
| System prompt / behavior | Persona, cenário, greeting e instruções pós-histórico | Profile da Lia, regras e configurações versionadas | Sim: internalizar estilo e comportamento estável, sem perder controle via config |
| Streaming / tool loop | Resposta incremental, chamadas de ferramentas, retorno e continuação | Transporte e orquestrador próprios | Sim: aprender formato, decisão e uso de ferramentas |
| Tool cards | Renderização de chamadas de ferramentas sem widget próprio | UI/tool registry | Modelo deve produzir chamada válida; widget é UI |
| Decisions / recipes | Skills reutilizáveis, escolha de opções e procedimentos | Sistema de skills e policy engine | Sim: seleção/execução de procedimentos, mas passos e guardrails externos |
| Background tasks | Tarefas em sessões ocultas, independentes da conversa principal | Scheduler, job manager, cancelamento e notificações | Planejamento e resumo são úteis; scheduler é externo |
| Automations | Gatilhos por tempo, inatividade ou observação de módulos | Motor de eventos e automações | Modelo decide conteúdo da tarefa quando solicitado; cron/trigger não depende de LLM |

O ADR upstream de 10/10/2026 descreve uma arquitetura aceita para skills, decisions, automations, background tasks e long-term memory. Isso é uma decisão de arquitetura upstream, não garantia de maturidade de cada UI/feature no release atual.

## 4. Percepção, voz e criação

| Capacidade AIRI | O que significa | Estado/maturidade observada na doc | Participação dos pesos |
|---|---|---|---|
| Vision / image input | Análise de imagens anexadas | Requer provedor/modelo com image input | Modelo multimodal/VLM ou especialista de visão |
| Vision Capture / screen ticker | Captura de janela/display em intervalos e envia contexto para personagem | Manual descreve fluxo developer/debug atual; exige consentimento e permissão de captura | Modelo deve interpretar screenshot e continuidade temporal; captura é externa |
| Video understanding | Manual atual lista o módulo de Vision; modelos atuais podem ter vídeo, mas isso não significa que toda build AIRI processe vídeo de forma geral | Validar por caminho de runtime concreto | Modelo com vídeo ou frames temporais + orquestração |
| Speech / TTS | Síntese da fala com provider, model e voice | Provider separado | Modelo TTS/voice dedicado; não presumir que o LLM gere áudio |
| Hearing / STT | Microfone e transcrição para texto | Provider de transcription; controles de sensibilidade | ASR dedicado ou modelo de áudio; pipeline externo |
| Wake words | Detecção de palavra de ativação | Manual não apresenta walkthrough completo/teste abrangente | Classificador/modelo pequeno ou detector externo |
| Voiceprint | Identificação por embedding de voz | Manual afirma que fluxo completo não foi testado pelos editores; dado pode identificar pessoa | Modelo speaker embedding separado; dado biométrico exige proteção especial |
| Stickers | Seleção/coleção de stickers para resposta | Manual afirma que área não foi testada em detalhe | Modelo decide conveniência/seleção; assets e renderização externos |
| Artistry | Geração de imagem via provedor; fluxo interativo pode chamar ferramenta | Exige image provider e tool calling ou fluxo especial de artista | LLM aprende quando solicitar; gerador de imagem é outro modelo |
| Beat Sync | Analisa áudio de janela/display e emite eventos de batida para efeitos do Stage | Módulo com captura e parâmetros de DSP | Geralmente DSP/sinal; opcionalmente modelo classifica eventos, não é tarefa do chat model |

## 5. Memória, ferramentas e integrações

| Capacidade AIRI | O que significa | Estado/limite explicitamente documentado | Participação dos pesos |
|---|---|---|---|
| Short-term memory | Memória de curto prazo além do contexto de conversa | Manual: em desenvolvimento | Aprender sumarização/continuidade; buffer é externo |
| Long-term memory | Ler, escrever e esquecer fatos por personagem | Manual alerta que maturidade/trigger ainda podem mudar; memory page geral também contém aviso de indisponibilidade | Treinar política de extração, recuperação, atualização e esquecimento; dados ficam fora dos pesos |
| Discord | Bot em canais de texto e voz; resposta usa modelo de chat ativo; voice input pode precisar de STT | Serviço bot separado; texto responde a DM/menção, não a toda mensagem | Conversa social, multi-user context, turn-taking, tool use; Discord API/conexão/permissões externas |
| Telegram | Bot para conversar em Telegram | Serviço separado; README upstream inclui DB e modelos para chat/vision/embeddings | Social dialogue e tool-use; bot/API/database externos |
| X / Twitter | Integração descrita no manual | Link aparece como indisponível no menu; status deve ser tratado como indisponível/limitado até nova prova | Texto social e chamadas de ferramenta, não API |
| Web search | Pesquisa atual via serviço externo (ex.: Tavily/DeepSeek na doc) | Requer provider/key | Aprender quando buscar, formular consulta, avaliar fontes e sintetizar; web é externa |
| Minecraft | Agente para controlar sessão Minecraft | Serviço local/source; instrução explícita para usar servidor confiável. No fork inspecionado, README informa que o runtime Mineflayer atual está em depreciação e deve migrar para Fabric | **Especialização de agente**: estado de mundo, percepção, plano, ação e feedback; integração/servidor externos |
| Factorio | Integração para controlar jogo/servidor | Manual diz que AIRI não inclui integração server-side pronta para deploy | Planejamento de produção/recursos e ações via adapter do jogo; não apenas LLM chat |
| Home Assistant | Controle de dispositivos domésticos | Configuração disponível, documentação detalhada ainda ausente | Tool calling e políticas; Home Assistant/API/dispositivos externos |
| MCP Server | Ferramentas fornecidas por processos externos | Desktop; comandos/args/env; só confiar em servidores MCP autorizados | Modelo aprende seleção/argumentos; MCP host, ferramentas e permissões externos |
| Computer use / local app access | Permitir que chat veja e opere aplicações locais | Manual mostra toggle de acesso no composer; o escopo é controlado pela aplicação | VLM + planejamento + output de ação estruturado; captura/execução/sandbox externos |

## 6. Dados, providers e sistema

| Capacidade AIRI | O que significa | Como tratar na Lia | Pesos? |
|---|---|---|---|
| Provider categories | Chat, Vision, Speech, Transcription e Artistry | Registry/capability contract/credential manager próprios | Não; os pesos são selecionados por tarefa |
| Local models | Importar/gerir modelos locais | Model registry e runtime local | Não, mas consome os pesos treinados |
| Data export/reset | Exportar, apagar e resetar dados locais | Privacidade, portabilidade e lifecycle próprios | Não |
| WebSocket connection | Canal de serviços com auth token e rede local | API/transport próprio; política de rede segura | Não |
| System settings | Tema, idioma, analytics, tray, atalhos e experimental options | UI/config do produto | Não |

## 7. Modelo especial do Minecraft encontrado no fork

O `airi/integrations/minecraft/README.md` presente na branch inspecionada documenta arquitetura cognitiva em quatro camadas:

1. **Perception:** eventos brutos, sinais normalizados e regras de observação.
2. **Reflex:** comportamentos de reação rápida/FSM e inibição de raciocínio redundante.
3. **Conscious:** fila de eventos, lifecycle do turno LLM, planner e consulta de estado.
4. **Action:** task executor e ações concretas no runtime do jogo.

O mesmo README avisa que a implementação Mineflayer atual está em trilha de depreciação em favor de um runtime Fabric. Isso precisa influenciar a pesquisa: usar AIRI como fonte de requisitos, mas não construir o futuro da Lia em cima de um serviço declarado em migração.

## 8. Consequência para Lia Model Lab

O inventário inteiro não cabe em um único SFT. Ele se transforma em uma matriz de requisitos, adapters e modelos especializados:

- **Lia Core:** texto, pt-BR, personalidade, raciocínio, instrução, tool calling, planejamento.
- **Lia Vision/Perception:** imagem, screenshot e talvez vídeo temporal, nativo na base se possível.
- **Lia Speech:** modelos especializados de ASR/TTS, identidade vocal e prosódia.
- **Lia Agent:** loop de ferramentas, decisões, skills e execução com feedback.
- **Lia Game:** policies/trajectories/adapters por jogo, com sandbox e avaliação ambiental.
- **Lia Embodiment:** intenção emocional/gestual estruturada; assets, rig e renderer externos.
- **Lia Memory Skills:** operações de memória aprendidas; banco, index, retenção e privacidade externos.

A especificação detalhada está em `02-MATRIZ-CAPACIDADES-MODELO-RUNTIME.md`.
