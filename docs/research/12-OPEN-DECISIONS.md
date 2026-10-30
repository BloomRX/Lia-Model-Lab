# 12 — Decisões abertas, impedimentos e riscos

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Registro: tudo abaixo é PROPOSTO ou PENDENTE

Decisões D-001–014 da v1.0 são histórico; esta missão não aprovou novos modelos, custos, dados, publicação ou alterações no produto. O proprietário aprova produto, persona, custo, direitos e release. Responsável técnico futuro propõe experimentos com evidências.

| ID | Decisão / risco | Evidência atual | Próxima prova / condição de resolução |
|---|---|---|---|
| O-01 | Core 4B inicial vs 27B remoto | Ranking por viabilidade, sem benchmark | Gates licença/compatibilidade, pt-BR/tools e custo, ADR proprietário |
| O-02 | Revisão exata de pesos/templates/formatos | Cards consultados, sem manifest de pesos | Congelar commits/hashes por checkpoint antes de download |
| O-03 | Licenças atuais e derivados | Gemma 4 Apache confirmado documentalmente; especialistas/vozes ainda incompletos | Snapshot LICENSE/NOTICE de cada artefato/dataset e revisão de distribuição |
| O-04 | GPU local 4/8 GB e ROCm/Vulkan | Registros históricos divergentes; sandbox sem GPU | Diagnóstico no PC; não inferir de nome da placa |
| O-05 | Backend de treino/framework | Compatibilidade documental, não smoke-tested | Load/backward/save/reload/merge/export na versão exata e GPU suportada |
| O-06 | Primeira voz Lia / biometria | Modelos existentes, identidade/direitos indefinidos | Voz original/consentida, contrato de uso e teste pt-BR; nada de clonagem sem autorização |
| O-07 | Persona canônica e humor | Objetivos, sem canon detalhado aprovado | Profile e rubrica revisados; dataset não pode inventar identidade |
| O-08 | Memória store / embeddings / retenção | AIRI fatos existe, pgvector placeholder | Schema ACL+temporal, retrieval local, forget/restore e provedor de storage |
| O-09 | Discord e privacidade entre cenas | AIRI ADR declara live checks faltantes e compartilhamento de contexto | Isolamento por scope e saída, consentimento de voz, testes multiusuário |
| O-10 | Minecraft primeiro, adapter e servidor | Quatro camadas presentes upstream; não executadas | Servidor autorizado, versões/licenças, seeds e action schema; aceitar escolha de jogo |
| O-11 | Factorio integração ausente | UI/store sem agente pronto comprovado | Prova server-side state/action e benchmark de produção |
| O-12 | Dados/escala/custo de curadoria | Plano apenas | Data cards e consentimentos, test selado e revisão humana |
| O-13 | Thresholds e amostra | Propostas, sem base/poder medidos | Congelar protocolo antes do treino; inconclusivo não é PASS |
| O-14 | Quantizações/backend visual/áudio | Não testados | Comparar base/adaptado/quant, round-trip e projector/talker |
| O-15 | Persistência/limites Arena e job remoto | Snapshot de recursos, sem SLA | Verificar quotas/duração/storage e recovery fora da sessão |
| O-16 | MoE/Omni/representações compartilhadas | Hipóteses de longo prazo | Ablação de routing/composição, custo/qualidade e vantagem de consolidação |

## Impedimentos para começar treinamento agora

Não há base revision fechada, schema executável/dataset aprovado, test selado/baseline medido, GPU/custo aprovado nem probe de treinamento/export. São bloqueios explícitos; não defeitos escondidos por um ranking. Esta missão prepara a execução, não autoriza a próxima fase.

## Riscos e mitigação

Esquecimento/persona repetitiva → mistura e ablação; alucinação de ação → retorno verificável; reward hacking → métricas de estado e holdout; prompt injection → ACL/sandbox determinísticos; roubo/vazamento de memória → isolamento antes de retrieval; voz sem direitos → consent ledger; licença mutável → snapshots; dependência CUDA → contratos e fallback CPU/Vulkan; arquitetura excessiva → poucos pesos e etapas; base enorme → envelope medido; contaminação → split por grupo/hash; afirmação de maturidade → status de evidência explícito.

Revisitar pesquisa upstream no início de Gate 0 e a cada release. Novos lançamentos não invalidam automaticamente baselines nem autorizam troca de base. Não corrigir as lacunas de runtime dentro desta missão documental.
