# 🏛️ Arquitetura do Sistema

## 1. Visão Geral
O sistema adota uma arquitetura em microsserviços/módulos desacoplados:
- **Frontend (Next.js):** Interface SPA/SSR para upload, preview e edição da frota.
- **Backend API (NestJS/Node ou FastAPI):** Orquestrador de requisições, autenticação e regras de negócio.
- **Parser Engine (Python/Node):** Serviço isolado focado no processamento de PDFs (PyMuPDF / pdfplumber) e integração com LLM fallback.
- **Fila de Processamento (Redis + BullMQ):** Gerencia o processamento assíncrono de PDFs pesados para não travar a API.
- **Banco de Dados (PostgreSQL / Supabase):** Armazenamento relacional dos dados das apólices e veículos.
- **Storage (AWS S3):** Armazenamento dos arquivos PDFs originais e templates Excel.

## 2. Fluxo de Dados (Data Flow)
`Cliente (Upload PDF)` ➔ `API Endpoint` ➔ `Bucket S3 (Salva PDF)` ➔ `Fila Redis` ➔ `Parser Engine (Extrai 17 campos)` ➔ `PostgreSQL (Grava Status/Dados)` ➔ `Frontend (Preview/Edição)` ➔ `Gerador Excel (Download .xlsx)`