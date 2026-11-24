# 🤖 IA & Parser Engine Integration

- **LLM Provider:** Anthropic API (Claude 3.5 Sonnet) / OpenAI (GPT-4o)
- **Estratégia de Parsing:**
  1. Tentativa via Parser Local Determinístico (PDF Plumber / PyMuPDF)
  2. Fallback para API de LLM via Structured Outputs (JSON Schema estrito dos 17 campos)