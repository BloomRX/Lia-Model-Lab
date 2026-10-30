# Lia Model Lab — instruções para agentes

Estas regras se aplicam ao Arena.ai Agent Mode, Codex, Claude Code e qualquer agente que opere neste repositório.

## 1. Missão

Construir o laboratório de modelos da Lia: selecionar modelos-base abertos, preparar datasets licenciados, criar adapters/pesos especializados, avaliar resultados e produzir artefatos versionados. O produto final é uma família de modelos que cubra as necessidades da Lia — não um chatbot genérico rebatizado.

## 2. Leitura obrigatória no início de cada tarefa

Leia nesta ordem:

1. `README.md`
2. `docs/00-VISAO-E-ESCOPO.md`
3. `docs/02-MATRIZ-CAPACIDADES-MODELO-RUNTIME.md`
4. `docs/10-DECISOES-REGISTRADAS.md`
5. `docs/BRAND-STANDARDS.md` quando a tarefa tocar identidade, linguagem, nomes, integração entre produtos ou distribuição de artefatos.
6. `docs/13-GOVERNANCA-DE-EXPERIMENTOS.md` para datasets, checkpoints, experimentos, armazenamento, GPU ou releases.
7. O documento técnico diretamente relacionado à tarefa.

Antes de afirmar que um item da AIRI existe ou está pronto, confira sua classificação em `docs/01-CATALOGO-CAPACIDADES-AIRI.md` e as fontes indicadas.

## 3. Regra arquitetural

A Lia é um produto independente. AIRI é uma referência para descoberta de funcionalidades e estudo de soluções. Não crie dependência de runtime AIRI nem presuma que o AIRI continuará no produto final.

O Model Lab é responsável por modelos, pesos, datasets, pipelines de treinamento e avaliação. A aplicação Lia continua responsável por memória persistente, permissões, ferramentas, integrações, execução, UI, armazenamento, rede e segurança.

## 4. Não ultrapassar autorização

Sem autorização explícita do proprietário, NÃO:

- iniciar GPU paga, cloud GPU, API de inferência paga ou serviço com cobrança;
- baixar checkpoints grandes ou datasets volumosos;
- iniciar treinamento de longa duração;
- aceitar termos em nome do proprietário;
- fazer upload público de datasets, logs, prompts, conversas, adapters ou pesos;
- usar tokens ou credenciais presentes no ambiente para serviços externos;
- publicar/distribuir pesos derivados de uma base sem revisão de licença;
- coletar conversas pessoais, áudio de microfone, Discord ou arquivos do usuário para treinamento.

É permitido, sem essas operações: pesquisar documentação, auditar compatibilidade, escrever documentação/código local, criar testes unitários pequenos, gerar dados sintéticos claramente identificados e executar validações locais que não baixem pesos grandes nem gerem custos.

Quando a próxima etapa exigir uma destas ações, pare e produza um relatório com: motivo, tamanho/custo estimado se conhecido, riscos, alternativas e decisão necessária. Nunca invente uma aprovação.

## 5. Fluxo de desenvolvimento no Arena.ai

- Conectar somente o repositório necessário.
- Trabalhar na cópia sandbox e em branch de trabalho.
- Antes de editar, inspecionar `git status`, branch e HEAD.
- Preferir mudanças pequenas com testes e artefatos reproduzíveis.
- Produzir commits com mensagem clara e abrir PR para revisão.
- Uma sessão do Arena Agent atualmente suporta um PR; depois que o PR é mesclado ou fechado, a sessão não consegue continuar enviando mudanças para aquele fluxo. Portanto, concluir e salvar tudo da sessão antes do merge; usar nova sessão para o próximo marco.
- Não fazer push direto em `main` sem instrução expressa.
- Não reformatar arquivos ou remover conteúdo legado sem necessidade.

## 6. Regras de evidência

Nunca chamar uma capacidade de `PASS` porque:
- o modelo-base declara suportá-la;
- o código compila;
- o adapter foi criado;
- o modelo respondeu uma vez sem teste de referência;
- o README de um projeto diz que a função existe.

