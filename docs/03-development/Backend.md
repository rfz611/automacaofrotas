# 🟢 Backend Stack & Architecture

- **Runtime / Framework:** Node.js com NestJS (TypeScript) *[ou Python com FastAPI, dependendo da sua escolha final]*
- **Gerenciador de Pacotes:** pnpm (ou npm/yarn)
- **ORM / Query Builder:** Prisma ORM ou Drizzle ORM
- **Validação de DTOs:** `class-validator` e `class-transformer` (ou Zod)
- **Processamento de Filas / Async:** BullMQ com Redis (para gerenciar os uploads pesados de PDFs em segundo plano)
- **Geração de Excel:** `exceljs` ou `openpyxl`