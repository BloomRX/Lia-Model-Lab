# 00 — Auditoria do projeto

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## Escopo e método

Lidos README, AGENTS, PACKAGE-MANIFEST, blueprint, documentos 00–11 da v1.0, configs e templates. Checkout inicial limpo, branch `arena/0b3b035e-lia-model-lab`, base `182f1a1edd08e7197b8ea62c9932e9778bc2af9a`. O pacote tem políticas, templates e requisitos; não tem pipeline executável de treinamento, dados curados, pesos, resultados ou ambiente ML validado. Não inferir capacidades do produto a partir do Lab.

Auditoria estática do código AIRI em **v0.13.0**, comparada à árvore **v0.12.0-beta.5**; fork Lia consultado separadamente em main. Nenhum aplicativo, bot ou teste upstream foi executado. CODE-PRESENT não é AUTOMATED-PASS nem RUNTIME-PASS. Fontes e hashes: [SOURCES](SOURCES.md).

## Autoridade e contradições

| Item | Evidência/impacto | Tratamento nesta missão |
|---|---|---|
| Blueprint §§20/25 coloca AIRI como corpo/runtime final | Conflita com v1.0 D-012 e direção independente | Preservar integralmente; ler como exploração histórica. Contratos novos não dependem de AIRI |
| README diz “este ZIP”, “nenhum commit/push”, main só tinha 2 arquivos | Estado de empacotamento, não deste checkout | README atualizado; histórico v1.0 permanece nos documentos |
| Gemma 4 teria termos próprios incompatíveis com Apache | Card oficial atual declara Apache 2.0 | Corrigir docs 04/06 e config; licença de dados/vozes continua independente |
| Shortlist v1.0 concentra 27B | Incompatível com memória local limitada como ponto de partida universal | Separar ranking de qualidade remota e piloto econômico 0.8B/4B |
| Gemma 4 áudio generalizado a toda família | Card limita áudio a E2B/E4B/12B | Comparar variantes exatas; saída é texto, não TTS |
| Memória pgvector sugerida pela existência do pacote | `src/index.ts` só conecta cliente e callback vazio | Não classificar como retrieval implementado |
| Factorio exposto na UI | Store configura conexão; não foi localizado agente server-side equivalente a Minecraft | Lacuna; sem promessa de jogo funcional |
| Hardware 4 GB vs 8 GB | v1.0/contexto da missão citam 4 GB; docs arquiteturais Lia citam 8 GB | Configuração atual desconhecida; diagnóstico no PC necessário |
| Fontes v1.0 usam branch mutável | Podem desaparecer ou divergir de main | Novos permalinks por SHA; preservar referências anteriores como histórico |
| Aprovações v1.0 | D-001–014 são registro anterior, não aprovações produzidas por esta pesquisa | Não alterar status de aprovação de produto; novas recomendações permanecem propostas |

## Estado do Lia Project

Snapshot consultado: `db99c709059a6d074b18361bfb32c9f144620632` (main). `airi/apps/stage-tamagotchi/package.json` confirma `0.12.0-beta.5`. Isto não prova igualdade de código com a tag upstream: fork pode conter patches. AGENTS e documentos de arquitetura/voz foram consultados como contexto. Não houve auditoria funcional completa do produto Lia. Todos os requisitos da matriz são **NOT-TESTED na Lia por esta missão**, mesmo quando há legado incorporado.

## Critério de fechamento

Documentos, matriz e evidências estáticas entregues para revisão. Gates de seleção de base, hardware real, compatibilidade LoRA/QLoRA/export e benchmarks permanecem **inconclusivos**, não aprovados. Sem checkpoints/datasets baixados, treino, gastos ou mudanças no runtime. Revisão documental não equivale a prontidão para iniciar GPU paga.
