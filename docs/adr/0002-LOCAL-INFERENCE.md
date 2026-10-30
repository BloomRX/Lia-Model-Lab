# ADR-0002 — Inferência local verificável antes de SFT

Data: 2026-10-30. Estado: **implementado para revisão**, execução com checkpoint real BLOCKED. Não aprova aquisição de pesos, licença específica, gasto, treinamento ou release.

## Estado de partida verificado

PR #1 permanece OPEN, `merged=false`; `main=20f1883ad1671139d7c023eff42b72c6bca96525`, consolidação `30e9b2e2acb1f95c3a162188638bba006025b5aa`. CI anterior success em push/PR; suíte original executada: 44 testes PASS. Não foi feito merge na main. O snapshot restaurado tinha exatamente os bytes desse HEAD remoto mas HEAD/index antigos; comparação de cada arquivo contra o remoto precedeu o alinhamento mixed do histórico, sem sobrescrever conteúdo. Trabalho continua na única branch da sessão e PR #1, não em outra branch.

A fundação já implementava Dataset Factory, registro de **planos**, comparação de **predições fornecidas**, cards e export estrutural safetensors. Não carregava tokenizer/modelo, não gerava predições e não tinha trainer ou validação PEFT real. Esses componentes são reutilizados, não substituídos por cópias.

## Decisão de execução

1. Supervisor/registro separado do subprocesso de inferência. Requests/responses e manifest de snapshot local são fronteiras de backend, não dependem de avatar, produto AIRI ou runtime cognitivo.
2. **Transformers + PyTorch local-only** como implementação de referência: aproxima a futura stack de SFT e preserva template nativo. Escolha explícita cpu/cuda/rocm/mps; ROCm usa API `torch.cuda` mas valida `torch.version.hip`. Sem device_map automático/offload silencioso, sem dependência padrão de CUDA/bitsandbytes, sem instalar Torch ao importar o pacote.
3. Pesos somente safetensors revisados/localizados pelo operador, com revisão imutável e inventário de arquivos/tamanhos/hashes. Sem downloader. Rejeitar symlinks, código Python/pickle, snapshots incompletos, hashes alterados e quantização não implementada. Checksums locais são integridade, não assinatura de autenticidade upstream ou parecer jurídico.
4. `infer-local` exige referência de autorização humana, raízes pesquisa/aprovados disjuntas, novo ID, limites de contexto/tokens/repetições/tempo e RAM conservadora. O subprocesso falha de forma registrada se falta runtime/driver/template. Nunca promover a modelo aprovado nem chamar teste sintético de inferência real.
5. Casos originais, públicos, de engenharia e não treinamento; duas ou três rodadas, sem executar tool calls. Rubrica pt-BR humana, checks automáticos mínimos de instrução/JSON/contexto e envelope Qwen. Não são benchmark de qualidade ou prova de segurança de ferramentas.
6. **Qwen3.5-0.8B** recomendado para primeiro smoke da arquitetura híbrida, em ambiente com RAM suficiente; **Qwen3.5-4B** continua candidato de capacidade Core. Qwen3-0.6B é controle mais simples de texto. Nenhum download aprovado. No sandbox ~4 GB, até pequenos Transformers FP32 podem falhar no envelope; preferir ambiente maior ou futura implementação GGUF revisada, sem prometer que caberá.

## Alternativas e consequências

- **llama.cpp/GGUF:** excelente alternativa CPU/Vulkan/CUDA/HIP/Metal para poucos recursos, mas quant, conversão e projector são artefatos distintos. Documentado upstream para Qwen3.5, **não implementado nem testado neste CLI**. Não gerar métricas por parsing frágil de stdout nem fingir que engine externa já suporta o contrato.
- **vLLM/SGLang:** opção futura de throughput em servidor. Dependências/memória não justificadas para um piloto serial CPU.
- **MLX/JAX:** válidos em seus ambientes, sem instalar uma segunda stack nesta fase.
- **API externa:** manter futura fronteira de backend, mas sem chaves, rede, API paga ou efeitos remotos agora; serviços podem não expor hashes/tokenizer/memória.
- **bitsandbytes:** upstream já contempla vários provedores; isso não prova RX580/gfx803 nem qualquer wheel/kernel. Quantização é gate separado, não atalho para dizer QLoRA compatível.

## Gates SFT

Primeiro concluir baseline real e revisão humana. Depois inventário de módulos Linear realmente observado, targets revisados, template de treino com generation spans, assistant-only loss validada, dados aprovados sem prompts de avaliação, PEFT forward/backward/save/reload, orçamento e autorização. Renderer sem máscara nativa confiável deve falhar, não treinar todo o prompt. LoRA pequeno antes de QLoRA reduz variáveis. Melhoria exige comparação pareada e regressões, não apenas salvar um adapter.
