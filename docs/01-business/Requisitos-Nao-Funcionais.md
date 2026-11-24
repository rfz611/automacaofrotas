# 03 - Requisitos Não Funcionais

Versão: 1.0

Projeto: Sistema de Automação de Frotas

Cliente: a corretora

Última atualização: 16/07/2025

---

# Objetivo

Este documento descreve os requisitos não funcionais do Sistema de Automação de Frotas. Esses requisitos definem como o sistema deve se comportar em relação a desempenho, segurança, disponibilidade, usabilidade, escalabilidade e qualidade.

---

# RNF-001 - Desempenho

O sistema deverá processar arquivos PDF de forma eficiente.

Critérios:

- PDFs pequenos (<50 veículos): até 10 segundos.
- PDFs médios (50–300 veículos): até 30 segundos.
- PDFs grandes (>300 veículos): processamento assíncrono.
- PDFs muito grandes (>1500 veículos): utilização de fila de processamento.

---

# RNF-002 - Escalabilidade

O sistema deverá permitir a inclusão de novas seguradoras sem necessidade de alterar os parsers existentes.

Cada seguradora deverá possuir um parser independente.

---

# RNF-003 - Disponibilidade

O sistema deverá estar disponível 24 horas por dia.

Objetivo mínimo:

99,5% de disponibilidade.

---

# RNF-004 - Segurança

O acesso deverá exigir autenticação.

As senhas deverão ser armazenadas utilizando algoritmo de hash.

Os uploads deverão aceitar apenas arquivos PDF.

---

# RNF-005 - Integridade dos Dados

Nenhum PDF poderá ser alterado durante o processamento.

O arquivo original deverá permanecer armazenado para auditoria.

---

# RNF-006 - Rastreabilidade

Todo processamento deverá gerar um histórico contendo:

- usuário;
- data;
- horário;
- arquivo enviado;
- seguradora detectada;
- quantidade de veículos;
- status;
- tempo de processamento.

---

# RNF-007 - Usabilidade

O sistema deverá possuir interface simples, permitindo que um colaborador consiga realizar um processamento sem treinamento técnico.

---

# RNF-008 - Compatibilidade

O sistema deverá funcionar nos principais navegadores modernos:

- Google Chrome
- Microsoft Edge
- Mozilla Firefox

---

# RNF-009 - Exportação

O Excel gerado deverá seguir exatamente o layout definido pela corretora.

---

# RNF-010 - Confiabilidade

Campos não identificados deverão ser destacados para conferência humana antes da geração do Excel.

---

# RNF-011 - Logs

O sistema deverá registrar:

- uploads;
- erros;
- downloads;
- alterações realizadas no preview.

---

# RNF-012 - Escalabilidade de Clientes

A arquitetura deverá permitir que o sistema seja adaptado futuramente para atender múltiplas corretoras de seguros sem necessidade de reescrita da aplicação.

---

# RNF-013 - Arquitetura Modular

Os módulos Frontend, Backend e Parser Engine deverão possuir responsabilidades independentes, permitindo evolução e manutenção isoladas.

---

# RNF-014 - Inteligência Artificial

O sistema deverá permitir integração futura com modelos de IA para auxílio na interpretação de documentos, validação de dados e correção automática de inconsistências.

---

# RNF-015 - Auditoria

Toda alteração realizada manualmente após o parsing deverá ficar registrada para fins de auditoria.

---

# Critérios de Aceite

O sistema somente será considerado apto para produção quando atender aos requisitos descritos neste documento.

---

# Histórico de Alterações

| Versão | Data | Alteração |
|---------|------|-----------|
| 1.0 | 16/07/2025 | Documento inicial |