# 00 — Visão, missão e escopo

## 1. Visão

O **Lia Model Lab** existe para que a Lia possa evoluir de uma aplicação que seleciona modelos de terceiros para um ecossistema com **modelos e pesos próprios**, construídos a partir de bases abertas e treinados para as capacidades, identidade e experiências da Lia.

A primeira linhagem será **Lia Core**. O objetivo de longo prazo é **Lia Omni**: uma família multimodal, especializada e integrada ao produto, capaz de conversar, raciocinar, perceber, falar, agir por ferramentas, interagir socialmente e atuar em ambientes digitais.

Lia Omni não é uma promessa de que um único checkpoint fará tudo. É um sistema composto por modelos e serviços especializados, com contratos e avaliações definidos.

## 2. Objetivos

1. Ter autonomia para selecionar, adaptar, treinar e versionar pesos da Lia.
2. Construir uma personalidade estável e reconhecível sem depender exclusivamente de um system prompt longo.
3. Ensinar comportamento de conversa, instrução, raciocínio, planejamento e tool-use.
4. Preparar modelos e adapters para visão, vídeo, áudio e tarefas especializadas quando a base suportar essas modalidades.
5. Cobrir as capacidades de produto inspiradas no AIRI: personagem/avatar, conversa, voz, percepção, integrações sociais, jogos, automação, memória e computer use.
6. Oferecer variantes que possam ser executadas em diferentes hardwares/hosts e níveis de custo.
7. Ter avaliação própria da Lia, em português brasileiro e em cenários reais do produto.

## 3. Não objetivos da primeira geração

- Treinar um foundation model de dezenas de bilhões de parâmetros do zero.
- Criar um modelo universal que execute sozinho Discord, jogos, memória e desktop sem serviços externos.
- Embutir dados pessoais, conversas privadas ou credenciais nos pesos.
- Substituir o runtime, permissões, ferramentas e integrações da aplicação Lia.
- Prometer suporte a todos os sistemas AMD/NVIDIA/Intel antes de validar drivers, kernels, framework e hardware.
- Distribuir um checkpoint só porque teve bom desempenho em benchmark público.

## 4. Princípio principal: cérebro não é o produto inteiro

A arquitetura deve separar:

| Camada | Responsabilidade | Exemplos |
|---|---|---|
| Pesos/modelos | Aprender padrões, linguagem, visão, áudio, planejamento, tool-use e comportamento | Lia Core, modelo de visão, modelo de fala, modelo de jogo |
| Runtime cognitivo | Construir contexto, selecionar modelos, chamar ferramentas, controlar loops, validar respostas | Brain router, orchestrator, agent loop |
| Memória | Persistir fatos e episódios que mudam ao longo do tempo | Memória episódica, semântica, preferências, relações |
| Ferramentas/integrações | Executar ações reais com autorização | Discord, Minecraft, Factorio, browser, filesystem, Home Assistant, MCP |
| Corpo/embodiment | Dar presença visual e expressiva | Live2D/VRM, rig, animações, expressões, lip-sync |
| Produto | UI, instalação, permissões, configuração, privacidade, updates e diagnóstico | Lia Launcher, Stage, configurações |

O modelo precisa aprender **quando e como solicitar** uma ação; o runtime precisa validar se ela é permitida; o conector executa; o resultado retorna ao modelo; e o modelo decide o próximo passo.

## 5. O que o AIRI significa para este laboratório

AIRI é uma referência de produto e engenharia, não o destino arquitetural. Seu manual 0.13.0 é utilizado como catálogo de capacidades a estudar. O fork presente em `Lia-Project/airi` foi identificado como 0.12.0-beta.5 no estado consultado em 30/10/2026. Portanto, a documentação upstream 0.13.0 não prova que a mesma versão/feature exista no fork da Lia.

A direção já registrada em `BloomRX/Lia-Project/AGENTS.md` é produto independente. O Lab deve gerar modelos que possam ser conectados ao runtime próprio da Lia, e não pesos condicionados a uma implementação AIRI específica.

## 6. Definição de sucesso do Lia Core v1

Lia Core v1 será considerado pronto somente quando:

- carregar de um artefato reprodutível e licenciado;
- produzir conversas naturais em pt-BR, com identidade Lia consistente;
- seguir instruções e manter contexto longo o suficiente para tarefas previstas;
- usar ferramentas com argumentos válidos e continuar a partir do resultado;
- distinguir quando não sabe, quando precisa de ferramenta e quando deve recusar;
- superar a base original em objetivos definidos, sem regressões inaceitáveis em capacidades gerais;
- passar avaliação cega humana e benchmarks internos;
- ter latência/custo e requisitos de hardware documentados;
- ter modelo-card, dataset cards, hash e instruções de inferência.

Visão e áudio não serão declarados cobertos por um modelo apenas porque o runtime suporta anexos; cada modalidade terá gate próprio.
