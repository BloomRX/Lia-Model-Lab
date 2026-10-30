# 10 — Workflow com Arena Agent Mode

**Missão 001 · consulta: 2026-10-30 · estado: proposta para revisão.**

## O que foi realmente observado

Terminal/bash, Python 3.11.2, Git e gh funcionaram; API GitHub, clone raso e escrita de documentação funcionaram. Sandbox é uma cópia do repo, não o PC do usuário. Recursos observados em [08](08-HARDWARE-INFRASTRUCTURE.md); não há GPU utilizável evidenciada. Não instalar checkpoints para “descobrir” se há GPU.

GitHub autenticado pela sessão; usar git para branch/status/commit/push e gh para PR. Não pedir tokens ou guardar credenciais. Documentação pública Arena confirma sandbox, ferramentas e entrega por PR ([fonte](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode), consulta 2026-10-30). Também contém avisos de limitação após merge/close e FAQ de download: não tratar essas descrições como SLA de persistência/backup. Confirmar condições da sessão antes de operação irreversível.

Não houve teste de isolamento adversarial, GPU, duração máxima de processo, quota de armazenamento, recuperação após encerramento ou job de ML. Um shell com rede não comprova essas capacidades. Acesso a GitHub e obtenção de páginas nesta pesquisa funcionaram; acesso ao registry de modelos/datasets a partir de um futuro job deve ser validado antes de planejar transferências. Não copiar secrets em logs de diagnóstico.

## Trabalho pequeno e verificável

Cada tarefa tem objetivo, não objetivos, fontes, critério de aceite, limite de custo/download, arquivos-alvo e rollback. Ordem:

1. Ler AGENTS, docs e decisões; status/branch/HEAD antes de editar.
2. Propor ADR quando mudar base, schema, licença ou capacidade.
3. Alteração pequena: schema, validator, mock/replay, baseline, treino piloto e release em tarefas separadas.
4. Rodar checks locais sem baixar pesos; registrar comandos/resultados/limitações.
5. Inspecionar diff, artefatos/segredos, criar commit revisável e PR na branch da sessão. Não tocar main nem mergear sem pedido.
6. Encerrar com handoff: o que mudou, evidências, bloqueios e próxima tarefa.

Sem ferramenta de subagentes disponível nesta sessão: pesquisa consolidada pelo agente principal, com consultas independentes em paralelo quando possível; **não simular revisores independentes**. No futuro, agentes de fontes/modelos/dados podem produzir achados com schema comum e revisão central, sem aprovar decisões concorrentes.

## ML no Arena: papel realista

Adequado nesta sessão a pesquisa, edição, validação de manifests/links, fixtures minúsculas, análise de resultados pequenos e scripts de testes sem pesos. Treino de 27B não é viável neste ambiente observado. CPU smoke tests pequenos podem ser possíveis posteriormente, sob limite e autorização de download.

Jobs longos devem usar ferramentas de processo apropriadas se disponíveis, com logs, cancelamento e checkpoint; não depender de um bash esperando indefinidamente. Treino remoto é execução explicitamente aprovada fora do sandbox, com recuperação de checkpoints e manifest, não uma sessão do chat como scheduler de produção. Sem serviços pagos nesta missão.

Git guarda código/docs/configs/manifest/métricas pequenas. Dados, pesos e cópias de pesquisa temporárias ficam fora do patchset. Persistência de arquivos da sessão não substitui artifact registry aprovado. Antes de fechar/mesclar PR, salvar e verificar tudo; nunca baixar/uploadar material privado apenas para apresentar resultado.
