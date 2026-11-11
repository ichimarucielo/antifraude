# Antifraude

O pipeline prepara a base mensal de faturamento de serviços antifraude a partir de um Excel. Ele preserva os identificadores de origem para auditoria e separa as linhas que exigem revisão.

## Executar no WSL

Na raiz do repositório, com Python 3.11 ou superior:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py
python -m unittest discover -s src -v
```

O script lê a primeira aba. Se houver mais de um Excel em `data/original`, indique o arquivo com `python src/main.py --input-file "caminho/arquivo.xlsx"`. A entrada deve conter `Invoice Number`, `Child`, `MID`, `Product Description` e `Total Amount Due`.

Se um arquivo `.xlsx` tiver apenas uma coluna com linhas CSV, o pipeline tenta identificar e separar automaticamente os campos por vírgula ou ponto e vírgula.

## Saídas

A execução substitui `data/trabalho/antifraude_trabalho.xlsx` e `data/final/antifraude_vf.xlsx`. Esses caminhos contêm exemplos versionados no Git.

- **TRATADO / BASE_COMPLETA** preserva `child_original` e `mid_original`. Nas linhas tratadas, `Child` e `MID` recebem o mesmo identificador padronizado.
- **SUJEIRA** conserva os dados de origem das linhas com valor ausente, inválido, não finito ou não positivo, com `Child` ausente ou inutilizável, ou com Stelo em ambos os identificadores. A coluna `motivo_sujeira` registra o primeiro critério aplicável.
- **CHECK_DUPLICIDADE** lista todas as linhas da base tratada que compartilham a chave `Invoice Number`, `Child` padronizado e `Product Description`, com o tamanho de cada grupo. A chave serve para revisão. Todas as linhas candidatas continuam na base.

A planilha histórica esperada para validar os ajustes de julho não faz parte do repositório. Os testes cobrem as regras implementadas e a reconciliação entre entrada e saídas.
