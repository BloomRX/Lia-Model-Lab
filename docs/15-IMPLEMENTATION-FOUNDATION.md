# 15 — Fundação técnica offline

Estado: **implementado e exercitado com fixtures sintéticas**, não pipeline de treinamento validado. Python >=3.11. Sem Torch, rede, modelo carregado, serviços pagos ou execução de ações externas.

## Instalar e verificar

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_repository.py
```

No Windows, usar `.venv\Scripts\python.exe` e `pip.exe`. Essa plataforma **não foi executada** aqui. O lock registra versões do ambiente CPU desta entrega; wheels/driver/kernels de ML precisam de lock próprio por backend. Nenhuma compatibilidade Qwen/Gemma é inferida dessas dependências.

## Dataset Factory v1

[Schema canônico](../src/lia_lab/schemas/example.schema.json), implementação em `src/lia_lab/datasets.py`. Texto e tool trajectories, JSONL, `schema_version: 1`; `id`, `group_id`, idioma pt-BR, capacidades, proveniência, privacidade e mensagens. Tool calls têm IDs únicos e resultados obrigatórios antes da continuação. Geração sintética exige identificação do gerador; dados pessoais exigem referência de consentimento, **não** o documento pessoal no Git.

```sh
.venv/bin/lia-lab validate-data tests/fixtures/pilot.jsonl
.venv/bin/lia-lab build-data tests/fixtures/pilot.jsonl /home/user/lia-research/dataset-fixture-v1 --seed 42
.venv/bin/lia-lab verify-data /home/user/lia-research/dataset-fixture-v1/manifest.json
```

Fixture manuscrita, fictícia, CC0-1.0 somente para testes de software; não é dataset de produção nem representa a persona aprovada. Card em [fixtures](../tests/fixtures/README.md).

Validação ocorre antes da escrita. Output exige novo diretório, sem overwrite. Dedup exato de mensagens normalizadas NFKC/whitespace; argumentos das tools preservados. Grupos ligados por duplicatas são unidos **antes** da remoção, para não separar diálogos ligados em splits diferentes. Split determinístico com seed, ~80/10/10 por grupo (não por linha), mínimo três grupos independentes. Manifest inclui source hash, algoritmo, lineage, IDs removidos, contagens e hashes de train/validation/test. `verify-data` revalida schema, hashes, contagens, IDs, grupos e conteúdo entre splits. O arquivo `manifest.json` só aparece ao concluir; output parcial sem manifest não é promovível e deve ser descartado/reconstruído sob novo diretório.

**Limites:** piloto em memória, entrada <=16 MiB/10.000 linhas; não dedup semântico/MinHash, não redaction automática, não comprovação de direitos por software. Flags `rights_reviewed`/`reviewed` são atestações do curador, não autorização criada pelo CLI. Mídia e máscaras de loss/chat-template precisam de outro incremento; o schema v1 rejeita campos multimodais em vez de fingir cobertura.

## Plano de SFT e registro

[Template](../configs/sft-pilot.template.yaml) é deliberadamente incompleto e deve falhar antes de artefatos reais revisados. Não preencher hashes/revisions com números inventados para “passar”. Exigir base/tokenizer commits imutáveis, hash dos pesos e template, licença revisada, dataset manifest verificável, módulos LoRA inspecionados, seed, hparams, precisão, backend, dependências exatas, hardware/driver e teto de custo/tempo.

```sh
# Somente após preencher uma configuração local real, não o template PENDING:
.venv/bin/lia-lab register-plan /caminho/plan.yaml \
  --research-root /home/user/lia-research \
  --approved-root /home/user/lia-approved-models
