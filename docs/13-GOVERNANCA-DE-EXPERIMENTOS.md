# 13 — Governança de experimentos e artefatos

## Objetivo

Permitir que qualquer resultado do Lia Model Lab seja reproduzível, auditável e comparável, sem colocar dados privados, datasets brutos, checkpoints ou estados de treinamento no Git.

## 1. Separação de armazenamento

| Categoria | Local recomendado | Git |
|---|---|---|
| Código, configs, schemas, manifests pequenos, templates e relatórios sanitizados | Repositório | Versionar |
| Índice de datasets e dataset cards | `docs/datasets/` ou registro equivalente | Versionar, sem amostras privadas |
| Índice de modelos e model cards | `docs/models/` ou registro equivalente | Versionar |
| Configuração e metadados de experimento | `experiments/<id>/` | Versionar quando sanitizados |
| Dados brutos, corpora licenciados, áudio/imagens privados | armazenamento local/remoto aprovado | Nunca versionar por padrão |
| Checkpoints, optimizer states, pesos, adapters, modelos mesclados e caches | armazenamento de artefatos aprovado | Nunca versionar |
| Relatórios de execução | relatório resumido e sanitizado | Versionar quando não expuser dados |
| Credenciais, tokens e consentimentos individuais | cofre/armazenamento seguro apropriado | Nunca versionar |

O diretório de pesquisa pode ser montado em volume local, drive externo ou armazenamento remoto. Não imponha `%LOCALAPPDATA%/Lia/Modelos` a dados de treinamento: essa pasta é reservada a modelos aprovados para consumo por aplicativos finais. O Model Lab deve usar uma raiz de pesquisa configurável e separada.

## 2. Identidade de dataset

Cada conjunto de dados recebe um ID estável e um card com:

- origem exata (URL, organização, repositório ou processo de geração);
- nome, versão/revision, data de aquisição e SHA-256 do manifesto/arquivo;
- licença e link para os termos aplicáveis;
- finalidade permitida e restrições de uso/redistribuição;
- forma de coleta, transformações, filtros e deduplicação;
- idioma, modalidades, volume e distribuição;
- presença potencial de PII, dados sensíveis ou conteúdo protegido;
- consentimento/base legal, retenção e processo de exclusão quando dados pessoais forem envolvidos;
- indicação de dados sintéticos, gerados por humano ou licenciados;
- splits train/validation/test e política de isolamento.

Não misture dados com permissões ou proveniência diferentes sem registrar a distinção. Não treine com conversas, áudio, Discord, arquivos ou histórico do usuário sem consentimento específico e política de dados aprovada. Dados de benchmark/holdout permanecem fora do treino e das iterações que os consultam.

## 3. Identidade de modelo e experimento

Todo modelo candidato e experimento precisa ter identidade imutável:

- identificador, proprietário/origem e URL de origem;
- revision/commit exato da base, tokenizer e chat template;
- hash dos pesos e licença da base;
- método (SFT, LoRA, QLoRA, DPO ou outro) e código/configuração usado;
- IDs e hashes de todos os datasets/splits;
- parâmetros de treino, seed, precisão, quantização e versões das ferramentas;
- hardware/driver/backend, host e localização do artefato;
- datas, duração, consumo estimado e custo real quando disponível;
- estado final: planejado, em execução, concluído, interrompido ou falhou;
- métricas, avaliações humanas, limitações e regressões observadas.

Um nome comercial, tag móvel ou branch `main` não substitui revision/hash.

## 4. Reprodutibilidade e retomada

- Cada execução parte de um commit de código e de configurações identificados.
- Fixe versões de dependências e registre comandos, parâmetros, seed e ambiente.
- Salve checkpoints de retomada fora do Git e documente o URI/path, checksum e frequência de checkpoint.
- Diferencie uma execução retomada de uma execução iniciada do zero.
- Preserve resultados e configurações de execuções falhas; marque o motivo, sem apagá-las.
- Registre alterações feitas após uma execução para não atribuir retrospectivamente resultados a código/configuração diferentes.

## 5. GPU remota, custo e autorização

Antes de iniciar qualquer execução remota ou paga, apresentar:

1. provedor/região/GPU e motivo da escolha;
2. estimativa de VRAM, RAM, armazenamento e duração;
3. custo por hora e teto total, ou declarar explicitamente quando não for possível estimar;
4. estratégia de checkpoint/retomada e comportamento ao atingir o limite;
5. dados que serão enviados, localização e política de exclusão;
6. opções locais/gratuitas ou de menor custo.

Exigir autorização explícita para criar recursos pagos, baixar modelos/datasets grandes, iniciar treinamento longo ou enviar dados a terceiros. Definir orçamento máximo e condição de parada antes da execução. Skills e subagentes nunca podem aprovar essas ações.

## 6. Gates de promoção

Use etapas distintas:

1. **Pesquisa:** documentos, hipóteses e comparação; sem treinamento custoso.
2. **Prova pequena:** amostra licenciada/sintética, smoke tests e estimativa real.
3. **Experimento controlado:** configuração e datasets fixados, métricas pré/depois e validação.
4. **Candidato interno:** model card, dataset cards, regressões, avaliação humana e uso restrito.
5. **Release aprovado:** revisão de licença, segurança, quantização, hashes, documentação de inferência, limitações e autorização de distribuição.

A criação de pesos ou o término de uma execução não promove o modelo automaticamente.

## 7. Templates e registros

Use os templates existentes em `templates/` como ponto de partida. Não invente resultados, licenças, métricas ou consentimento para preencher campos desconhecidos: marque-os como pendentes. Cada resultado citado em README ou roadmap deve apontar para o experimento e sua evidência correspondente.
