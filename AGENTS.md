# Lia Model Lab — instruções para agentes

## Escopo e leituras

Leia [README](README.md), [índice oficial](docs/README.md), [ADR de consolidação](docs/adr/0001-CONSOLIDATION.md), [marca](docs/BRAND-STANDARDS.md) e [governança](docs/13-GOVERNANCA-DE-EXPERIMENTOS.md). Para código, leia [fundação técnica](docs/15-IMPLEMENTATION-FOUNDATION.md). Documentação numerada e ADRs são a autoridade; não recrie árvores paralelas ou arquivos legados.

Lia Model Lab entrega modelos/adapters, datasets governados, contratos, avaliação e manifests. A aplicação Lia é independente; AIRI é referência, nunca runtime obrigatório. Persistência de memória pessoal, permissões, captura, integrações, execução e avatar/produto ficam externos aos pesos. O Lab especifica contratos de consumo e testa mocks, não implementa o produto final aqui.

## Autorização

Pode pesquisar, escrever código e testes pequenos, validar configs e fixtures fictícias. **Não** iniciar GPU/cloud/API paga, grandes downloads, treino longo, uploads públicos de dados/pesos/adapters, publicação de derivados, coleta de conversas/arquivos/áudio pessoais ou aceite de termos sem aprovação específica. Na falta de autorização: documentar tamanho/custo/risco/alternativas, continuar tarefas independentes. Não usar credenciais ambientais para outros serviços; GitHub desta tarefa usa a autenticação provisionada, sem solicitar tokens.

Nunca colocar segredos, dados pessoais, transcrições, checkpoints, adapters reais, optimizer states ou corpora brutos no Git. Não publicar logs privados. Usar raiz de pesquisa configurável separada da pasta de modelos aprovados da aplicação. Dados exigem origem/licença/proveniência/consentimento quando aplicável, retenção e descarte; público não significa treinável.

## Evidência e decisões

Distinguir decisão aprovada, proposta, hipótese, experimento planejado, execução real e resultado comprovado. `CODE-PRESENT`/`DOCUMENTED` não equivalem a `AUTOMATED-PASS`/`RUNTIME-PASS`. Não provar jogo, tools ou memória por resposta textual. `NOT-TESTED` exige motivo. Resultado ML precisa de base revision/hash, dataset/split, template, protocolo, hardware/backend e data. Aprovação de organização/código não aprova modelo-base, orçamento ou release. Mudanças relevantes exigem novo ADR, sem reescrever decisões passadas para inventar aprovação.

## Skills e subagentes

Consultar [.agents/skills/README.md](.agents/skills/README.md) e [orquestração](docs/14-ORQUESTRACAO-DE-AGENTES.md). Ler manualmente `.agents/skills/<nome>/SKILL.md` para a tarefa pertinente se descoberta automática não estiver comprovada. Perfis em `.codex/agents/` têm responsabilidades de revisão, read-only por instrução; não criam sandbox nem elevam permissão. Arena **não é presumido** capaz de descobrir skills ou executar perfis Codex. Sem ferramenta real de spawn/wait, executar em sequência e informar que não houve delegação.

O principal coordena fontes/escopo/saída/stop e ownership. Revisores leem; principal edita README, AGENTS, configs, SOURCES e manifest. Se escrita delegada for autorizada no futuro, arquivos exclusivos por tarefa; nunca dois agentes editando o mesmo arquivo. Não simular revisores independentes. Preservar `docs/BRAND-STANDARDS.md` e separar licença do código/base/dados/voz/assets/marca.

## Desenvolvimento e validação

- Antes de editar: `git status`, branch, HEAD e estado remoto; integrar semanticamente, não fazer merge cego.
- Trabalhar apenas na branch desta sessão; não enviar para main nem mergear PR sem pedido.
- Componentes pequenos; testes para sucesso, inputs inválidos, vazamento, overwrite, caminhos e hashes.
- Não carregar pesos nem fazer rede como efeito colateral de importar módulos/testar CLI.
- Executar `.venv/bin/python -m pytest -q` e `.venv/bin/python scripts/verify_repository.py`.
- Depois de alterações finais: `.venv/bin/python scripts/verify_repository.py --write-manifest`, validar novamente e `git diff --check`.
- Manifest representa fonte mantida, skills/perfis/configs/testes/docs, não checkpoints/cache/ambiente local. Não atualizar hashes para mascarar corrupção sem investigar.
- Commits claros, PR para main, relatório de comandos reais, limitações, custos/downloads não realizados e próximos gates. Não fechar/mesclar a sessão antes de salvar tudo.

## Artefatos de experimento/release

Obrigatórios: base/tokenizer/template revisions e hashes, licença/notices, dados/cards/splits/hashes, método/config/seed/dependências, ambiente/hardware/driver/backend, checkpoints de retomada, duração/custo reais (null se não executado), métricas base/adaptado/quantizado, falhas/regressões, checksums e instruções de inferência. Export estrutural local não aprova publicação nem prova carregamento PEFT. Nenhuma ação gerada pelo modelo concede sua própria autorização.
