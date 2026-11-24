# 📡 Especificação das APIs (REST)

Este documento define os contratos de entrada e saída (payloads) para a comunicação entre o Frontend (Next.js) e o Backend.

---

## Endpoints Principais

### 1. Upload e Parsing de Apólice
- **HTTP Method:** `POST`
- **Route:** `/api/v1/apolices/upload`
- **Content-Type:** `multipart/form-data`
- **Request Body:** `file` (Arquivo PDF da apólice)
- **Response (202 Accepted):**
  ```json
  {
    "job_id": "uuid-da-fila",
    "status": "PROCESSING",
    "message": "Apólice enviada para a fila de processamento."
  }

  {
  "id": "uuid-apolice",
  "seguradora": "Porto Seguro",
  "status": "AGUARDANDO_REVISAO",
  "veiculos": [
    {
      "item": 1,
      "placa": "ABC1D23",
      "chassi": "9BWAA45U7FP102941",
      "casco": 2319.60,
      "rcf_dm": 200000.00,
      "rcf_dc": 200000.00,
      "dmo": 50000.00,
      "flags_atencao": []
    }
  ]

POST /api/v1/apolices/:id/export

Body: Objeto JSON com os 17 campos revisados pelo usuário.

Response (200 OK): Binary stream do arquivo .xlsx gerado.