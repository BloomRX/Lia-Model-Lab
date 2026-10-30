# Validação atual — hardening v0.4.0

Data: 2026-10-30. Partida: `2cb652353e1429ae75dd647e824edc107019babd`, PR #1 OPEN e main não integrada. Antes de editar, comparação byte a byte do snapshot com o remoto, alinhamento do HEAD/index restaurados e execução dos **84 testes anteriores PASS**. Nenhum trabalho recente remoto sobrescrito; sem force push/merge.

## Executado

| Procedimento real | Resultado e alcance |
|---|---|
| Suíte base `.venv/bin/python -m pytest -q` | **143 passed, 1 skipped**. Skip é o módulo TF opcional, executado no ambiente abaixo; não é inferência faltante mascarada |
| Ambiente separado `.cache/api/.venv`, lock requirements-api.lock | **151 passed**, com **Transformers5.22.1 real e sem Torch**. Config/registry/API Jinja/tokenizer WordLevel próprio, não tokenizer/modelo Qwen |
| `pip check` em ambos os ambientes | Sem dependências quebradas; conflito safetensors corrigido para0.8.0 |
| Compilação `python -m compileall -q src scripts` | PASS |
| CLI doctor/help e recusa approve-inference não interativo | Executados/testados, sem criar grant real |
| Autorizações em testes | Stores temporários de checkpoint fictício, confirmação TTY simulada declarada, limites/modelo/revision/hash/suite/código/paths/ação, expiração/futuro/TTL, concorrência, consumo, worker claim, finalização e replay. Nenhuma autorização operacional real |
| Backend em testes | Mocks de Auto classes, frontend, from_pretrained/offline/dtype, processor textual, contexto, output slicing/EOS, texto vazio, tools opacas; mocks não comprovam pesos |
| API real HF5.22.1 | AutoConfig e mappings; assistant_masks, multi-turn, tool calls/retornos, EOS e spans ruins com tokenizer original. Nenhum forward/backward/modelo instanciado |
| Processo real sem Torch | Worker com grant sintético falha por dependência; worker sem grant recusa mesmo com flags offline. Nenhum resultado de linguagem gerado |
| Linux recursos/rede | RLIMITs aplicados/consultados em Python descartável; unshare user/net aplicado e inode diferente confirmado neste host. Timeout real de filho descartável testado. Não teste de proteção de Windows/macOS/GPU nem sandbox completo |
| Resultados/falhas | Stubs sintéticos testam completed, incomplete, failed, timed-out, interrupted, parciais, hash/model/order divergentes, respostas vazias, JSON/listas corruptos e não sobrescrever ID. São contratos, não métricas de modelo |
| Verificador e manifest | JSON/YAML/TOML/frontmatter/schema, links locais, cobertura/bytes/SHA, perfis/skills e symlinks realmente verificados; regenerado e repetido sem flag. Contagens finais no output do verificador/PR |
| Marca e whitespace | BRAND-STANDARDS igual à main consultada; git diff --check limpo |

Correções decorrentes de falhas reais durante desenvolvimento: pin safetensors antigo não satisfazia TF5.22.1; máscara nativa com whitespace final podia incluir tool/user posterior; gate antigo de falha sem Torch precisou exigir grant sintético antes de alcançar import, mantendo também teste explícito de recusa sem grant. Teste do próprio verificador detectou link de evidência ainda não criado durante a edição; artefato foi criado e testes repetidos. Não ocultar esses resultados intermediários como PASS.

## Reprodução sem pesos

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_repository.py
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src scripts
.venv/bin/lia-lab doctor

# Ambiente API separado: somente libs pequenas, sem Torch/modelos/tokenizers upstream.
python -m venv .cache/api/.venv
.cache/api/.venv/bin/pip install -r requirements-api.lock
.cache/api/.venv/bin/pip install --no-build-isolation --no-deps -e .
.cache/api/.venv/bin/python -m pytest -q
.cache/api/.venv/bin/python -m pip check
```

CI tem jobs separados base e lightweight-api; ambos não adquirem pesos. Estado remoto deve ser consultado no HEAD final, não inferido dos testes locais. Em CI com user namespaces proibidos, teste verifica recusa explícita, não registra namespace aplicado. Regenerar manifest após últimas edições; verificador não valida anchors Markdown, todas as URLs externas nem autenticidade/legalidade de conteúdo por hashes.

## NOT-TESTED / desconhecido

- Config.json, LICENSE, revision, tokenizer_config, template e geração originais dos checkpoints: hosts de pesos fora da allowlist. Fonte oficial de código/tests não substitui artefato exato. Qwen3.5-0.8B é citado por teste slow upstream, **não rodado**; para0.6B o teste consultado é **-Base**, não post-trained.
- Inferência real, qualidade pt-BR/persona/tools, RAM/VRAM/latência/throughput de modelo: nenhum checkpoint, runtime Torch ou GPU. Todos sem resultado real; não há modelo Lia aprovado.
- Processor Qwen completo com seus componentes, dtype/kernels/driver CUDA/ROCm/MPS/CPU com pesos, proteção em Windows/macOS/AMD/GPU e robustez contra conteúdo hostil: sem execução específica. RLIMIT/namespace não provam segurança de modelos.
- PEFT, forward/backward, treinamento, reload/merge/quant/export equivalentes e melhoria mensurável de adapter: não realizados. Renderer validado com API leve não aprova template Qwen real ou dados/persona.
- Revalidação/execução upstream AIRI e descoberta/delegação real de agentes: não realizadas; fallback sequencial, sem revisão independente simulada.

## Custos e governança

Zero pesos/datasets externos adquiridos, zero GPU/API paga, zero dados pessoais, zero licença aceita, zero publicação de pesos/datasets/adapters. Somente dependências pequenas de desenvolvimento/API foram instaladas. Grants dos testes são fictícios/temporários; operador humano deve confirmar uma operação real em terminal próprio e store externo. JSON/SQLite/TTY não autenticam identidade criptográfica; código/relógio/host e conta local são fronteiras de confiança.

[Guia atual](16-REAL-INFERENCE-PILOT.md), [ADR](adr/0003-INFERENCE-HARDENING.md), [evidência](evidence/hardening-validation.json). Histórico de relatórios permanece no Git, sem coleções documentais paralelas.
