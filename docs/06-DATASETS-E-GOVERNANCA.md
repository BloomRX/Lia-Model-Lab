# 06 — Datasets, curadoria, privacidade e licenças

> **Atualização Missão 001 (2026-10-30):** documento v1.0 preservado. Consulte o [índice da pesquisa e correções](README.md), a [auditoria](research/00-PROJECT-AUDIT.md) e as [fontes atuais](research/SOURCES.md). Afirmações históricas não comprovam validação nesta missão.

## 1. Objetivo

Criar datasets próprios de alta qualidade que ensinem capacidades da Lia sem copiar conversas privadas, violar licenças ou misturar dados de produção com dados de avaliação.

**Qualidade > volume.** Um conjunto menor, consistente, revisado e bem rotulado costuma ser um primeiro experimento melhor do que milhões de exemplos sem procedência.

## 2. Famílias de dataset

| Dataset | Conteúdo | Saída desejada | Privacidade/risco |
|---|---|---|---|
| `lia-persona-ptbr` | Diálogos e cenários originais escritos/revisados para Lia | Resposta com identidade, estilo e limites | Não incluir dados pessoais reais sem consentimento |
| `lia-instruction` | Instruções, perguntas, explicações, raciocínio e tarefas gerais | Resposta correta e calibrada | Revisar licenças e dados potencialmente sensíveis |
| `lia-tool-use` | Chamadas de ferramentas, schemas, retornos e continuação | Tool call correto, interpretação e conclusão | Tokens/IDs/URLs reais devem ser falsos ou redigidos |
| `lia-memory-ops` | Extrair, guardar, consultar, atualizar, esquecer e respeitar escopo | Operação de memória tipada | Dados sintéticos; teste de deleção e isolamento |
| `lia-social-discord` | Conversas multiusuário simuladas e exemplos consentidos/licenciados | Menção, atribuição correta, turn-taking e privacidade | Nunca usar export privado de servidor por padrão |
| `lia-vision-screen` | Screenshots sintéticos/licenciados e perguntas com referência | Grounded visual answer | Desfoque/redação de nomes, chats, tokens e dados pessoais |
| `lia-game-minecraft` | Trajetórias state/action/result em mundos controlados | Sequência de ações para objetivos | Servidores confiáveis, licença dos assets/mods e sandbox |
| `lia-game-factorio` | Estado, inventário, recipes, planejamento e ações | Planejamento de produção/recursos | Licença de jogo/mod e ambiente isolado |
| `lia-embodiment` | Contexto -> emoção/intensidade/gaze/gesture | Saída JSON de expressão | Dados de atores/personagens licenciados |
| `lia-safety` | Prompt injection, abuso de ferramentas, consentimento e refusals | Recusar ou pedir confirmação corretamente | Adversarial; controle de acesso |

## 3. Fontes permitidas

- Conteúdo original criado para a Lia.
- Dados sob licença compatível com uso, modificação e redistribuição pretendidos.
- Dados sintéticos gerados por professor/LLM com origem e método identificados, seguidos de filtragem, deduplicação e revisão.
- Dados de ambientes simulados próprios (Minecraft/Factorio/etc.) com autorização e respeito às licenças do jogo, mod e ferramenta.
- Conversas de teste do proprietário apenas quando houver autorização específica, minimização, redaction e uma justificativa clara; nunca como default.

## 4. Fontes proibidas sem aprovação específica

- Histórico privado do ChatGPT/Discord/Telegram/email do usuário.
- Áudio do microfone, voiceprint ou voz de outra pessoa sem consentimento/licença.
- Screenshots de desktop com dados pessoais, tokens, chats ou arquivos privados.
- Datasets “scrapeados” sem licença/origem verificável.
- Conteúdo que viole termos de serviço ou direitos de terceiros.
- Chaves, tokens, senhas, IDs privados ou identificadores pessoais.

## 5. Metadados obrigatórios por dataset

Cada dataset deve ter um dataset card (usar `templates/DATASET-CARD.md`) com:

- nome, versão, finalidade e responsável;
- fonte/origem e data de aquisição;
- licença e autorização para derivação/redistribuição;
- composição, idioma, modalidades e contagens;
- método de anonimização, redaction e dedup;
- limites conhecidos, vieses e riscos;
- split train/validation/test e política anti-leakage;
- checksum de cada arquivo/manifest;
- procedimento para remover uma fonte e reconstruir a versão.

## 6. Privacidade e isolamento

- Memórias pessoais permanecem no runtime e armazenamento do usuário, não no dataset global.
- Discord deve usar namespace por usuário/servidor/canal conforme permissão; mensagens de um servidor não devem contaminar resposta a outro.
- Testar ataques de exfiltração: pedido para revelar conversa, token, memoria de outro user ou conteúdo que não pertence ao interlocutor.
- Dados sensíveis não entram no treino apenas porque o usuário os forneceu em uma conversa.
- Aplicar retenção curta para dados de captura/voz e uma forma real de deletar.
- Não registrar transcrições ou screenshots nos logs padrão de avaliação.

## 7. Formatos e normalização

Manter um formato canônico independente de framework, depois converter para template do modelo.

Exemplo conceitual de conversa:

```json
{
  "id": "example-000001",
  "source": "synthetic-authored",
  "license": "CC-BY-4.0",
  "language": "pt-BR",
  "task": "tool_use",
  "messages": [
    {"role": "user", "content": "Qual é o horário atual em Tóquio?"},
    {"role": "assistant", "tool_calls": [{"name": "clock.lookup", "arguments": {"timezone": "Asia/Tokyo"}}]},
    {"role": "tool", "name": "clock.lookup", "content": {"local_time": "09:15", "date": "2026-10-30"}},
    {"role": "assistant", "content": "Em Tóquio são 09:15 de 30 de outubro de 2026."}
  ],
  "quality": {"reviewed": true, "reviewer": "curation-team"}
}
```

Este é exemplo sintético de schema, não dado pronto para treino. Não copiar timestamps de exemplo como fatos vivos.

## 8. Split e leakage

- Split por origem/conversa/ambiente, não random por linha quando há sequências relacionadas.
- Manter `test` selado e sem acesso do treinador.
- Datasets adversariais podem ter suite pública e privada; reportar qual foi usado.
- Detectar duplicatas exatas e semânticas entre splits.
- Registrar qualquer contaminação suspeita e invalidar a avaliação quando necessário.

## 9. Dados de jogos e agentes

Trajetórias devem ter `observation`, `action`, `result`, `reward/goal`, `environment_version`, `seed` e condição de término. Separar ações de alto risco, uso de comandos/código, networking e manipulação de arquivos. O agente não deve aprender a executar scripts recebidos de jogadores/servidores sem validação.

## 10. Licença e cadeia de proveniência

O direito de utilizar um modelo-base não implica automaticamente o direito de distribuir qualquer derivative sob a mesma licença. O release gate deve revisar termos da base, dos dados, das vozes, imagens, assets 3D, plugins e ferramentas. Correção Missão 001 (2026-10-30): o card oficial do Gemma 4 declara Apache 2.0, mas os direitos dos dados/vozes e notices do checkpoint exato ainda precisam de revisão; Qwen3.8-27B e Qwen3.5-27B declaram Apache-2.0 nos respectivos model cards consultados, mas datasets e código ainda têm licenças independentes.