```

Raízes precisam ser disjuntas; nenhum caminho dentro da pasta aprovada é escrito. Config e ambiente **planejados** são separados do ambiente **observado do planejador**. Registro conserva hashes de config/dataset e commit de código, estado git_dirty, snapshot hash do código presente e hash do lock, sem sobrescrever ID. Um checkout sujo não é apresentado como idêntico ao HEAD; isso continua plano, não prova de treinamento reproduzido. `status=planned`, `training_executed=false`, duração/custo reais null. `authorization_ref=null` não impede planejar e não autoriza executar. O software não tem comando de iniciar treinamento. Uma integração Transformers/PEFT/TRL virá após probe autorizado da base/processor, preparação da loss e backend; não é honesto implementar um “treinador universal” sem esses gates.

`verify-resume RECORD CHECKPOINT_MANIFEST` exige hashes de adapter, optimizer, scheduler e RNG, mais config/data/código/lock compatíveis; somente verifica metadados/arquivos, **não retoma** job. Não salvar optimizer como pickle no Git. Treinador futuro define checkpoint e revisão do ambiente original; não aceitar mudanças silenciosas de config após uma rodada.

## Avaliação inicial e comparação

```sh
.venv/bin/lia-lab compare tests/fixtures/base.json tests/fixtures/adapter.json \
  tests/fixtures/adapter-quantized.json --output /home/user/lia-research/fixture-comparison.json
```

Recebe **predições pré-calculadas**, com test hash, base revision, hash de artefato, protocolo/seed/template/budget, ambiente e evidência de origem. Rejeita variantes ausentes, IDs faltantes/duplicados, gabaritos divergentes e protocolo diferente. Reporta exact-match e regressões por capacidade, sem gate agregado que esconda perdas. Não executa inferência nem avalia personalidade, qualidade humana ou latência. Fixtures contêm hashes/identidades **fictícios declarados**, não resultados de modelos. Harness local preparado em [16](16-REAL-INFERENCE-PILOT.md), ainda sem checkpoint real; integração com o contrato pareado de compare e splits selados permanece gate; [09](09-BENCHMARK-STRATEGY.md) define o protocolo mais amplo.

## Exportação local de adapters

`inspect-adapter DIR` verifica `adapter_config.json`, `adapter_model.safetensors` pelo parser real safetensors e `provenance.json` (base_id/revision/base_weights hash). Verifica matrizes A/B pareadas, rank, tipos de arquivo/caminhos e hashes. Não executa código/pickle. `export-adapter SOURCE DEST` copia somente esses três artefatos para diretório novo e verifica hashes; produz export-manifest com status estrutural. Não faz merge, quantização, upload ou promoção à aplicação.

Não foram produzidos/exportados adapters treinados; os testes criam matrizes minúsculas de zeros em diretórios temporários. Formas e hashes não provam compatibilidade com a base ou equivalência de inferência: PEFT save/load, reload com base exata, logits/tarefas e licença continuam NOT-TESTED até probe real. Shards, DoRA, multimodal/experts e formatos fora deste contrato são fora de escopo.

## Governança e próximos incrementos

Templates [dataset card](../templates/DATASET-CARD.md), [model card](../templates/MODEL-CARD.md), [experimento](../templates/EXPERIMENTO.md) e [avaliação](../templates/AVALIACAO.md) continuam obrigatórios. Nenhum campo pendente deve receber aprovação falsa. Separar atestação humana, validação estrutural, execução de modelo e aprovação de distribuição.

Incremento implementado em [16](16-REAL-INFERENCE-PILOT.md): renderer com gate de generation spans e supervisor/worker de inferência local; ambos ainda sem tokenizer/checkpoint real testado. Próximos gates: probe LoRA/QLoRA save/reload; treinador SFT específico para arquitetura/processor; near-dedup auditável e mídia. Cada incremento tem orçamento/gate próprio, sem bloquear manutenção local do laboratório.

## Cards gerados como rascunho

`lia-lab write-card dataset MANIFEST OUTPUT.md` revalida hashes/splits e gera contagens e identidade do dataset. `lia-lab write-card model ADAPTER_DIR OUTPUT.md` inspeciona adapter e gera linhagem/hashes. Ambos usam criação exclusiva, sem sobrescrever card existente, e marcam revisão de direitos, avaliação, consentimento e release como PENDING. Isso complementa os templates, não substitui a revisão humana nem fabrica aprovação.
