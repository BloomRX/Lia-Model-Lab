# Fontes, versões e evidências

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Método e alcance

Todas as consultas abaixo ocorreram em **2026-10-30 UTC**. Código por git/gh; cards/páginas oficiais por fetch de texto. Links de código fixam SHA; páginas/cards em main/latest são **mutáveis** e precisam de revision e hash antes de treinamento. Não são resultados de benchmark Lia. Leitura parcial de cards extensos limitou-se às seções de arquitetura/licença/capacidades e exemplos relevantes; tabelas inteiras de benchmarks não foram usadas para ranquear por pontuação.

## Fontes AIRI e Lia

| ID | Fonte / versão | Evidência usada / método |
|---|---|---|
| A1 | [AIRI v0.13.0](https://github.com/moeru-ai/airi/tree/3c4aca209330f1a78fe7288e8c4ca75639cd10e6) | Clone raso, tag e arquivos; base do inventário |
| A2 | [AIRI beta.5](https://github.com/moeru-ai/airi/tree/6ea680f51486d257f9b0eeda3bdc25db4307d3bb) | Fetch tag, tree de cognitive/memory/Factorio; não execução |
| A3 | [ADR skills/automations/memory](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/docs/ai/adr/2026-10-10-skills-automations-and-memory.md) | Estado Accepted; limitações live checks e privacidade declaradas |
| A4 | [CognitiveEngine](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/integrations/minecraft/src/cognitive/index.ts) / [container](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/integrations/minecraft/src/cognitive/container.ts) | Inicialização e separação perception/reflex/brain/executor |
| A5 | [memória](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/packages/stage-ui/src/stores/memory.ts) / [pgvector](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/packages/memory-pgvector/src/index.ts) | Persistência de fatos versus placeholder |
| A6 | [Discord adapter](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/integrations/discord-bot/src/adapters/airi-adapter.ts) / [VoiceManager](https://github.com/moeru-ai/airi/blob/3c4aca209330f1a78fe7288e8c4ca75639cd10e6/integrations/discord-bot/src/bots/discord/commands/summon.ts) | Intents, metadados, buffers por usuário, transcrição/reprodução |
| L1 | [Lia Project main snapshot](https://github.com/BloomRX/Lia-Project/tree/db99c709059a6d074b18361bfb32c9f144620632) | Clone raso e docs/AGENTS somente leitura |
| L2 | [package.json incorporado](https://github.com/BloomRX/Lia-Project/blob/db99c709059a6d074b18361bfb32c9f144620632/airi/apps/stage-tamagotchi/package.json) | Declara 0.12.0-beta.5; não prova paridade de código |
| L3 | [qa-benchmark](https://github.com/BloomRX/Lia-Project/blob/db99c709059a6d074b18361bfb32c9f144620632/docs/qa-benchmark.md) | Documenta método/harness de diagnóstico, não valores atuais de hardware; registro primário 4 GB não recuperado |
| L4 | [AIRI-ANALYSIS](https://github.com/BloomRX/Lia-Project/blob/db99c709059a6d074b18361bfb32c9f144620632/docs/architecture/AIRI-ANALYSIS.md) / [voz](https://github.com/BloomRX/Lia-Project/blob/db99c709059a6d074b18361bfb32c9f144620632/docs/product/M1-PERSONAL-VOICE-ARCHITECTURE.md) | Divergência de VRAM e limites AMD |

Referências detalhadas por capacidade: [inventário](01-AIRI-CAPABILITY-INVENTORY.md) e [ledger JSON](evidence/airi-evidence.json). A consulta de tags também retornou v0.13.1/v0.14.0, sem auditá-las; não afirmar que 0.13.0 é latest. Branch antiga `arena/01a10290-lia-project` e links da v1.0 são históricos e não foram usados como prova do main atual.

## Modelos: cards oficiais consultados (estado DOCUMENTED)

| ID | URL | Uso |
|---|---|---|
| M1 | https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/README.md | Apache, LM 27B, contexto, visão/vídeo, ferramentas/engines |
| M2 | https://huggingface.co/Qwen/Qwen3.5-27B/raw/main/README.md | Arquitetura densa, parâmetros/contexto/licença |
| M3 | https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/README.md | Candidato econômico, contexto/encoder/licença |
| M4 | https://huggingface.co/Qwen/Qwen3.5-0.8B/raw/main/README.md | Prototipagem, tamanho/contexto/licença |
| M5 | https://huggingface.co/Qwen/Qwen3.5-35B-A3B/raw/main/README.md | MoE 35B/3B, experts, contexto |
| M6 | https://ai.google.dev/gemma/docs/core/model_card_4 | Card oficial: Apache 2.0, variantes/PLE/Unified, modalidades e contexto; página avisa migração gemma.ai |
| M7 | https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/raw/main/README.md | Idiomas, Thinker–Talker, modalidades, saída e limites de engine |
| M8 | https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/raw/main/config.json | Componentes e limites de posição distintos; dtype BF16 |
| M9 | https://github.com/QwenLM/Qwen3.8/tree/2ea10dc725823bf7c3e21ce8557cbe15245132ae | README/release, família 3.5/3.6/3.8; gh consultado |
| M10 | https://github.com/google-deepmind/gemma/tree/9e1f74131ba9d45e5fe6ae7bb3941d9f2abb39c3 | README: JAX, Gemma4_E4B, FT e LoRA; não runtime validado |

Não aceitar termos/downloads automaticamente. Não houve inspeção integral dos LICENSE de todas as vozes/checkpoints auxiliares; ficam pendentes. Dados das tabelas estruturais são do card, não uma recontagem de tensores.

## Frameworks, especialistas e benchmarks — snapshots GitHub consultados

Cada linha aponta ao commit resolvido via API; README consultado no mesmo período. SHA é âncora para rechecagem, não lock de ambiente executado. Código/licença de repo não substitui model card dos pesos.

| Fonte | SHA / link | Finalidade |
|---|---|---|
| ggml-org/llama.cpp | [e0f142d5ddc1](https://github.com/ggml-org/llama.cpp/tree/e0f142d5ddc1461ce721644d92af33db23545105) | documentação oficial de stack/especialista; não executado |
| huggingface/peft | [ebf159f74d80](https://github.com/huggingface/peft/tree/ebf159f74d80a0d406f7afa943ede73b3901c20e) | documentação oficial de stack/especialista; não executado |
| huggingface/trl | [775de52a5805](https://github.com/huggingface/trl/tree/775de52a5805cbcd427556bde96677b946457ada) | documentação oficial de stack/especialista; não executado |
| huggingface/transformers | [e82b00dd04d7](https://github.com/huggingface/transformers/tree/e82b00dd04d71b2e2801ecf3029eea3858868091) | documentação oficial de stack/especialista; não executado |
| unslothai/unsloth | [9a1ea09dc3a2](https://github.com/unslothai/unsloth/tree/9a1ea09dc3a2a662d0a342cc200b0e49e4cb1f60) | documentação oficial de stack/especialista; não executado |
| axolotl-ai-cloud/axolotl | [a998b3d34c20](https://github.com/axolotl-ai-cloud/axolotl/tree/a998b3d34c208b2c9e40bf9a542c467a3e9fa993) | documentação oficial de stack/especialista; não executado |
| ROCm/ROCm | [63fd8390bf64](https://github.com/ROCm/ROCm/tree/63fd8390bf645ae3c0c715537025137127f892e3) | documentação oficial de stack/especialista; não executado |
| openai/whisper | [86098128c0b4](https://github.com/openai/whisper/tree/86098128c0b4f24f0e2aa2994de830614b474227) | documentação oficial de stack/especialista; não executado |
| SYSTRAN/faster-whisper | [9e472ae9de8b](https://github.com/SYSTRAN/faster-whisper/tree/9e472ae9de8bb374552f531f752654554b76b2d6) | documentação oficial de stack/especialista; não executado |
| rhasspy/piper | [73c04d81d559](https://github.com/rhasspy/piper/tree/73c04d81d5590ecc46e522de3601ce7fb29fc2be) | documentação oficial de stack/especialista; não executado |
| FunAudioLLM/CosyVoice | [074ca6dc9e80](https://github.com/FunAudioLLM/CosyVoice/tree/074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc) | documentação oficial de stack/especialista; não executado |
| QwenLM/Qwen3-TTS | [022e286b98fb](https://github.com/QwenLM/Qwen3-TTS/tree/022e286b98fbec7e1e916cb940cdf532cd9f488e) | documentação oficial de stack/especialista; não executado |
| QwenLM/Qwen3-ASR | [7c6daf77a242](https://github.com/QwenLM/Qwen3-ASR/tree/7c6daf77a2421100f5fb066495372c00129d39ff) | documentação oficial de stack/especialista; não executado |
| FlagOpen/FlagEmbedding | [897baa67c0ff](https://github.com/FlagOpen/FlagEmbedding/tree/897baa67c0ffddbfccf4e6776ff55310d67809d4) | documentação oficial de stack/especialista; não executado |
| QwenLM/Qwen3-Embedding | [44548aa5f0a0](https://github.com/QwenLM/Qwen3-Embedding/tree/44548aa5f0a0aed1c76d64e19afe47727a325b8f) | documentação oficial de stack/especialista; não executado |
| MineDojo/Voyager | [55e45a880755](https://github.com/MineDojo/Voyager/tree/55e45a880755d0c8c66ca7fb5fe7962ac8974f89) | documentação oficial de stack/especialista; não executado |
| openai/Video-Pre-Training | [095519fbd4ee](https://github.com/openai/Video-Pre-Training/tree/095519fbd4ee0e9281d19f19601e45629de9ac3f) | documentação oficial de stack/especialista; não executado |
| eleutherAI/lm-evaluation-harness | [d6de81643928](https://github.com/eleutherAI/lm-evaluation-harness/tree/d6de81643928d653435c431bae19945d41d32520) | documentação oficial de stack/especialista; não executado |

## Infraestrutura e workflow

- [AMD ROCm compatibility matrix](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html): página consultada identifica ROCm 10.1.0, 2026-08-26; selector de GPUs não inclui RX 580. Não representa teste no PC do usuário.
- [Arena Agent Mode](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode): sandbox/tools/GitHub/PR e avisos pós-merge; página mutável, sem inferir SLA de GPU/storage.
- Diagnóstico local via Python `platform`, `os.cpu_count`, `/proc/meminfo`, `shutil.disk_usage`, `which` e presença de dispositivos GPU: valores em 08, consulta nesta sessão. Não houve acesso ao PC do proprietário nem treinamento.

## Literatura metodológica para rechecagem

- [LoRA](https://github.com/microsoft/LoRA): método de adaptação low-rank; link técnico de referência, não nova execução.
- [QLoRA](https://github.com/artidoro/qlora): NF4/double quant/paged optimizer; link metodológico, compatibilidade local não testada.
- PEFT/TRL nos snapshots acima são a documentação operacional consultada para SFT/adapters/preferências. Hparams e thresholds deste pacote são propostas próprias, não alegações de resultado desses projetos.

## Limitações e honestidade de evidência

Auditoria estática seletiva de caminhos relevantes, não revisão de cada linha do AIRI ou runtime Lia. Não foram executados bots, jogos, captura, voz ou testes upstream; nenhum benchmark de modelo, treino ou conversor foi rodado. Sem GPU/hardware atual do proprietário. Licenças/model revisions de especialistas, formatos distribuídos por checkpoint e compatibilidade completa de multimodal tuning continuam gates abertos. Resultados de fornecedores não comprovam capacidade Lia. Revalidar todas as páginas mutáveis no Gate 0 e em cada release.

## Reconsulta na consolidação — 2026-10-30

Cards oficiais Qwen3.8-27B, Qwen3.5-27B/4B e Gemma 4 foram reconsultados nas URLs M1/M2/M3/M6. Propriedades estruturais continuaram documentadas; nenhum novo resultado Lia foi obtido. A recomendação econômica de 4B foi consolidada com alternativas, footprints e cenário de custo **hipotético**, não tarifa de serviço contratado.

Documentação Codex consultada: https://developers.openai.com/codex/subagents/ redirecionou para https://learn.chatgpt.com/docs/agent-configuration/subagents?surface=app. Seções Custom agents/Global settings confirmam perfis TOML e campos agents.enabled/max_concurrent_threads_per_session. Sintaxe local validada; cliente Codex não executado. Arena: https://help.arena.ai/articles/5432423882-how-to-use-agent-mode reconsultado; não foi identificada garantia de descoberta automática das skills/perfis neste host.

Dependências de software instaladas do PyPI/registry permitido: PyYAML, jsonschema, pytest, safetensors, numpy e dependências pequenas/de build, versões em requirements.lock. São ferramentas de validação/fixtures; nenhuma base, corpus ou adapter real foi adquirido. Reinstalação e smoke do pacote descritos em VALIDATION. Literatura/repositórios da pesquisa original permanecem fontes históricas fixadas, não auditados novamente na íntegra nesta consolidação.
