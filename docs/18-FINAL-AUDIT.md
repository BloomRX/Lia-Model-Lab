# 18 — Auditoria final da PR #1

Data: **2026-10-31**. Parecer: **pronta para revisão humana da infraestrutura/pesquisa após as correções abaixo; não aprovação de pesos, execução, licença ou release**. Não constitui certificação de segurança. Sem merge, fechamento ou aprovação de inferência real.

## Estado inicial e método

GitHub consultado antes de editar: PR1 OPEN/mergedAt=null, MERGEABLE, HEAD `4eadfa39860914ea1c84e19e0bc246933a44ae62`; main `20f1883ad1671139d7c023eff42b72c6bca96525`. Main é ancestral da branch; divergência main...branch **0/19**. Nenhum comentário/review/thread. Os quatro checks iniciais (verify/lightweight-api, eventos push/PR) tinham SUCCESS. Há um workflow ativo; `main.protected=false`, rulesets visíveis vazios: CI aprovado não significa política de proteção de branch obrigatória configurada.

Snapshot restaurado tinha HEAD/index182f1a1, mas **zero diferenças byte a byte** para todos os arquivos do HEAD remoto. Fetch e comparação precederam reset mixed, sem substituir bytes, trocar branch ou force push. A baseline foi executada antes das correções: **157 passed, 1 skipped**. Novos commits remotos devem sempre ser rechecados antes do envio.

Revisão sequencial pelo principal: módulos Python executáveis, CLI, schemas, scripts, configs/locks/workflow; testes e fixtures; documentação numerada/ADRs/fontes; nove skills e sete perfis. Não houve ferramenta de subagentes ou revisão independente. Evidência de revisão de código não é teste com checkpoint. Não reconsultamos todos os links/cards externos nem fizemos análise jurídica de LICENSE ausentes.

## Achados e correções

**P0 — nenhum identificado dentro do modelo de ameaça do ADR0003.** Não extrapolar isso para host comprometido, mesmo UID, dependências nativas, conteúdo hostil ou hardware não testado.

| ID | Grau | Achado concreto | Correção / regressão |
|---|---|---|---|
| F01 | P1 | register_plan verificava existência antes de atomic_json, que podia substituir registro concorrente | Reserva atômica do diretório/ID e publicação exclusiva; dois registradores reais em threads, exatamente um vencedor |
| F02 | P1 | seal/plan-inference/compare verificavam “arquivo novo”, mas usavam replace sobrescrevível | atomic_json(overwrite=False), publicação por hard link de temporário completo; concorrência e dangling symlink testados, sem fallback inseguro |
| F03 | P1 | Verificação/registro podiam associar hash posterior a config/manifest/split previamente lidos | Hash antes/depois das leituras, identidade verificada preservada no registro; mutações induzidas rejeitadas |
| F04 | P1 | Resultado “completo” podia omitir métricas de carga, input budget e relatório de perfil ou apresentar TTFT supostamente medido | Validação exige métricas finitas, null para não medido, total consistente, input+output/contexto e perfil; inválidos não promovidos |
| F05 | P1 | Ausência de memory.max podia cair na RAM do host e superestimar envelope em cgroup v1/layout desconhecido | Retorna null sem layout v2 reconhecido; inferência bloqueia. Não implementa sizing universal de hierarquias cgroup |
| F06 | P2 | Múltiplos arquivos de pesos sem índice eram aceitos; arquivos especiais eram ignorados | Índice obrigatório para múltiplos safetensors, mapping tipado e inventário sem FIFO/especiais; testes com tensores de zeros e FIFO descartável |
| F07 | P2 | Configs/suites malformadas falhavam tarde; target_modules string era aceito como sequência de caracteres | Validação estrutural antecipada, identidade/capability/mensagens, schemas e expected call; target_modules deve ser lista; testes negativos |
| F08 | P2 | JSON 1e999 virava infinity apesar do parser “strict”; YAML não finito/sintaxe inválida não tinha erro uniforme | Rejeição de overflow/NaN/inf e erro LabError para YAML inválido; regressões reais de parser |
| F09 | P2 | Finalização SQLite não verificava operação e podia substituir o primeiro finished | Finalização vinculada à operação consumida, transacional e idempotente; preserva timestamp inicial e rejeita operação trocada |
| F10 | P2 | Verificador podia omitir symlinks quebrados/diretórios antes de aplicar filtro de arquivos | Rejeita symlinks em árvores mantidas antes do filtro, com regressões |
| F11 | P2 | Gemma tinha descrição de família no campo model_id; docs tinham datas/telemetria e referências v1.0 ambíguas | Gemma marcado explicitamente family-placeholder/model_id=null, sem inventar ID; índice único, fontes históricas/datas separadas, streaming do piloto corrigido para memória limitada e referências legadas substituídas |

| F12 | P1 | JSON Schema de tools podia resolver $ref externo durante validação, fazendo I/O de rede/arquivos fora do fluxo autorizado | Validador compartilhado SFT/suite permite apenas referências no próprio documento, antes da resolução; testes negam URL/file e preservam referências locais |

Correções não reduzem autorização ou allowlist. Usamos os módulos existentes, sem adicionar backend/modelo/trainer ou duplicar infraestrutura.

## Arquitetura, execução e segurança

