# ADR-0006 — Contrato fixo do piloto Qwen3.5-0.8B em CPU

Data: 2026-11-02. Estado: **implementado e validado com headers, configuração meta, frontend original e pesos sintéticos; inferência original NOT-TESTED**. Não aprova base, licença humana, orçamento, execução ou release. Complementa ADRs 0003–0005 sem alterar seus gates.

## Contexto

PR #4 integrada em `3ec4313ba57ec94a7f3d93ec4f7a0d533d5077cf` por solicitação do proprietário. O contrato anterior recusava sizing Qwen3.5 desconhecido. O pedido do primeiro piloto autoriza aquisição pública e stack CPU, mas exige contabilizar arquitetura completa, sem export texto-only ou fallback por tamanho de arquivo.

## Decisão

Suportar exclusivamente o config canônico SHA-256 `7755fa7f94c366b1bc8db482e9a3c56721093ece9ed6a8234560e443b13168d1` da revisão `2fc06364715b967f1860aea9cf38778875588b17` de `Qwen/Qwen3.5-0.8B`. Equações independentes enumeram texto híbrido, visão e MTP; nomes, shapes, dtypes e índice devem coincidir exatamente. Config diferente continua desconhecido; nenhum fallback estima parâmetros pelos bytes armazenados.

Há 488 tensores serializados e 873438784 elementos: 452 BF16 e 36 F32. Todos, inclusive visão e auxiliares, entram no sizing float32. O envelope anterior é preservado: `elements * 4 * 3 // 2 + snapshot_bytes + 1 GiB = 8084353423 bytes`. A margem da política é aplicada à disponibilidade, sem mudar o envelope.

Transformers 5.22.1 oficial usa `AutoModelForMultimodalLM` / `Qwen3_5ForConditionalGeneration`, frontend `AutoProcessor` / `Qwen3VLProcessor`. O processor seleciona `chat_template` próprio/default; não possui a API tokenizer `get_chat_template`. Nenhum template alternativo é inventado. Texto é entregue ao processor em conteúdo multimodal tipado; imagem/vídeo não são exercitados pelo piloto textual.

O loader oficial filtra `mtp.*` e não materializa nem executa MTP. A integração preserva explicitamente os **15 tensores auxiliares exatos** como Parameters congelados em submódulo de armazenamento, após validar o core oficial; não muda classe ou forward e não implementa geração MTP. Isso consome memória e é declarado no contrato da operação (`verified-frozen-mtp-storage-no-mtp-generation-v1`). Não se ignora prefixo genérico: tensor adicional, dtype/shape diferente ou submódulo preexistente bloqueia. Teste sintético verifica inclusive valor não zero restaurado. O parâmetro `lm_head.weight` só pode faltar na serialização se for o mesmo objeto Parameter do embedding em runtime, não apenas numericamente igual.

Relatórios de loading exigem missing/unexpected/mismatched/error vazios, exceto alias tied comprovado. Diagnóstico adicional não vazio bloqueia. Depois da restauração auxiliar, o state completo deve corresponder ao inventário, descontado somente o alias. O funcionamento com pesos originais permanece sem prova até execução autorizada.

## Identidade e gates

Lock CPU separado, `requirements-ml-windows-cpu.lock`, fixa todas as versões e URLs oficiais CPU de Torch/torchvision com SHA-256. Base/API locks permanecem independentes. Plano e worker vinculam config/arquitetura/política auxiliar, executável/versão Python, versões instaladas, hash do lock e hashes das fontes críticas instaladas. Qwen3.5 exige lock exato, Torch CPU sem CUDA/HIP, CPU/float32 e TF 5.22.1. Mudanças invalidam a operação aprovada. Não se importa ML nem se acessa rede para obter essa identidade.

Aquisição é script explícito separado, público/sem credenciais e sem efeitos em import. Verifica revisão, licença declarada, inventário, tamanho e hashes; staging externo permite retomada com Range validado, sem overwrite de snapshot existente. Não sela nem concede aprovação.

## Consequências e evidência

[Relatório do piloto](../19-QWEN35-FIRST-PILOT.md) contém aquisição, sizing, runtime, resultados e comandos humanos. Configuração meta confirma shapes e alias sem carregar pesos. Pesos sintéticos pequenos exercitam loader real e restauração. Frontend original prepara os cinco casos sem geração. Isso é AUTOMATED-PASS para conformance; não é RUNTIME-PASS do checkpoint original. RAM insuficiente, revisão humana pendente e grant ausente impedem o piloto real nesta sessão. Job Objects continuam sem isolamento completo e sem autorização própria.
