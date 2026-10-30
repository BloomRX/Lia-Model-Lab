# Validação executada — consolidação e fundação offline

Data: 2026-10-30. Ambiente: Linux x86_64 kernel 6.1.158+, Python 3.11.2, 2 CPUs visíveis, sem `/dev/dri`, `/dev/kfd` ou `/dev/nvidia0`. Não é telemetria do PC do proprietário.

## Testes e verificações realmente executados

| Procedimento | Resultado e alcance |
|---|---|
| `.venv/bin/python -m pytest -q` | **44 passed**; schema/JSONL, roles/tools, direitos pendentes, consent_ref, limites, dedup/linkagem/grupos, splits, hashes, caminhos/symlinks, planos, retomada de metadados, predições e export/cards com tensores sintéticos |
| `python scripts/verify_repository.py --write-manifest` e novamente sem flag | **PASS**; 72 arquivos do pacote, cobertura exata/tamanhos/SHA-256, JSON real, YAML real com chaves duplicadas rejeitadas, TOML real, links relativos, skills e perfis |
| Parsers | 5 JSON do pacote + manifest JSON; 5 YAML de configs/CI; 9 frontmatters YAML; 9 TOML de projeto/config/perfis; JSONL fixture parseado e validado por schema Draft202012 |
| Links e agentes | 125 links relativos resolvem; 9 skills com frontmatter/entradas/procedimento/saída/critério/limites e 7 perfis com nome/descrição/instruções read-only e referências explícitas existentes. Âncoras de títulos e URLs externas não revalidadas automaticamente |
| Testes do próprio verificador | Incluídos nos 44: detectar link quebrado, symlink fora do pacote e alterações de cobertura/hash, além do happy path |
| Instalação editável e `pip check` | Pacote/CLI instalado, sem dependências quebradas |
| Instalação em venv separado | Reinstalado com `requirements.lock` + `--no-build-isolation --no-deps -e .`, 44 testes passaram e `pip check` sem erros |
| Smoke CLI instalado | validate-data, build-data, verify-data, write-card dataset e compare executados com fixtures; splits/card/relatório em `.cache/` ignorado, sem artefatos de produção |
| Template incompleto | `register-plan` rejeita PENDING com exit 2, sem criar raiz/experimento; comportamento também em teste automatizado |
| Export/retomada | Parser real safetensors e cópia/hashes exercitados somente com matrizes minúsculas de zeros e arquivos fictícios em diretórios temporários; não há adapter treinado |
| Integridade histórica útil | Ledger AIRI igual ao de `c18c4ee`; 39 registros preservados, 48 linhas da matriz e seus IDs de benchmark conferidos. Não foi repetido clone/execução upstream nesta consolidação |
| Marca | Conteúdo igual ao `origin/main` consultado, sem alteração de BRAND-STANDARDS |
| `git diff --check` | Sem erros de whitespace ao fechar a entrega |

A instalação limpa inicialmente falhou porque `pip freeze` omitia setuptools/wheel de bootstrap e `bdist_wheel` não existia no venv novo. **Corrigido**: ambos foram fixados no lock/build-system; reinstalação sem isolamento e testes repetidos passaram. Não ocultar esse erro nem chamar a primeira tentativa de PASS.

## Reprodução

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_repository.py
.venv/bin/python -m pip check
.venv/bin/lia-lab validate-data tests/fixtures/pilot.jsonl
```

Após editar fontes/docs/configs, regenerar o manifest com `--write-manifest` e repetir sem flag. O verificador inclui a si próprio e todos os arquivos mantidos de fonte, docs, configs, skills, perfis, testes e CI; exclui apenas o próprio manifest, Git, caches, metadata instalada/config local e artefatos ML. Validar hashes não constitui revisão legal ou prova de qualidade do conteúdo.

## NOT-TESTED / não realizado

- Treinamento SFT/LoRA/QLoRA, Transformers/PEFT/TRL, carga de modelo/tokenizer/processor, gradientes/kernels, PEFT save/reload e equivalência após merge/quantização: sem pesos adquiridos nem GPU/autorização de execução.
- Inferência real, baseline de qualidade Lia, pt-BR/persona/tools end-to-end com modelo, métricas humanas e benchmarks de jogos/voz/visão: fixtures não substituem essas avaliações.
- GPU CUDA/ROCm/Vulkan, hardware atual do usuário, Windows/macOS e instalação em outras versões Python: não acessados/executados.
- Invocação real dos sete agentes Codex, descoberta automática de skills no Arena e concorrência de agentes: não há ferramenta de delegação exposta; somente sintaxe/referências locais verificadas.
- Workflow GitHub Actions remoto: arquivo criado e YAML parseado; execução remota deve ser consultada no PR, não inferida do sucesso local.
- Revalidação de cada permalink AIRI, testes runtime AIRI/Lia e integrações Discord/Minecraft/Factorio: pesquisa estática anterior preservada, sem execução nesta entrega.
- Auditoria automática de PII, near-dedup semântico, esquema multimodal e verificação de consentimentos reais: não implementados. Curador continua responsável; valores de atestação não autorizam dados.

## Custos, dados e aprovação

Nenhuma GPU/API paga provisionada; nenhum checkpoint ou corpus grande baixado; nenhum dado pessoal/conversa/áudio usado; nenhum adapter/modelo/dataset de produção publicado. Houve apenas download de dependências pequenas de software, incluindo NumPy (~17 MB de wheel), parsers, testes e ferramentas de build. Root de pesquisa e root de modelos aprovados permanecem separados; export/registro não promovem um modelo à aplicação. Aprovação de modelo-base, persona/dados, direitos de voz, teto de GPU/download e distribuição continuam pendentes.
