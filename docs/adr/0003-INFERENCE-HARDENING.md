# ADR-0003 — Autorização operacional e hardening da inferência

Data: 2026-10-30. Estado: **implementado/testado como software para revisão**, sem autorização real, pesos ou inferência. Substitui a referência textual de execução e os contratos de carregamento/métricas do ADR-0002; não concede aprovação de base/treino/release.

## Contexto

Partida remota confirmada: `2cb652353e1429ae75dd647e824edc107019babd`, PR #1 aberta, main não integrada. O snapshot restaurado tinha exatamente esses bytes e HEAD/index antigos; todos os arquivos foram comparados com o remoto antes de alinhar o histórico mixed sem alterar conteúdo. Não houve força no push, troca de branch ou revisão independente simulada.

Uma string approval_ref não comprovava autorização, e subprocesso/offline flags eram confundíveis com sandbox. AutoTokenizer em VLM completo precisava ser substituído por processor. O renderer verificava máscara, mas não o escopo efetivo de cada turno. A instalação leve de TF5.22.1 revelou também incompatibilidade com safetensors==0.6.2: o requisito oficial é >=0.8.0.

## Decisões

- Planejar a operação exata sem executá-la. Operador revisa modelo/revision/URL/licença/hash do arquivo legal, SHA do snapshot, tamanho, suite, código, paths, device/dtype e budgets; confirma a frase com SHA do plano em **terminal interativo**.
- `approve-inference` é comando do **operador humano**, nunca do agente. Store SQLite externo ao checkout, snapshot e raízes de pesquisa/aprovados. POSIX exige owner-only e UID atual; isso não autentica a identidade civil do proprietário. Sem --yes e sem aceitar JSON/string de atestação como execução não interativa.
- Grant específico `action=local-inference`, validade 1..3600 s, contexto/tokens por request/total, quantidade exata, duração e custo externo máximo zero. Vincular todo o plano, manifesto, licença, código e suite. Não autorizar download/treino/publicação/release. Uso único por transação SQLite, claim do supervisor, claim único do worker e finalização. Erro, bloqueio ou interrupção não devolvem o grant; concorrência não executa duas vezes.
- Worker também consulta o store externo; variáveis offline não substituem esse gate. Alterar o plano exige nova revisão/confirmação. Store ausente, permissões incompatíveis, expiração, mudança ou replay bloqueiam antes de carregar pesos.
- Separação de processo + timeout/grupo POSIX não são sandbox. Perfis explícitos: portable-process (sem limites OS/rede), linux-rlimit (CPU/AS/FSIZE/NOFILE/NPROC) e linux-netns-rlimit (mais namespace IP via unshare). Os dois últimos somente Linux CPU. Não fazer fallback silencioso. Filesystem/IPC Unix, permissões do usuário, VRAM e processos que escapem do grupo não estão isolados; NPROC é por UID e pode ser ignorado para contas privilegiadas.
- Backend por model_type **e architectures** exatos. Full qwen3_5 usa AutoModelForImageTextToText → Qwen3_5ForConditionalGeneration, AutoProcessor → Qwen3VLProcessor; qwen3 usa AutoModelForCausalLM → Qwen3ForCausalLM, AutoTokenizer → Qwen2Tokenizer. Rejeitar qwen3_5_text, MoE, Gemma e arquiteturas não auditadas no loader atual, em vez de fallback genérico. Shortlist não é suporte do loader.
- TF5.22.1 fixado, safetensors0.8.0 compatível e ambiente leve próprio sem Torch para configs/registries/tokenizer original/API Jinja. Sem checkpoint/tokenizer upstream obtido. Não adotar use_kernels/remote code para contornar hardware.
- Máscara nativa assistant_masks, validação prefix-stable por turno: nenhum system/user/tool supervisionado, todo assistant (incluindo tool calls) com tokens treináveis. Não corrigir spans por heurística. Templates que não cumpram isso requerem variante de treino auditada, não treino de prompt inteiro.

## Modelo de ameaça e limites

Protege contra execução acidental, plano trocado, grant expirado/reutilizado e desvio de orçamento sob operador/ambiente local confiáveis. Não protege contra código ou pessoa com o mesmo UID/controle do host que edite Python/SQLite, restaure backup, simule TTY, manipule relógio ou forge resultados. Não é assinatura, identidade criptográfica, autorização da licença, solução distribuída/NFS ou medidor de energia/billing. Não copiar/rollbackar stores para “recuperar” grants. Custo zero proíbe serviços pagos; o Lab não consegue impedir cobrança de uma máquina paga que o operador escolha fora do software.

Offline flags são opções das bibliotecas, não firewall. trust_remote_code=False/safetensors reduzem caminhos perigosos, mas não eliminam bugs nativos, supply chain ou conteúdo malicioso. Namespace IP não é sandbox de arquivos/Unix sockets; Windows/macOS não receberam essas garantias Linux. Ambientes com dados/segredos ou conteúdo hostil exigem sandbox/container/VM avaliado externamente.

## Evidência e próximos gates

Registries/AutoConfig e engine Jinja/tokenizer executados de fato em TF5.22.1 sem Torch. RLIMIT e namespace Linux verificados em processos Python descartáveis, não em modelos. Testes mocks verificam argumentos/shape/protocolo, não compatibilidade dos pesos. Teste real expôs máscara excessiva em span com whitespace final; o gate rejeita em vez de declarar sucesso. Inferência, template/tokenizer original, checkpoint config exato/revision, qualidade, PEFT/gradientes e treino continuam NOT-TESTED.
