# 🔄 Casos de Uso (Use Cases)

## UC01 - Processamento de Apólice PDF
- **Ator:** Operador da corretora.
- **Fluxo Principal:**
  1. O usuário faz o upload de um ou mais arquivos PDF na interface web.
  2. O backend identifica a seguradora e aciona o Parser Engine correspondente.
  3. O sistema extrai os 17 campos de cada veículo da frota.
  4. O sistema grava o resultado na tabela `apolices` e `frota_veiculos` com status `AGUARDANDO_REVISAO`.
  5. O usuário é redirecionado para a tela de conferência.

## UC02 - Revisão e Edição de Dados (Preview)
- **Ator:** Operador da corretora.
- **Fluxo Principal:**
  1. O usuário visualiza a tabela interativa na tela com os dados extraídos.
  2. Células que falharam na validação (ex: Chassi != 17 caracteres ou Placa inválida) aparecem destacadas.
  3. O usuário altera os dados manualmente direto na célula e clica em "Salvar e Exportar".

## UC03 - Geração e Download da Planilha Excel
- **Ator:** Operador da corretora.
- **Fluxo Principal:**
  1. O sistema lê os dados revisados do banco de dados.
  2. Abre o template `assets/excel-padrao.xlsx` via biblioteca de manipulação Excel (`openpyxl` / `ExcelJS`).
  3. Preenche a partir da linha `A2` e aplica as formatações.
  4. Disponibiliza o download do arquivo `.xlsx` gerado.