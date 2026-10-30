# 07 — Estratégia de datasets e personalidade

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Governança antes de volume

Plano, não dataset de produção. Não coletar conversas privadas, Discord, imagens de tela ou vozes sem autorização específica. Conteúdo público não implica licença de treino. Fonte sem direitos claros fica em quarentena e não entra na mistura. Data card por fonte/versão; licença por exemplo/asset, direito de treino/derivação/redistribuição e consentimento por finalidade. LGPD, dados biométricos, menores e terceiros exigem revisão apropriada; anonimização não garante ausência de reidentificação.

Persona canônica precisa ser aprovada pelo proprietário antes de exemplos em escala: valores, estilo, humor permitido, preferências ficcionais estáveis, limites e comportamento privado/grupo. Não inventar biografia afetiva ou memórias do usuário para “dar personalidade”. Pesos aprendem tendências, não lista de bordões. Preferências pessoais mutáveis permanecem externas.

## Portfólio de dados (independentes, mistura controlada)

| Coleção | Estrutura / objetivo | Qualidade e risco específicos |
|---|---|---|
| Persona / emotion | contexto + diálogo → resposta + intenção afetiva opcional | Variação de tom, silêncio, humor, discordância, situações técnicas/tristes/grupo; evitar caricatura |
| Conversação pt-BR | multi-turn, registros regional/coloquial/técnico | Avaliadores nativos, naturalidade sem estereótipos; não transformar toda resposta em gíria |
| Reasoning | problema → solução verificada / resultado | Verificadores independentes; não imitar raciocínio longo incorreto |
| Coding | tarefa + repo/fixture → patch → teste | Código licenciado, sandbox e testes; separar projetos/snapshots entre splits |
| Tools | schemas + pedido → tool_call → result → continuação | Sem tool, deny, erro, timeout, retry, injection; ground truth executável |
| Planejamento | objetivo+estado → plano+ações+feedback | Estado e pré/pós-condições; avaliar replanejamento, não só plausibilidade |
| Vision | imagem + pergunta → evidência/box/resposta | Direitos de imagem, ambiguidade/ilegível, negativos |
| Screen understanding | screenshot+DOM/accessibility → alvo/ação | UI simulada/licenciada; resolução, coords e segredos redigidos |
| Audio understanding | áudio → eventos/tempo/descrição | Rotular fala vs som não verbal; direitos de áudio separados |
| Speech | texto/áudio + speaker consentido + prosódia | Alinhamento, taxa de amostra, condições acústicas, direitos de identidade vocal |
| Social / Discord | cena+participantes fictícios+turnos → responder/calar | Menções, ironia, conflito, fala sobreposta, canal privado, atribuição |
| Game interaction | estado/objetivo/action schema → ação → próximo estado/reward | Seeds, versão, engine, terminal condition; não confundir narrativa com execução |
| Minecraft | inventário/world events/navigation → skills/resultados | Sobrevivência, coletar/construir; mundos holdout, permissões e stuck recovery |
| Factorio | mapa/receitas/energia/fluxos → construir/produzir | Bottlenecks, produção/minuto, recurso/energia; servidor e adapter ainda ausentes |
| Memory retrieval | query+memórias fictícias/ACL → read/write/update/forget | Conflitos temporais, fonte, desconhecido, isolamento e deleção |
| Embodiment | contexto+fala+rig capabilities → emotion/gaze/gesture | Validade de enum, intensidade/TTL, sincronização e postura contextual |

## Schema canônico proposto v0

JSONL para texto/trajectories; manifest JSON/Parquet para metadados; mídia em object storage aprovado por hash, nunca bytes privados no Git. URI não deve conter token. Conversor por chat template, não um template universal.

```json
{
  "schema_version": "0",
  "example_id": "synthetic-schema-example",
  "source_id": "original-fixture",
  "capabilities": ["tools", "persona"],
  "language": "pt-BR",
  "synthetic": true,
  "license": "PENDING_REVIEW",
  "consent_ref": null,
  "privacy": {"scope": "fictional", "pii_reviewed": true},
  "messages": [
    {"role": "user", "content": "Confira o inventário do mundo de teste."},
    {"role": "assistant", "tool_calls": [{"id": "call1", "name": "inventory.inspect", "arguments": {}}]},
    {"role": "tool", "tool_call_id": "call1", "content": {"wood": 3}},
    {"role": "assistant", "content": "Há três unidades de madeira no inventário."}
  ],
  "tools_version": "fixture-v0",
  "media": [],
  "episode_id": "test-episode",
  "split_group": "fixture-only",
  "quality": {"review_status": "schema-illustration-not-training-data"}
}
```

Campos adicionais por modalidade: media sha256/mime/duration/sample_rate/dimensions/timestamps, state_before/after, action_id, reward e done; source URL/revision, creator/model/prompt/hash sintético, transformação/toolchain, reviewer, retention/deletion. Exemplo acima é somente ilustração de schema e **não está liberado para treinamento**.

## Pipeline de qualidade

1. Registro de origem/licença e finalidade, consentimento e retenção; bloquear PENDING.
2. Validação de schema/roles/tool_call_id, arquivos e alinhamento temporal.
3. Redaction de PII/segredos, revisão humana para biometria/imagens; logs também protegidos.
4. Dedup exato por hash após normalização + near-duplicate MinHash/texto; perceptual hash em imagem/áudio conforme aplicável. Manter fingerprints para remoção.
5. Filtros de idioma, qualidade/factualidade, execução das tools/código e consistência persona. LLM judge não pode ser único curador nem criar o próprio gabarito sem verificação.
6. Split por fonte/conversa/pessoa/projeto/mundo/seed e período **antes de expansão sintética**; dedup cruzado train/test. Propor 80/10/10 apenas quando grupos suficientes; test selado e benchmark externo não entra no treino.
7. Amostragem estratificada humana e registro de rejeições. Volume só depois de demonstrar qualidade.
8. Versionar manifests imutáveis, hashes de assets, script/config e política de retirada. SemVer do schema, snapshots de coleção e changelog de proveniência.

## Mistura e personalidade não repetitiva

Piloto proposto por tokens supervisionados: 25% persona/pt-BR, 25% conversa/instrução geral, 20% reasoning/coding, 20% tools/planejamento, 10% social/memória fictícia. Não é decisão de produção; revisar distribuição de erros e licenças. Multimodal/jogo em fases posteriores e misturas próprias. Controlar duplicação de situação e n-gramas, comprimento, bordões, bajulação, autoidentificação excessiva e diversidade emocional. Comparar persona-only vs mistura; manter holdout com paráfrases e conflitos.

Dados sintéticos: teacher/version/prompt registrados, termos verificados, geração declarada, verificadores e revisão humana; não fabricar consentimento nem usar modelo para “lavar” dado sem licença. Self-play de jogos só com ambiente autorizado e feedback verdadeiro. Aprovar eventual publicação separadamente do direito de treinamento interno.
