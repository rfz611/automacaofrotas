# 🛠️ Coding Standards & Diretrizes de Desenvolvimento

## 1. Princípios Gerais
- **Código Limpo (Clean Code):** Funções pequenas, responsabilidade única (SRP) e nomes de variáveis autoexplicativos em inglês.
- **Tipagem Estrita:** Uso obrigatório de TypeScript (Frontend/Backend Node) e Type Hints (Backend Python). Uso de `any` é estritamente proibido.
- **Validação de Schemas:** Utilizar bibliotecas de validação de DTOs (`Zod` ou `Class-Validator`) na entrada da API para garantir integridade.

## 2. Padrões do Parser Engine
- **Tratamento de Exceções:** Tratar falhas de leitura de PDF de forma graciosa. Se um campo não for localizado, retornar `null` e marcar a linha para revisão humana em vez de quebrar a aplicação.
- **Logs Estruturados:** Registrar logs de processamento indicando: Seguradora detectada, tempo de execução e quantidade de itens extraídos.