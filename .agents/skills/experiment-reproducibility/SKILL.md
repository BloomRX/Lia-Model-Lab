---
name: experiment-reproducibility
description: Track manifests, exact revisions, hashes, seeds, environments, checkpoints and artifact storage.
---

# experiment reproducibility

Read docs/13-GOVERNANCA-DE-EXPERIMENTOS.md and templates/EXPERIMENTO.md. Record code commit, dependency versions, OS, driver, backend, GPU, CPU, RAM and storage. Pin model revision, tokenizer/template, quantization and hashes; pin dataset IDs, splits, transformations and manifest hashes. Record method, hyperparameters, seed, optimizer, precision and commands. Store artifacts outside Git with URI/path, checksum, checkpoint frequency and resume state. Distinguish fresh run, resumed run, dry-run and simulation. Record duration, costs, failures and config changes. Sanitize logs. Never commit weights, raw data, optimizer states, secrets or private logs.
