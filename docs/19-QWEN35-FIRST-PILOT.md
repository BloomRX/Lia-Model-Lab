# 19 — Primeiro piloto Qwen3.5-0.8B

Estado: **Resultado B — preparação validada; piloto real bloqueado**. PR #4 integrada em `3ec4313ba57ec94a7f3d93ec4f7a0d533d5077cf`; branch `codex/qwen35-first-pilot`. Nenhum checkpoint-base é promovido a Lia Core ou release por esta preparação.

## Aquisição e revisão documental de licença

Modelo post-trained oficial: `Qwen/Qwen3.5-0.8B`, revisão imutável `2fc06364715b967f1860aea9cf38778875588b17`. [Árvore da revisão](https://huggingface.co/Qwen/Qwen3.5-0.8B/tree/2fc06364715b967f1860aea9cf38778875588b17), [card](https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/2fc06364715b967f1860aea9cf38778875588b17/README.md), [LICENSE integral](https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/2fc06364715b967f1860aea9cf38778875588b17/LICENSE). API upstream declarou público/não gated e licença apache-2.0; o texto integral foi obtido e examinado, identificando Apache License 2.0 e copyright Alibaba Cloud 2026. SHA-256 dos bytes originais de LICENSE: `bbedc3fda3305820b977265f01b8619d87570a6739de3a5582c3464840f1e57a`. Hash não é parecer jurídico nem autorização operacional.

Foram adquiridos/verificados 12 arquivos oficiais, 1769978895 bytes, fora do Git, na pasta externa `J:\Lia-Model-Storage\Qwen\Qwen3.5-0.8B\2fc06364715b967f1860aea9cf38778875588b17`. O único arquivo não adquirido do inventário foi `.gitattributes`, sem função de runtime. SHA-256 LFS foi comparado para pesos/tokenizer.json e identidade Git blob SHA-1 para os demais, além de SHA-256 local de todos. Manifesto de aquisição fica fora do snapshot e não substitui `seal-model`.

Obrigações a considerar pelo proprietário: conservar a licença e atribuições; indicar alterações em arquivos modificados; conservar avisos pertinentes e NOTICE quando distribuído; observar cláusula de patentes, ausência de garantia e limites de responsabilidade. Direitos de marca não são concedidos pela licença dos pesos. Nesta revisão exata, nenhum NOTICE separado foi listado; não se presume isso para outras revisões/artefatos. Não houve divergência observada entre card e LICENSE. Não houve aceite de termos gated, redistribuição ou publicação de pesos. Licenças do código/dependências, base, dados, voz/assets e marca continuam categorias distintas.

**Revisão humana: PENDENTE. `license-review-ref`: null.** Este documento é levantamento do agente para o proprietário revisar. Não atesta que o proprietário examinou/aprovou a licença, não pode servir sozinho como referência humana e não libera seal/execução. A confirmação e a referência real devem vir do responsável; o agente não as fabrica.

## Gates preservados

Plano e execução usarão CPU/float32, best-effort com margens padrão, suite oficial, repeats 2, max tokens 128, contexto 2048, timeout 1800 s e launcher Windows obrigatório. Grant externo/humano/temporário/de uso único permanece obrigatório; nenhum foi criado. Aquisição não autoriza carregar pesos nem gerar respostas. Sem treino, adapter, allowlist nova ou trust_remote_code.

O diagnóstico inicial observou cerca de 2,2 GiB de RAM disponível. A evidência final recolhe novamente a memória e aplica o envelope completo. Não foram fechados aplicativos externos nem reduzidas margens para forçar o preflight.

## Arquitetura e runtime verificadas

[ADR-0006](adr/0006-QWEN35-PINNED-CPU-PILOT.md) registra o contrato fixo e a preservação explícita dos 15 tensores MTP, sem geração MTP. O inventário de [12 arquivos](../configs/qwen35-acquisition.json) inclui todos os pesos, config, tokenizer, processor e template. `generation_config.json` e NOTICE não existem nessa revisão; não foram inventados. O template original tem SHA-256 `273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80`.

488 tensores, 873438784 elementos, 452 BF16 e 36 F32; 1746882752 bytes de payload. Texto, visão e MTP estão cobertos pelas equações. Pesos residentes float32: 3493755136 bytes. Envelope conservador inalterado: **8084353423 bytes / 7,53 GiB**. Com visibilidade parcial do Job e margens 10% + 10%, requer pelo menos 10105441779 bytes disponíveis na dimensão física (9,41 GiB); não é uma reserva nem garantia de alocação. O cap máximo proposto do Job seria o envelope, nunca limite aplicado nesta sessão. Cap aplicado e pico de inferência são null.

Ambiente ML externo: `J:\Lia-Model-Lab-Environments\qwen35-cpu`; Python 3.11.0 x64, Torch 2.14.0+cpu, torchvision 0.29.2+cpu, Transformers 5.22.1. [Lock separado](../requirements-ml-windows-cpu.lock) fixa 47 dependências; wheels CPU oficiais com SHA-256, sem alterar locks base/API. CUDA e HIP do build são null; backend CPU/eager/float32, sem quantização, sem kernels remotos. Nenhum download/instalação ocorre por import, testes padrão ou CLI.

O tag oficial Transformers v5.22.1 resolve a `446a570e62b04a89ea001604ada7366baac2ea67`; os bytes instalados de modeling_qwen3_5.py, configuration_qwen3_5.py e modeling_auto.py foram comparados com esse commit. [Evidência sanitizada](evidence/qwen35-first-pilot.json) registra hashes e memória. Classe concreta `Qwen3_5ForConditionalGeneration`, AutoModelForMultimodalLM, Qwen3VLProcessor/Qwen3_5Tokenizer. O vision_config legado é normalizado pela AutoConfig oficial; não se modifica o config original.

Ryzen 5 5500, 6 núcleos/12 threads, 17063882752 bytes de RAM física. RX 580 2048SP apareceu no inventário Windows; não houve prova de runtime GPU nem instalação de ROCm/CUDA. A matriz AMD consultada para Windows não lista essa placa. CPU é o único caminho preparado. Vulkan/llama.cpp/GGUF são alternativas futuras, sem backend/binaries/checkpoint adquiridos ou benchmark nesta sessão.

## Evidência e diagnóstico

Teste do contrato e aquisição: 32 passed, 1 skipped (symlink Windows requer privilégio). Quatro testes opt-in CPU passaram: loader oficial com pesos sintéticos pequenos e valor MTP não zero; rejeição de alias untied; processor/tokenizer/template originais nos cinco casos da suite sem geração; modelo oficial em device meta com shapes/tied identity. O device meta não aloca pesos originais. Testes padrão não dependem do snapshot nem importam Torch. Revisão realizada pelo principal, sem delegação ou revisores independentes simulados.

O diagnóstico com orçamento, registrado em JSON, bloqueia por RAM física depois das margens. `doctor` sem required_bytes pode reportar allowed=true para qualidade das observações: isso não significa que o modelo caiba. Não foi invocado infer-local com grant fictício para obter um erro. Nenhum manifesto de seal ou plano operacional real foi produzido sem revisão humana; nenhum grant foi criado/consumido.

Requests reais concluídos: **0**. Respostas: `[]`. Tempos de loading/geração, throughput, picos, qualidade pt-BR, JSON/tools e avaliação pareada: **NOT-TESTED**, pois os pesos originais não foram carregados. Conformance não prova qualidade, tools executadas, memória pessoal ou visão. Treino, adapters, export/quantização, PEFT e release não foram executados/aprovados. Custo externo pago USD 0; HF público e índices oficiais de dependências usados apenas para aquisição gratuita. Total de bytes de dependências não foi medido; 1769978895 bytes de arquivos do snapshot foram adquiridos, com possível tráfego adicional de retomadas/metadados não medido.

## Continuação exata pelo responsável

Primeiro obter recursos suficientes e uma revisão humana real da LICENSE. Não gerar grant enquanto o orçamento não couber; tentativas bloqueadas também consomem grant. A aquisição não concede esses gates. PowerShell no checkout, usando o ambiente fixado:

```powershell
$Py = 'J:\Lia-Model-Lab-Environments\qwen35-cpu\Scripts\python.exe'
$Snapshot = 'J:\Lia-Model-Storage\Qwen\Qwen3.5-0.8B\2fc06364715b967f1860aea9cf38778875588b17'
$Manifest = 'J:\Lia-Model-Storage\manifests\qwen35-0.8b-2fc0636.json'
$Plan = 'J:\Lia-Research\qwen35-0.8b-text-001.plan.json'
$ReviewRef = Read-Host 'Referencia real da revisao humana da LICENSE'
if ([string]::IsNullOrWhiteSpace($ReviewRef) -or $ReviewRef.StartsWith('PENDING')) { throw 'Revisao humana ausente' }
& $Py -m lia_lab.cli seal-model $Snapshot $Manifest --model-id Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --license-id Apache-2.0 --license-file LICENSE --license-review-ref $ReviewRef
if ($LASTEXITCODE -ne 0) { throw 'Seal falhou; investigar sem sobrescrever manifestos' }
$Common = @('--snapshot', $Snapshot, '--snapshot-manifest', $Manifest,
  '--suite', 'configs/inference-suite.json', '--research-root', 'J:\Lia-Research',
  '--approved-root', 'J:\Lia-Approved-Models', '--run-id', 'qwen35-0.8b-text-001',
  '--device', 'cpu', '--dtype', 'float32', '--containment', 'portable-process',
  '--memory-policy', 'best-effort', '--memory-margin-percent', '10',
  '--memory-uncertainty-margin-percent', '10', '--repeats', '2',
  '--max-tokens', '128', '--context', '2048', '--timeout', '1800')
& $Py -m lia_lab.cli plan-inference @Common --output $Plan
if ($LASTEXITCODE -ne 0) { throw 'Plano falhou' }
```

O responsável revisa a operação completa, prepara seu diretório externo/ACL do store e, **em terminal humano próprio**, executa a confirmação interativa. O agente não executou nem deve automatizar este passo:

```powershell
& $Py -m lia_lab.cli approve-inference $Plan --store 'J:\Lia-Operator\grants.db' --ttl 3600
# Confirmar a frase exata com o SHA da operacao, somente se aprovada.
```

Depois da confirmação humana, usar o ID real retornado, com os mesmos argumentos `$Common`, no mesmo ambiente/config/código; qualquer alteração exige novo plano/grant. O agente pode receber o ID e executar somente se recursos continuarem suficientes:

```powershell
$GrantId = Read-Host 'ID do grant real retornado pelo terminal humano'
& $Py -m lia_lab.cli infer-local @Common --approval-store 'J:\Lia-Operator\grants.db' --approval-id $GrantId
```

Não reutilizar run-id após tentativa nem sobrescrever evidências. Não aceitar o relatório atual como licença-review-ref fabricado. Caso recursos continuem insuficientes, manter Resultado B e planejar host autorizado maior; nenhum switch silencioso para 0.6B, GPU, quantização ou margens menores.
