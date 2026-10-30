# Validação documental — Missão 001

Data: 2026-10-30. Escopo: integridade documental; **não** avaliação ML/runtime.

## Checks realizados

- `git diff --check`: sem erros de whitespace.
- Todos os links Markdown relativos de README, AGENTS e docs resolvem para arquivos locais existentes (âncoras de títulos não verificadas).
- Os 14 documentos obrigatórios estão presentes; índice e README apontam para a pesquisa.
- Ledger AIRI contém 39 registros; todos os caminhos existem no checkout `v0.13.0` fixado. Arquivos têm SHA-256 e quantidade de linhas para reconferência; referências de diretório não têm hash de arquivo.
- Matriz possui 48 linhas e as dez colunas especificadas (incluindo ID e classe); IDs de benchmark usados estão definidos no plano.
- JSON de evidências e manifest podem ser lidos pelo parser padrão Python.
- `docs/Lia_Model_Blueprint.md` é idêntico byte a byte ao original do HEAD inicial; não foi editado.
- Nenhum checkpoint, dataset, clone temporário, áudio ou credencial incluído na alteração. `.cache/` está ignorado.
- Config de candidatos mantém status de shortlist e não aprova os novos candidatos econômicos.

## Reprodução sem rede/modelos

```python
from pathlib import Path
import hashlib, json, re, subprocess

files = [Path('README.md'), Path('AGENTS.md'), *Path('docs').rglob('*.md')]
for p in files:
    for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
        if '://' in link or link.startswith(('#', 'mailto:')):
            continue
        target = link.split('#')[0]
        assert not target or (p.parent / target).exists(), (p, link)

original = subprocess.check_output([
    'git', 'show',
    '182f1a1edd08e7197b8ea62c9932e9778bc2af9a:docs/Lia_Model_Blueprint.md'
])
assert original == Path('docs/Lia_Model_Blueprint.md').read_bytes()
manifest = json.loads(Path('PACKAGE-MANIFEST.json').read_text())
for item in manifest['files']:
    data = Path(item['path']).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
```

Para revalidar evidência de código, obter a tag/SHA descrita em SOURCES e comparar `source_sha256` com os arquivos do upstream; isto exige rede, mas não modelos. Validação de existência de um caminho **não** comprova a funcionalidade descrita: limitações semânticas e de execução continuam no inventário.

Config YAML: revisão textual do diff realizada; parser PyYAML não disponível nesta sessão, portanto parse YAML **NOT-TESTED**, sem instalação de dependência.

## Não realizado

Treinamento, download de pesos, inferência, benchmark de modelo, probe LoRA/QLoRA/merge, testes do AIRI/Lia, autenticação de bots, acesso ao PC do proprietário ou serviços pagos. Não há selo PASS de nenhuma capacidade Lia resultante destes checks.
