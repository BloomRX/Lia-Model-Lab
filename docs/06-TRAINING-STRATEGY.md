# 06 — Estratégia de criação dos pesos

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Caminho inicial recomendado, condicionado a Gate 0

Base instruction-tuned aberta → baseline congelado → dados licenciados e split selado → SFT LoRA (BF16) ou QLoRA (NF4, base congelada) → avaliação → adapter → merge opcional com cópia limpa da base → avaliação de equivalência → quantização de inferência → regressão → model card/publicação **após aprovação**.

Não executar nesta missão. Começar 0.8B como teste de pipeline e 4B como hipótese de primeiro candidato útil; 27B não é requisito para gerar primeiros pesos. Referência técnica: PEFT, TRL e frameworks em [SOURCES](SOURCES.md). Templates existentes continuam obrigatórios.

| Técnica | Benefício | Uso recomendado / impedimento |
|---|---|---|
| SFT | Ensinar comportamento por exemplos | Primeiro experimento persona/pt-BR/tools; não ensina API funcional sem executor |
| LoRA | Poucos parâmetros treinados, base congelada | Referência BF16 quando memória permitir; targets mapear por arquitetura |
| QLoRA | Base 4-bit congelada + adapter | Comparar com LoRA mantendo dados/budget; kernels e precisão são riscos |
| Full FT | Atualiza toda base | Adiar: memória/optimizer/custo e esquecimento maiores |
| Continued pretraining | Adaptar distribuição/domínio | Só se corpus licenciado e erro de domínio justificarem; não etapa automática |
| DPO / preference optimization | Escolhas de estilo/comportamento | Após SFT; pares independentes, desacordo e anti-bajulação; não substituir dados factuais |
| Distillation | Reduzir latência/tamanho | Teacher/data terms, fidelidade e retenção de capacidade antes de adotar |
| Multimodal FT | Grounding e associação de modalidades | Baseline visual primeiro; congelar encoder inicialmente, testar alinhamento/processor |
| Tool-use training | Escolha/args/feedback/erros | Trajetórias executáveis e casos sem ferramenta; máscara de loss não treina tool result como fala Lia |
| RL (PPO/GRPO etc.) | Otimizar retorno verificável | Só jogo/sandbox com reward robusto, seeds holdout e prevenção de reward hacking; não RL em desktop do usuário |

## Artefatos distintos e reprodutibilidade

1. **Base original:** id+commit+hash, config, tokenizer/processor/template, licença. Nunca sobrescrever.
2. **Base QLoRA:** representação quantizada no treino, método/versionamento NF4/double quant, dtype de compute; não é novo master treinado.
3. **Adapter:** matrizes treinadas + adapter_config; exige base exata e não contém toda capacidade da base.
4. **Merged master:** base limpa de alta precisão + adapter; comparar logits/tarefas com adapter aplicado. Merge de adapters diferentes não é comutativo em geral nem garantia de qualidade.
5. **Quantizado de inferência:** GGUF Q8/Q6/Q5/Q4 ou formato realmente suportado; calibração separada do test. Não equiparar NF4 de treino a GGUF Q4.

Registrar em manifest externo: parents hashes, git commit, dados/hashes/splits, seed, framework/container/driver, target modules/trainable count, optimizer/scheduler, sequence length, batch/accumulation, packing, loss masks, LR, rank/alpha/dropout, checkpoints/RNG/scheduler states e logs redigidos. Checkpoint final sozinho não reproduz retomada. Licenças e notices acompanham todos os derivados.

## Experimentos e ablações propostos

- E0: load/forward/backward/save/reload do candidato exato; abortar em gradientes NaN, módulos treináveis inesperados ou license gate falho.
- E1: prompt-only vs SFT persona+pt-BR; evitar atribuir ganho ao prompt alterado.
- E2: LoRA vs QLoRA com mesma base/dados/seeds/budget. Grid inicial apenas proposto: rank 8/16, LR 1e-5–1e-4, 1–3 épocas, 2K tokens, microbatch 1; ajustar por validação, não test. Não confundir esses números com prescrição aprovada.
- E3: mistura geral+persona vs persona isolada; avaliar repetição e esquecimento. Só então tool/memory/social, com replay e ablação.
- E4: visão/jogo em experimentos separados; não declarar nova modalidade de base textual sem arquitetura/alinhamento.
- E5: quantização comparada ao master não quantizado.

Early stopping por validação, limite de steps/custo aprovado e checkpoint periódico. Preservar último bom estado e cancelar em regressões de segurança. Nenhuma busca de hyperparams no test selado.

## Precisão e quantização

BF16 é referência quando hardware/arquitetura suportam. FP16 só com checagem de range, loss scaling e equivalência; não converter cegamente bases BF16. 8-bit favorece fidelidade/memória; 6/5-bit equilibram footprint; 4-bit reduz memória com risco de perda em tools, grounding, pt-BR e persona. Avaliar cada um, não assumir monotonicidade da qualidade.

Relatar tamanho real, RAM/VRAM pico, TTFT, tokens/s, contexto e perda por suite para **base original → adaptado → merged opcional → cada quantizado**. Uma variante que falha grounding ou permissões não pode ser liberada por ter conversa melhor. Quantizar após treino não dispensa testar a base quantizada usada em QLoRA como condição de treino separada.
