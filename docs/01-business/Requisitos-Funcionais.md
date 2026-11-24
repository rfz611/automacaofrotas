RF-001 — Login

O sistema deverá permitir que usuários autenticados acessem a plataforma.

RF-002 — Dashboard

Após o login, o usuário visualizará um painel contendo:

Quantidade de PDFs processados.
Quantidade de veículos processados.
Últimos arquivos enviados.
Histórico.
RF-003 — Upload

O usuário poderá enviar:

1 PDF.
Vários PDFs.
Arrastar arquivos (Drag and Drop).

O sistema aceitará somente:

.pdf
RF-004 — Processamento

Após o upload:

O sistema deverá:

Detectar a seguradora.
Selecionar o parser correto.
Extrair os veículos.
Validar os dados.
Salvar o resultado.
RF-005 — Preview

Antes do Excel ser gerado:

O usuário visualizará todos os veículos.

Será possível editar qualquer campo.

RF-006 — Excel

Após aprovação:

O sistema gerará um Excel seguindo o layout padrão da corretora.

RF-007 — Histórico

Todos os processamentos ficarão armazenados.

Será possível visualizar:

data
usuário
arquivo
quantidade de veículos
status
download
RF-008 — Download

O usuário poderá baixar novamente:

PDF original
JSON
Excel
RF-009 — Pesquisa

Pesquisar por:

placa
seguradora
cliente
data
RF-010 — Usuários

Administrador poderá:

criar usuários
remover usuários
alterar senha
RF-011 — Logs

O sistema registrará:

upload
processamento
erros
downloads
RF-012 — Parser

O parser deverá:

detectar layout
extrair dados
normalizar dados
validar dados
RF-013 — IA (Futuro)

Quando houver dúvidas:

A IA poderá sugerir correções.

RF-014 — Scheduler (Futuro)

O usuário poderá:

Selecionar um Excel.

Selecionar um horário.

Selecionar um destino.

O sistema fará o envio automaticamente.

RF-015 — Controle de versões dos arquivos

Se um PDF for reprocessado, o sistema mantém o histórico das versões.

RF-016 — Comparação de processamentos

Permitir comparar:

PDF original.
Dados extraídos.
Excel gerado.

Isso ajuda muito na conferência.

RF-017 — Tratamento de erros

Se o parser não conseguir identificar um campo, o sistema destaca o problema no Preview para o usuário corrigir.

RF-018 — Estatísticas

Mostrar indicadores como:

PDFs processados por dia.
Veículos processados por mês.
Tempo médio de processamento.
Taxa de sucesso do parser.
Quantidade de correções manuais.

Esses dados podem mostrar para a corretora o impacto real da automação.