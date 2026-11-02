# Fixtures de software

Origem: exemplos escritos para testes desta entrega, sem conversas, arquivos ou áudio pessoais. Licença destas fixtures textuais: CC0-1.0. `provenance.synthetic=true` e generator `handwritten-test` indicam exemplos fabricados para teste, não dados humanos/coleta pública.

`pilot.jsonl` tem nove diálogos aritméticos fictícios; não representa a persona Lia aprovada nem um corpus de treinamento. `base.json`, `adapter.json` e `adapter-quantized.json` são predições simuladas com hashes/revision fictícios e evidência `synthetic-not-inference`. O adapter da fixture erra tools deliberadamente para testar que a regressão aparece.

Não há modelo-base, adapter treinado ou resultado de inferência aqui. Testes criam safetensors minúsculos de zeros apenas em pastas temporárias; nenhum peso é versionado. Não publicar estas métricas como qualidade de Lia Core.
