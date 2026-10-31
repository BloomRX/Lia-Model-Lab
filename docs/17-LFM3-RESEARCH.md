# 17 — Liquid AI LFM3: pesquisa, contratos e decisão de arquitetura

Consulta: **2026-10-31**. Estado: **research-only / license-review-required**. Nenhum peso, GGUF, tokenizer upstream ou dataset adquirido; nenhum código de checkpoint executado. Não é aprovação comercial nem parecer jurídico.

## 1. Evidência e limites da consulta

Fontes primárias efetivamente lidas, via API GitHub (metadados/código/documentação apenas):

- **D**: [Liquid4All/docs, commit 4a4f438](https://github.com/Liquid4All/docs/tree/4a4f438d736ff85f35d9ac128901cbb646d305d3): páginas dos seis modelos pós-treinados, link do Base, guia de licença, áudio, templates, tools e implantação llama.cpp.
- **C**: [cookbook, commit 3d0cbcb](https://github.com/Liquid4All/cookbook/tree/3d0cbcb7dc40b690e3e4996c5b78e4d3020f8232/finetuning/notebooks): seis notebooks SFT texto/VL/áudio/Omni/TTS/VQA lidos como JSON/texto, **não executados**.
- **L**: [llama.cpp b11960, commit 8642541](https://github.com/ggml-org/llama.cpp/tree/8642541b255bfb5dc39cd351a178be09013a55d6): árvore, conversor `conversion/lfm3.py`, template LFM3 e implementação de geração áudio consultados; não build/teste/auditoria integral.
- **F**: [liquid-finetune, commit d9cc23d](https://github.com/Liquid4All/liquid-finetune/tree/d9cc23dae5a16498ab7dc11958b80ca803e0440a): README/árvore; framework tem SFT/LoRA/VLM, mas isso não prova cada checkpoint.

As páginas de lançamento [Liquid](https://www.liquid.ai/blog/lfm3), [artigo HF](https://huggingface.co/blog/LiquidAI/lfm3), [Omni](https://docs.liquid.ai/lfm/models/lfm3-omni-2b), cards e LICENSE individuais no HF **não foram reconsultados**: hosts fora da allowlist. Não contornar restrição por proxy. Os IDs abaixo são referenciados pela documentação oficial D; isso confirma **referência oficial**, não acesso independente ao repositório/arquivos atuais. Revision de docs/código não é revision de checkpoint. Todos os inventários, hashes, NOTICE, configs, templates e licenças de artefato exato permanecem pendentes. No catálogo, K foi representado nominalmente como1024 tokens; sem config exata, esses números não são limites operacionais validados.

Não há benchmark independente incorporado nesta rodada nem resultado ML da Lia. Capacidades/contextos/tamanhos abaixo são **declarações do fabricante**; recomendações são **inferências técnicas condicionais**. Não transportar placares do fabricante para relatório de experimentos Lia.

## 2. Família, artefatos e shortlist por função

| ID original exato (LiquidAI/) | Declaração D | Papel / recomendação técnica, não aprovação |
|---|---|---|
| LFM3-1.7B | 1.73B; texto→texto; 256K entrada+saída; tri-hybrid 24 camadas: 13 gated short convolution, 5 sliding-window, 6 global attention | **Shortlist Core compacto pós-treinado**. Instruções/tools/saídas estruturadas. Fabricante desaconselha agentic coding e reasoning multi-etapa complexo; usar retrieval e escalonamento, não prometer Core universal |
| LFM3-1.7B-Base | Checkpoint pré-treinado oficialmente ligado em D; propriedades da família não substituem config Base | **Comparador de treinamento**, não chatbot pronto. Mais liberdade de comportamento, mas maior custo de alinhamento e regressões; post-trained é primeiro baseline mais econômico |
| LFM3-VL-2B | ~1.92B: 1.73B LM +164M encoder +25M projector; texto/imagem/vídeo→texto;128K | **Shortlist Lia Vision**. OCR/documentos/cenas, apontamento/grounding; desktop/jogo/pequenos textos e coordenadas exigem suite própria, não assumir agente de UI pronto |
| LFM3-Audio-2B | ~2B; texto/áudio16kHz→texto/fala24kHz/intercalado;32K; encoder causal + codec | **Shortlist Hearing/Speech**, avaliar ASR e TTS separadamente; understanding e conversa não equivalem a transcrição |
| LFM3-Omni-2B | 2.17B; texto/imagem/vídeo com soundtrack/áudio→texto/fala/intercalado;32K | **Ablação de integração**, não substituto automático de Core/especialistas. Não-reasoning; contrato proposto proíbe `enable_thinking=True` |
| d1-2B | 1.92B;128K; LFM3-VL; texto/imagem/vídeo→decisões tipadas em um forward, sem gerar tokens | **Shortlist decisões sem áudio**: classificação, extração, boxes, probabilidades. Não chatbot, ASR, TTS ou policy autorizada |
| d1-Omni-2B | 2.17B;128K; LFM3-Omni; texto/imagem/áudio→decisões tipadas | **Condicional à necessidade de áudio**: roteamento/sons/pergunta falada. Não gera transcrição, conversa nem fala. D recomenda d1-2B sem áudio e relata melhor calibração/texto/box simples nessa variante |

Não existe ranking único. Qwen3.5-0.8B (probe), Qwen3.5-4B (Core econômico), Qwen3.8-27B (comparador maior), Qwen3-0.6B (controle textual) e Gemma4 E2B/E4B/12B/26B A4B/31B continuam no catálogo/comparação; suporte executável não acompanha inclusão no catálogo. Comparar Core apenas com Core, percepção visual com visual e decisão com decisão.

### Idiomas e contexto

D declara texto em English, Arabic, Chinese, French, German, Italian, Japanese, Korean, Portuguese, Spanish, Vietnamese, Thai, Indonesian, Hindi, Russian e Polish para texto/VL/Omni/d1. Base requer confirmação própria. “Portuguese” **não comprova naturalidade pt-BR**, sotaque, gíria, nomes ou compreensão de UI brasileira.

Áudio/Omni declaram ASR/TTS em Arabic, Danish, German, Greek, British/American English, Finnish, French, Hebrew, Italian, Japanese, Korean, Dutch, Polish, Portuguese, Spanish, Swedish, Turkish e Chinese (18 idiomas, English com dois sotaques). **Live ASR é documentado somente em inglês.** A lista de ASR/TTS não comprova os mesmos idiomas em conversa com reasoning: D mostra prefill `<think>` para Audio, mas a matriz exata por idioma nesse modo permanece desconhecida sem card/probe. Não habilitar thinking no Omni. d1-Omni declara fala nos idiomas textuais exceto Hindi/Thai/Vietnamese/Indonesian; não herdar a lista de TTS, pois d1 não sintetiza fala.

256K/128K/32K são limites declarados, não contexto economicamente utilizável neste hardware. Medir recuperação, degradação, memória e latência em comprimentos crescentes; vídeo/áudio consomem budget. O catálogo explicita evidência familiar e ausência de config exata.

### GGUF são seis artefatos separados

D liga oficialmente `LiquidAI/LFM3-1.7B-GGUF`, `LiquidAI/LFM3-VL-2B-GGUF`, `LiquidAI/LFM3-Audio-2B-GGUF`, `LiquidAI/LFM3-Omni-2B-GGUF`, **`LiquidAI/d1-2B-GGUF` e `LiquidAI/d1-Omni-2B-GGUF`**. Não inventar Base-GGUF. São registros próprios no catálogo, com parent, formato, licença pendente e revision própria desconhecida. Link oficial não é inventário HF confirmado.

Exemplos D mostram texto Q4_K_M; VL Q4_0; Audio Q4_K_M + `mmproj-LFM3-Audio-2B-Q8_0.gguf`; d1 Q8_0. A lista completa de quantizações e nomes Omni não pôde ser confirmada. Não assumir todas Q2/Q4/Q5/Q6/Q8 para todos. Pesos do backbone e mmproj precisam pertencer ao mesmo contrato/revision; codec e cabeças de saída também entram no inventário. Conversão própria e quantização oficial não são o mesmo artefato.

## 3. Licença: risco comercial material

**Não é Apache-2.0. Não classificar como OSI open source. Não alterar a allowlist Apache-2.0 do seal/worker. Não aceitar termos.** D declara LFM Open License v1.0 em cada página pós-treinada. Para Base/GGUF a licença individual precisa ser obtida, não inferida do original. Campo `individual_license_inspected: false` em todos os registros.

O guia oficial D de 15/10/2026 foi lido integralmente; **o texto completo vinculante de cada checkpoint não estava acessível**. A tabela distingue orientação oficial de verificação jurídica. Não substituir contrato por resumo nem alegar auditoria concluída.

| Categoria | O que o guia D documenta | Consequência / revisão pendente |
|---|---|---|
| Direitos | Uso, modificação, fine-tuning, reprodução/distribuição; sem obrigação de abrir modificações; termos próprios para modificações condicionados à licença original | Confirmar grants copyright/patentes nas seções2/3 e artefatos abrangidos; adapter/merge/GGUF não elimina restrição |
| Threshold | Receita anual de **US$10.000.000 ou mais**; Legal Entity inclui controle, controladas e controle comum | Não contar só receita atribuída à Lia nem só a sociedade que hospeda o modelo. Confirmar definição integral, período de apuração, moedas, mudança societária e momento de ultrapassagem |
| Uso comercial | Vantagem comercial direta/indireta ou compensação; abaixo do Threshold, sujeito às demais condições; ao atingir US$10M, guia diz que uso comercial de originais/derivados não está licenciado e exige licença comercial separada | Não dizer “gratuito para sempre” nem presumir tolerância/grace period. Revisão antes de produto, aquisição/investimento/crescimento e contratos de clientes |
| Pesquisa/privado | Guia permite pesquisa/testes/avaliação interna; Threshold limita uso comercial; nonprofits qualificados têm exceção para fins não comerciais/pesquisa | “Privado” não significa não comercial: inferência interna numa empresa pode ser vantagem comercial. Confirmar aplicabilidade exata ao proprietário e eventual entidade |
| Distribuição §4 | Cópia da licença, preservar copyright/atribuição, incluir NOTICE se fornecido e marcar arquivos modificados | Inspecionar conteúdo real de NOTICE; não inventar texto/nome “Built with”. Registrar alterações de código/pesos/metadados e revisão de como marcar binários/adapter |
| Downstream | Guia aplica Threshold separadamente a cada empresa usuária comercial; licença do distribuidor não cobre automaticamente cliente acima do limite | Risco de produto redistribuível e promessas de liberdade futura; revisar cadeia de distribuição, documentação/termos e alternativa de base permissiva |
| Marcas | Permite declarar uso dos modelos; não concede permissão geral para marcas/branding Liquid AI | Não renomear Lia como produto oficial Liquid nem sugerir endosso; revisar atribuição e nome do derivado |
| Encerramento §11 | Guia relata término automático/imediato por descumprimento, parar uso de modelos/derivados e apagar cópias | Planejar migração/continuidade, backups e obrigações downstream; verificar texto vinculante e negociação comercial |

**Decisão técnica:** risco comercial maior que um artefato Apache revisado; manter rota alternativa Qwen/Gemma e interfaces que permitam trocar pesos. Pesquisa não equivale a distribuição aprovada. Revisão jurídica deve adquirir LICENSE/NOTICE de cada revision, comparar diferenças, avaliar entidade/receita/uso e aprovar por escrito antes de treinamento/redistribuição comercial. Nenhuma conclusão jurídica ou aceite nesta missão.

## 4. Runtime: contratos de pesquisa, nenhum loader novo

| Variante | Exemplo oficial / classe evidenciada em L | Frontend / saída |
|---|---|---|
| Texto/Base | AutoModelForCausalLM; `Lfm3ForCausalLM` | AutoTokenizer; classe concreta/config Base ainda desconhecida |
| VL | AutoModelForImageTextToText; `Lfm3VlForConditionalGeneration` | AutoProcessor; image/video preprocessing, encoder e projector |
| Audio | AutoModelForMultimodalLM; `Lfm3AudioForConditionalGeneration` | AutoProcessor, `audio_tokenizer`/LiquidCodec, encoder causal, depth decoder; resultado com códigos/comprimentos de áudio, não só tensor de tokens |
| Omni | AutoModelForMultimodalLM; `Lfm3OmniForConditionalGeneration` | AutoProcessor reúne texto/imagem/vídeo/áudio/codec; `audio_codes`, `audio_lengths`, waveform24kHz |
| d1 | AutoModel; `D1Model` identificado no conversor | `system_one(state, questions, media=...)`; estruturas tipadas, não `.generate()` |

Classes do conversor não são confirmação de `config.json` do checkpoint exato. Exemplos D/C requerem **`trust_remote_code=True`**, inclusive processor/tokenizer. Aqui permanece **False**. AutoModel/AutoProcessor disponíveis em framework não tornam custom implementation auditada.

D recomenda Transformers>=5.20.2 para Audio/Omni e >=5.19 para d1-Omni; texto usa atualização sem mínimo fixo. C fixa, no notebook texto, TF5.20.2/TRL1.16.0/PEFT0.21.2/Torch2.14.1, entre outros. São versões de receita, não lock validado Lia nem mínimos universais. Não instalar essa stack nesta missão. TF5.22.1 atual do Lab é API leve testada para contratos anteriores, não suporte LFM3 validado. Dependências documentadas: torch/accelerate, torchvision/Pillow para visão, librosa/soundfile para áudio, torchcodec para vídeo/Omni; kernels, libs nativas, versões e licenças transitivas precisam de auditoria.

Template L em `models/templates/LFM3.jinja` mostra ChatML `<|im_start|>`/`<|im_end|>`, `<think>`/`</think>`, XML `<tool_call><function=...>` e `<tool_response>`, ferramentas adiadas/tool references. Templates próprios de ASR/TTS e `<|audio_start|>` não podem ser reduzidos ao chat Qwen. Não reutilizar parser XML como executor. Nome/argumentos emitidos são dados não confiáveis: ACL, schema, orçamento e confirmação permanecem no runtime.

### Gate de auditoria antes de vendorização

Contrato proposto (não implementado): obter listing/commit de cada checkpoint; resolver `auto_map` de config, tokenizer_config e processor_config para **nomes reais** de `configuration_*`, `modeling_*`, `processing_*`, tokenização, feature/image/video processing, código LiquidCodec e imports transitivos. Os nomes exatos ainda não foram obtidos; não apresentar glob como inventário auditado. Fixar bytes/SHA/licença do código separada dos pesos; procurar rede, subprocess, execução dinâmica, desserialização, imports e escrita, kernels/extensões e cargas secundárias. Revisão humana do diff e dependências; só depois considerar vendorização com notices, testes e backend específico.

Qualquer backend futuro deve exigir autorização vinculada à ação/formato/arquivos auxiliares, sem download implícito. Generativo, fala e decisão precisam de protocolos e budgets próprios. d1 usa latência/CPU/RSS/calibração, **não tokens/s de geração**. Worker atual é inferência textual Qwen; não fingir áudio/d1 por um alias no mapa. LFM3, GGUF e LFM Open License continuam recusados pelos gates existentes.

## 5. GGUF/llama.cpp: melhor hipótese inicial local, não execução aprovada

D Audio e d1-Omni exigem **v0.8.0/b11960 ou posterior**. O tag b11960 resolve ao commit L; árvore contém `src/models/lfm3.cpp`, implementações mtmd lfm3vl/lfm3a/lfm3a-gen e testes systemone. Conversor L cobre texto/VL/Audio/Omni/d1 e separa componentes multimodais. Isso comprova presença de código, **não funcionamento desta build/hardware ou equivalência TF**. Para Omni, instruções específicas do card GGUF não puderam ser lidas; b11960 é baseline de investigação, não mínimo Omni verificado no card. Texto/VL D dizem apenas “build com suporte LFM3”; não inventar versão mínima.

Transformers mantém frontend/código Python/codec; GGUF usa conversão, template e kernels C++/mtmd. Há lacunas funcionais: D limita d1 GGUF a **Noul, Choice e Score**; extração text/number/date/box/boxes e multi-label exigem Transformers documentado. Endpoint `/v1/systemone` não é chat completion. Probabilidades “calibradas” são declaração do fabricante: medir Brier/ECE/reliability e abstention por domínio, nunca probabilidade=autorização.

D Audio documenta ASR via llama-mtmd-cli, TTS via llama-tts + mmproj e conversa/ tools/streaming por `/v1/realtime` WebSocket do llama-server. Não inferir paridade de todas essas funções para Omni. Imagem exige mmproj; vídeo exige política de frames/timestamps e áudio sincronizado. API OpenAI-compatible não garante suporte multimodal/typed/realtime completo. Limitar uploads/URLs, duração, resolução, buffers e autenticação; servidor local não deve buscar mídias arbitrárias nem expor rede por padrão.

D documenta Windows CPU AVX2/NVIDIA e uma tabela Vulkan AMD **antiga b7075 para LFM2**, além do app Llama Windows11 x64/ARM64. **Essa tabela não valida LFM3/b11960**. Não recomendar binário b7075 para LFM3. Antes do probe futuro fixar release/commit/build flags e verificar suporte CPU/Vulkan de cada operação LFM3/mtmd/codec, fallback, driver e RAM. A API da [release b11960](https://github.com/ggml-org/llama.cpp/releases/tag/b11960) foi consultada: existem assets `llama-b11960-bin-win-cpu-x64.zip`, `llama-b11960-bin-win-vulkan-x64.zip`, `llama-b11960-bin-ubuntu-x64.tar.gz` e `llama-b11960-bin-ubuntu-vulkan-x64.tar.gz`, além de outras plataformas. É confirmação de distribuição de binários nessa versão, não de operações LFM3/codec específicas na RX580. Nenhum asset foi baixado. Nenhum runtime foi compilado/instalado aqui.

Referência histórica Ryzen5 5500/16GB/RX5802048SP ~4GB não é telemetria. **CPU é a primeira hipótese de portabilidade**, sem meta de velocidade; Vulkan é experimento separado, sem promessa de aceleração RX580/ROCm. Offload parcial pode não cobrir encoder/codec; medir picos RAM/VRAM e competição com jogo/UI. ~1GB em 4-bit para 1.7B é alegação D; piso nominal 1.73B×0.5byte≈0.865GB exclui metadados, cache, contextos, buffers, encoder/codec/OS. Não prometer 256K ou Omni em4GB.

## 6. Treinamento: receitas existem, suporte Lia não

| Variante | Evidência C lida | Próximo probe autorizado, não executado |
|---|---|---|
| 1.7B post-trained | `lfm3_sft_with_trl.ipynb`: SFT+LoRA extração JSON, prompt/completion, save/merge | baseline vs adapter, native masks/limites, multi-turn/tools e save/reload em base exata |
| 1.7B Base | Link oficial do checkpoint; não validada receita dedicada Base | comparar custo/dados de instruction alignment vs post-trained; template/base EOS, retenção factual/pt-BR, não copiar receita e declarar suporte |
| VL | `lfm3_vl_sft_with_trl.ipynb`: LoRA no language_model, encoder visual congelado, assistant_only_loss e generation spans | masks nativas reais, grounding/OCR, não treinar tokens de imagem/user, encoder/projetor preservados, reload e regressão |
| Audio | `lfm3_audio_sft_with_transformers.ipynb`: comando falado→texto; `lfm3_audio_tts_sft_with_transformers.ipynb`: fala | LoRA texto não comprova TTS preservado; TTS inclui language_model e depth_decoder, codec24kHz/12 codebooks/frames80ms segundo C; targets e loss de áudio específicos |
| Omni | `lfm3_omni_sft_with_transformers.ipynb` comando falado→texto e `lfm3_omni_vqa_sft_with_transformers.ipynb` VQA | encoder visão/áudio congelados na receita VQA; verificar saída de fala e cross-modal retention, não só loss textual |

C usa q/k/v/o_proj, in/out_proj e w1/w2/w3; são **targets de receita**, não discovery/validação em pesos Lia. Convolução/atenção híbrida não equivale ao mapa de módulos Qwen. SFT é objetivo, LoRA é parametrização; QLoRA exige caminho quantizado/kernels/targets validado separadamente. Nenhum teste de QLoRA, adapter reload, merge ou equivalência executado nesta missão. GGUF de inferência não é base NF4 de treinamento.

Renderer atual é textual; não suporta automaticamente labels de codec/mídia. Presença de `{% generation %}` em template não prova assistant_masks corretas. Exigir testes com tokenizer/processor exatos, tool call/result múltiplos, EOS, áudio/texto intercalados, padding, spans e contexto sem truncagem; rejeitar máscara vazia/overmask. Validar dados multimodais licenciados/consentidos e splits antes de qualquer forward/backward. Preservar componentes via hashes/configs e contagem de trainables; congelamento não garante ausência de regressão. Nenhum notebook, download ou célula de treinamento executado.

## 7. Plano comparativo sem ranking cruzado

| Trilha | Métricas/probes a executar posteriormente |
|---|---|
| Core (LFM3 post/Base vs Qwen/Gemma) | pt-BR naturalidade/instruções/persona; factualidade; reasoning/planejamento e coding fora do nicho; tool schema/argumentos/recusa sem ferramenta; long-context retrieval; regressões e custo de adaptação |
| Vision (VL vs Qwen/Gemma multimodal) | OCR pt-BR, documentos, UI desktop/jogo com texto pequeno; boxes/points IoU/erro espacial, resolução/frames; imagens adversariais/prompt injection; fim-a-fim captura→decisão |
| Hearing/Speech | ASR WER/CER pt-BR/ruído/sotaques; eventos sonoros; TTS inteligibilidade/MOS humano e pronúncia; latência primeiro áudio/RTF/underruns; barge-in/cancelamento, sem confundir live ASR inglês com suporte pt-BR |
| Omni vs composição | Mesmos eventos/seeds/qualidade/budgets; memória pico vs modelos residentes ou carregados sob demanda; sincronização áudio-vídeo; TTFA, turn-taking, cancelamento e falhas por modalidade; preservar identidade do Core |
| d1/d1-Omni | F1/classificação/extração, grounded boxes, Brier/ECE/calibração, cobertura×erro com abstention; latência p50/p95 por lote/contexto; OOD e drift. Emissão tipada não é execução de ação |

Em cada trilha separar fabricante, estudo independente reconsultado e experimento Lia (hoje **nenhum ML**); registrar revision/formato/quant/runtime/hardware/contexto/RAM/VRAM/CPU/latência. Não comparar tokens/s d1 com generativo nem atribuir economia sem medir. Benchmarks independentes específicos ainda não incorporados.

## 8. Decisão desta rodada e gates

**Shortlist de pesquisa:** post-trained1.7B para Core compacto; Base como ablação de adaptação; VL para visão; Audio para Hearing/Speech; d1-2B para decisões; Omni e d1-Omni condicionados a ganho de integração/entrada de áudio. Não adotar todos. Manter Core como responsável por conversa/persona/planejamento, runtime como orquestrador/autoridade e memória externa. Resultado perceptivo pode ser encaminhado ao Core, com fontes/confiança/tempo e validade de estado.

Bloqueios por ordem: (1) LICENSE/NOTICE/cards/config/listing e revisions exatos; (2) revisão jurídica comercial e aprovação de aquisição; (3) inventário/auditoria de código/runtime/deps ou vendorização aprovada; (4) backend/protocolo de ação e formato específico, testes negativos e autorização humana; (5) pesos autorizados em ambiente adequado; (6) probes de inferência/qualidade/hardware; (7) treinamento/save-reload/quantização somente em missão separadamente autorizada. **Nenhum backend LFM3 executável foi adicionado.**

Evidência executada desta missão: [JSON](evidence/lfm3-research.json) e [reprodução/validação](VALIDATION.md).
