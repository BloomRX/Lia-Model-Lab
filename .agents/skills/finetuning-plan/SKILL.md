---
name: finetuning-plan
description: Plan SFT, LoRA, QLoRA and fine-tuning resources without executing jobs.
---

# finetuning plan

Read docs/05-PLANO-DE-TREINAMENTO.md, docs/08-INFRAESTRUTURA-E-OPERACAO.md and docs/13-GOVERNANCA-DE-EXPERIMENTOS.md. Define target behavior, hypothesis, baseline and stop criteria. Pin base revision, tokenizer, chat template, license and framework support. Compare full fine-tuning, LoRA and QLoRA; distinguish inference quantization from training quantization. Estimate memory for weights, gradients, optimizer, activations, context, batch and overhead with explicit assumptions. Plan a small licensed/synthetic pilot, validation, seed, resumable checkpoints, sanitized logs and adapter export. Record cost ceiling and regression gates. Output an unexecuted plan. Do not install, download large weights, provision paid GPUs or start training without explicit approval.
