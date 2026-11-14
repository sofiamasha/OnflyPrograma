# Relatório de Reservas de Hotéis — Entrega

## 1. Objetivo

Desenvolver uma aplicação em Python 3.11 para processar reservas de hotéis a partir de arquivos CSV, aplicar as regras de negócio e gerar um relatório consolidado em JSON.

## 2. Problemas identificados e correções

Durante a análise do projeto, foram identificados e corrigidos os seguintes problemas:

1. **Limite de reservas:** a implementação limitava o processamento a 200 registros. O limite artificial foi removido para permitir a leitura de todo o arquivo.
2. **Reservas NO_SHOW:** reservas com esse status estavam sendo consideradas faturáveis. A regra foi ajustada para considerar faturáveis somente reservas `CONFIRMED`.
3. **Cálculo de diárias:** o cálculo não considerava corretamente a diferença entre datas de meses ou anos diferentes. Foi corrigido para utilizar a diferença completa entre checkout e check-in, multiplicada pela quantidade de quartos.
4. **Conversão cambial:** a conversão utilizava uma operação inadequada e podia gerar imprecisão. Foi corrigida para multiplicar o valor pelo câmbio correspondente, utilizando `Decimal`.
5. **Ordenação do ranking:** os hotéis estavam sendo ordenados de forma crescente pelo faturamento. A ordenação foi corrigida para faturamento decrescente, com `hotel_id` crescente em caso de empate.
6. **Tratamento de entradas inválidas:** erros como taxa de câmbio ausente e arquivo com codificação inválida não eram tratados corretamente. O tratamento foi ajustado para retornar o código de saída 2 para entradas inválidas.

## 3. Testes adicionais

Foram adicionados testes em `tests/test_additional_requirements.py` para verificar requisitos que não estavam suficientemente cobertos pela suíte original, incluindo:

- processamento de mais de 200 reservas;
- desempate no ranking de hotéis;
- ausência de taxa de câmbio;
- arquivo com codificação inválida;
- precisão dos cálculos com `Decimal`;
- arredondamento do total após a soma dos valores;
- relatório sem diárias faturáveis.

Os testes originalmente fornecidos foram preservados.

## 4. Como executar

### Requisitos

- Python 3.11
- Dependências do projeto

### Instalação

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

**Linux/macOS:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

### Testes e análise estática

```bash
python -m pytest -q
python -m ruff check src tests
```

### Executar o relatório de validação

**PowerShell:**

```powershell
$env:PYTHONPATH = "src"
python -m onfly_report --input data/exemplo-validacao.csv --rates data/taxas_cambio.csv --output output/exemplo.json --top 5
```

**Linux/macOS:**

```bash
PYTHONPATH=src python -m onfly_report --input data/exemplo-validacao.csv --rates data/taxas_cambio.csv --output output/exemplo.json --top 5
```

### Executar com o dataset completo

**PowerShell:**

```powershell
python -m onfly_report --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json --top 5
```

**Linux/macOS:**

```bash
PYTHONPATH=src python -m onfly_report --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json --top 5
```

## 5. Resultados da validação

Ambiente utilizado: CPython 3.11.17, pytest 8.3.4 e Ruff 0.8.4.

- Suíte original, antes das correções: 5 falhas identificadas.
- Suíte final: **13 testes aprovados**.
- Ruff: **All checks passed!**

### Dataset de validação

| Indicador | Resultado |
|---|---:|
| Total de reservas | 12 |
| Confirmadas | 9 |
| Canceladas | 2 |
| No-show | 1 |
| Diárias faturáveis | 28 |
| Total faturado | R$ 7.566,00 |
| Média por diária | R$ 270,21 |

### Dataset completo

| Indicador | Resultado |
|---|---:|
| Total de reservas | 300 |
| Confirmadas | 235 |
| Canceladas | 31 |
| No-show | 34 |
| Diárias faturáveis | 1.347 |
| Total faturado | R$ 396.170,00 |
| Média por diária | R$ 294,11 |

## 6. Considerações finais

Também foram conferidos o schema do JSON, a ordenação dos meses e do ranking de hotéis, a representação dos valores monetários com duas casas decimais, o arredondamento `ROUND_HALF_UP`, a utilização de `Decimal` nos cálculos financeiros, o offset `-03:00` em `generated_at` e os códigos de saída previstos para os diferentes tipos de erro.