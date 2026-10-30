# 03 — Pesos versus runtime

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Taxonomia

- **A — pesos:** representação/generalização aprendida: linguagem, raciocínio, interpretação de contexto e estratégias. Não significa que precisamos treinar novamente uma capacidade já forte na base.
- **B — especialista:** percepção, ASR, TTS, embedding, reranking, política de ação ou classificação, treináveis separadamente.
- **C — runtime:** persistência, relógio, captura, APIs, transportes, schemas, permissões, execução, animação e observabilidade.
- **D — híbrido:** combinação explícita A/B/C. Não usar D para esconder responsabilidade indefinida.

A [matriz](../research/02-LIA-CAPABILITY-MATRIX.md) atribui classe, dados e teste por capacidade. Falar sobre uma ferramenta/jogo/memória não satisfaz seu critério operacional.

## Fronteiras obrigatórias

| Função | Pesos/especialista | Runtime / proprietário do estado |
|---|---|---|
| Memória | Identificar necessidade, formular consulta, usar evidência, sugerir atualização | Persistir, ACL, índice, recuperação, deleção, backups |
| Discord | Relevância social, interlocutor, linguagem de grupo, turn-taking | API, canais, identidades, áudio, consentimento, rate limits |
| Jogos | Estratégia, seleção de skill e replanejamento | World state, simulação, ação, servidor, navegação, arbitragem |
| Persona | Padrões de estilo/humor/reação/valores autorizados | Profile versionado, preferências mutáveis e contexto social |
| Avatar | Intenção emocional/corporal e alinhamento com fala | Rig, renderer, visemes, áudio, relógio, clamp de intensidade |
| Tool use | Escolha, argumentos e interpretação de resultado | Validação, permissão, sandbox, retry/idempotência, execução |
| Reasoning | Inferência e planejamento | Orçamento/timeout, checkpoints de tarefa, cancelar, verificar resultado |

## O que nunca deve ser “resolvido” por fine-tuning

Segredos, tokens, ACL, dados pessoais mutáveis, relógio, configuração de rede, execução de comandos e garantia de autorização. Recusas aprendidas ajudam, mas não substituem controles determinísticos. Modelo não concede sua própria permissão.

Prompt injection em tela, jogo, página, memória ou tool result é entrada não confiável. Delimitar dados e instruções, aplicar menor privilégio; executar em ambiente isolado. Nenhum plano gerado pode saltar confirmação de ação destrutiva.
