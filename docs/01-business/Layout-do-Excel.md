# # Layout do Excel

## Objetivo

Este documento descreve o layout padrão utilizado pela corretora para a geração da planilha consolidada de frotas a partir das apólices processadas.

---

## Mapeamento de Colunas

| Coluna | Campo | Obrigatório | Origem | Tipo de Dado | Exemplo / Formatação |
| :---: | | :--- | :---: | :---: | :---: | :--- |
| **A** | Item Apólice | Sim | PDF | Integer | `1` |
| **B** | Placa | Sim | PDF | String | `ABC1D23` (sem traço/espaço) |
| **C** | Marca | Sim | PDF | String | `VOLKSWAGEN` |
| **D** | Modelo | Sim | PDF | String | `NOVO GOLTRENDLINE 1.0` |
| **E** | Ano Fab | Sim | PDF | Integer | `2014` |
| **F** | Ano Mod | Sim | PDF | Integer | `2015` |
| **G** | Chassi | Sim | PDF | String | `9BWAA45U7FP102941` |
| **H** | Bônus | Sim | PDF | Integer | `4` |
| **I** | FIPE | Sim | PDF | String/Int | `538300` |
| **J** | Casco | Sim | PDF | Decimal | `2319.60` |
| **K** | RCF DM | Sim | PDF | Decimal | Conforme a proposta |
| **L** | RCF DC | Sim | PDF | Decimal | Conforme a proposta |
| **M** | DMO | Sim | PDF | Decimal | Conforme a proposta |
| **N** | APP | Não | PDF | Decimal | `0.00` ou *Vazio* |
| **O** | Vidros | Não | PDF | Decimal | `25000.00` (limite da cobertura; vazio se o PDF não traz limite) |
| **P** | Assist | Não | PDF | String | `Incluso` ou `24h` |
| **Q** | CI | Não | PDF | String | `J01Cls` |

---

## Regras de Negócio e Valores Padrão

1. **RCF e DMO sem valores padrão:**
   - Os valores devem ser extraídos do bloco do próprio veículo na proposta.
   - Se não forem localizados ou não estiverem contratados, permanecem vazios para revisão; nunca são inferidos.

2. **Formatação de Moeda:**
   - Os campos `Casco`, `RCF DM`, `RCF DC`, `DMO`, `APP` e `Vidros` devem ser inseridos como valores numéricos (`decimal`), aplicando a formatação de moeda BRL no arquivo Excel final.

3. **Início da Inserção:**
   - A escrita dos dados deve começar a partir da linha **`2`** (`A2:Q2`), preservando a linha de cabeçalho amarela intacta presente em `assets/excel-padrao.xlsx`.