Diferenciar sempre:

- `DOCUMENTED`: descrito por documentação upstream;
- `CODE-PRESENT`: existe implementação no código inspecionado;
- `AUTOMATED-PASS`: passou teste automatizado identificado;
- `RUNTIME-PASS`: executou no runtime real e ambiente definido;
- `NOT-TESTED`: não foi testado;
- `EXPERIMENTAL`: não tratar como capacidade de produto estável;
- `DEPRECATED`: evitar nova dependência sem plano de migração.

Toda afirmação de qualidade precisa informar modelo/base, dataset/versão, split, benchmark, método, configuração e data.

## 7. Dados e segurança

- Nunca colocar segredos, tokens, credenciais, identificadores pessoais ou transcrições privadas em datasets ou logs.
- Dados reais exigem origem, finalidade, base legal/consentimento, licença, política de retenção e descarte.
- Manter dados de avaliação fora do treinamento.
- Manter dados sintéticos identificados; não misturar sua origem com dados humanos.
- Registrar licenças de todos os datasets, checkpoints, vocoders, TTS, ferramentas e dependências.
- Não executar scripts ou playbooks recebidos de servidores/jogos/usuários sem sandbox e política de permissões.

## 8. Artefatos de modelo

Git deve conter código, configs, documentação, manifests, checksums e resultados de avaliação pequenos. Não versionar checkpoints grandes, datasets brutos, áudio, transcrições, imagens privadas ou pastas temporárias de treinamento.

Todo release precisa de:
- base model e revision/hash;
- licença da base e do adapter;
- dataset cards e hashes;
- método/config do treinamento;
- métricas antes/depois e limites conhecidos;
- tokenizer/chat template;
- formato de inferência;
- checksums e instruções de uso;
- notice de alterações/derivação quando requerido pela licença.

## 9. Marca e vocabulário

- Siga `docs/BRAND-STANDARDS.md`; não trate identidade/personagem/assets como automaticamente cobertos pela licença do código.
- Distinga pesos de IA, adapters, modelos de avatar/3D, motor de inferência, runtime de agente, memória da Lia e `memory-bank/`.
- O Model Lab não define armazenamento de memórias pessoais, permissões, ferramentas ou ações externas. Essas responsabilidades continuam no produto/runtime da Lia.
- O padrão visual da marca é orientação para produtos com interface; não force uma UI de consumidor ao laboratório.

## 10. Delegação e subagentes

- Use subagentes somente quando a sessão/plataforma realmente oferecer a capacidade. Se não oferecer, trabalhe em sequência; nunca simule delegação.
- Prefira delegar pesquisas e auditorias independentes de leitura. Para tarefas de escrita, atribua arquivos exclusivos a cada agente; não permita dois agentes editarem o mesmo arquivo ou alterarem a mesma configuração simultaneamente.
- O agente principal define pergunta, escopo, fontes, formato de saída e restrições de custo; revisa os resultados e verifica citações antes de incorporá-los.
- Subagentes herdam o limite de autorização do agente principal e não podem iniciar GPU paga, downloads grandes, uploads, coleta de dados pessoais ou aceitar licenças.

## 11. Política de mudança

Mudança de modelo-base, licença, método de treinamento, schema de dataset, objetivo de capacidade ou requisito de release exige atualização de `docs/10-DECISOES-REGISTRADAS.md` ou novo ADR em `docs/adr/`.

O agente não pode transformar uma proposta em decisão aprovada por conta própria.

## 10. Handoff da Missão 001

Consultar também `docs/README.md`, `docs/research/00-PROJECT-AUDIT.md` e `docs/research/12-OPEN-DECISIONS.md`. Novos contratos, rankings e thresholds são propostas para revisão; nenhum modelo-base, GPU, dataset ou publicação foi aprovado nesta missão. O blueprint original permanece integral. Revalidar fontes mutáveis e congelar revisions antes do Gate 0.