- `io` centraliza serialization, hashing, limites de path e publicação; Dataset Factory valida e divide; experiments registra planos/resume/export **estruturais**; evaluation pontua predições fornecidas; cards gera rascunhos. Não há trainer nem runtime de produto. Imports dos módulos instalados foram exercitados sem Torch/modelos.
- Inferência: supervisor monta operação exata e consome grant; worker valida binding/claim antes de imports ML. A única dependência reversa authorization→inference é import local de confirmação, sem ciclo de inicialização observado nos testes/imports. Não houve necessidade de refatoração arquitetural ampla.
- Grant externo SQLite/TTY continua vinculado à ação, checkpoint/revision, manifesto/licença, suite, código, paths, budgets, TTL e uso único; strings/env/fixture não aprovam execução real. Claim/finalização/replay/expiração e concorrência têm testes. TTY/DB/relógio/UID local confiável são pressupostos, não autenticação criptográfica.
- Snapshot: licença Apache atestada/revisada, config/arquitetura explícitas, sem Python/pickle/auto_map no contrato do modelo, trust_remote_code=False, safetensors/header/shards/bytes/hashes e symlinks rejeitados. Atestar Apache não verifica juridicamente o conteúdo nem torna outro checkpoint Apache. Download segue autorização separada.
- portable-process não aplica rlimits/rede; Linux CPU rlimit e netns são opcionais, sem fallback. Não isolam FS/Unix IPC/VRAM e NPROC tem caveats UID/root. Windows child-only, sem Job Object; não equivalentes macOS/GPU/Vulkan/ROCm. Nesta auditoria não se testou contenção com modelos; suíte usa filhos Python descartáveis e pode observar recusa de userns.
- Resultados parciais/timeout/interrupção/falha não se tornam completed-not-quality-approved. Status completo tampouco aprova qualidade/release. Protocolo JSON não é assinatura contra adulteração pelo mesmo usuário.
- Caminhos resolvidos devem permanecer nas raízes possuídas; roots pesquisa/aprovados disjuntas. Não prometemos defesa contra troca de arquivo/symlink por invasor com o mesmo UID entre chamadas, NFS/distributed locking ou durabilidade universal em power loss.

## Catálogo, licenças e GGUF

Qwen3/3.5 têm apenas contratos de arquitetura/registry API testados; Qwen3.8, MoE, Gemma e exports não suportados continuam sem loader. Checkpoints, revisions, LICENSE/tokenizer/templates exatos não foram validados com pesos. Gemma é um placeholder explícito de família até seleção de variante/ID real: não inferir ID a partir de nome comercial.

LFM3 mantém **7 originais +6 GGUF separados**, Base distinto do chat, d1 distinto do generativo, parent/formato explícitos e schema research-only. Nenhum registro foi promovido. Catálogo não é autoridade de autorização.

O [relatório LFM3](17-LFM3-RESEARCH.md) distingue guia oficial consultado, texto vinculante integral não acessado, LICENSE/NOTICE individuais não inspecionados e risco comercial/Threshold >=US$10M/Legal Entity/downstream/atribuições/marcas. Não há aprovação, aceite ou mudança de allowlist. Open-weight não significa licença permissiva/OSI. Revisão por artefato continua obrigatória, inclusive Qwen/Gemma/voz/dependências.

llama.cpp b11960: código/conversor/template inspecionados historicamente, release/binários consultados; sem build, inferência ou validação de RX580/AMD/Vulkan. GGUF requer projectors/codec conforme modalidade; d1 suporta subconjunto tipado documentado. Esta auditoria não baixou/compilou/executou llama.cpp.

## Validação executada e limites

- Base final: **197 passed, 1 skipped** (módulo API opcional).
- Ambiente API separado TF5.22.1 sem Torch: **205 passed**. API/tokenizer original de teste não é tokenizer Qwen/LFM3.
- 40 casos adicionais ao baseline, derivados dos achados; stubs/métricas/tensores são fictícios declarados, não modelo/inferência.
- Instalação limpa de wheel: wheel construído sem deps, instalado em terceiro venv com lock base; todos os módulos importados fora da raiz fonte, schemas encontrados no pacote, doctor e validate-data executados; Torch ausente. Valida empacotamento/CLI Linux Python3.11, não plataformas ou stack ML.
- pip check nos três ambientes, compileall, CLI help/doctor, JSON/YAML/TOML/JSONL/links locais, manifesto e diff --check: executados; resultados finais em [VALIDATION](VALIDATION.md). O verificador não certifica anchors Markdown, links externos ou legalidade/autenticidade dos hashes.
- CI base passou a incluir pip check e compileall além de testes/verificador. Estado remoto final e SHA são registrados na PR após push para evitar referência autorrecursiva ao próprio commit.

## Pendências que não bloqueiam integrar pesquisa/software

**P3 / próxima missão:** instrumentação TTFT/prefill/energia; cgroup v1/hierarquias adicionais, Windows Job Object/sandbox externo; wheel/OS/Python matrix em CI; pins de Actions por SHA e hashes de distributions dos locks; auditoria transitiva/supply chain; ativar branch protection e revisão independente pelo proprietário. Não foi efetuado scan completo de CVEs nem auditoria formal de dependências nativas. CI verde e versão pinada não garantem ausência de vulnerabilidades.

**Bloqueios mantidos para executar/adaptar/distribuir modelos:** aquisição e revisões individuais/autorização humana, LICENSE/NOTICE, código customizado/vendorização LFM, runtime/hardware/driver, pesos/config/tokenizer/template, masks exatas e forward/backward/PEFT/reload/merge/quantização. Qualidade/persona pt-BR e efeitos reais das tools/jogos/memória/voz continuam não testados. Skills/perfis tiveram sintaxe/referências/procedimentos/limites revisados; execução real de agentes e delegação continuam NOT-TESTED.

Não houve downloads de checkpoints/GGUF/datasets, instalação Torch/stack GPU, recursos pagos, treino, dados pessoais, aceite de termos, publicação de pesos ou grants operacionais reais. Não adicionar contagens históricas de testes a resultados atuais.
