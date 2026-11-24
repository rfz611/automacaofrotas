# ⚙️ Parser Engine Specification

## 1. Dicionário de Dados do Modelo Excel (corretora)

O parser DEVE extrair e normalizar os dados do PDF para atender ao seguinte esquema de dados estrito:

| Campo DTO | Tipo de Dado | Coluna Excel | Validação / Regra de Negócio |
| :--- | :--- | :--- | :--- |
| `item_apolice` | Integer | A | Numérico sequencial |
| `placa` | String | B | Uppercase, regex: `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$` |
| `marca` | String | C | Uppercase, sem caracteres especiais |
| `modelo` | String | D | Descrição completa do veículo |
| `ano_fabricacao` | Integer | E | 4 dígitos |
| `ano_modelo` | Integer | F | 4 dígitos |
| `chassi` | String | G | Exact 17 chars, regex alfanumérico |
| `classe_bonus` | Integer | H | Inteiro entre 0 e 10 |
| `codigo_fipe` | String | I | String/Código da FIPE |
| `valor_casco` | Decimal | J | Formato moeda, separador de decimal `.` |
| `rcf_danos_materiais`| Decimal | K | Formato moeda |
| `rcf_danos_corporais` | Decimal | L | Formato moeda |
| `danos_morais` | Decimal | M | Formato moeda |
| `app_passageiros` | Decimal | N | Formato moeda (opcional) |
| `cobertura_vidros` | String | O | Descrição curta |
| `assistencia` | String | P | Descrição do serviço (ex: "Incluso", "24h") |
| `codigo_identificacao`| String | Q | Código CI da seguradora |

---

## 2. Arquitetura do Engine (Python FastApi / Worker)

A extração deve ser isolada em um serviço (Engine) separado da API principal:

```text
[PDF Input] 
    │
    ▼
[01. Detection Service] ──► Identifica Seguradora (Porto, Tokio, Bradesco)
    │
    ├─► [02A. Regex/Table Parser] ──► Extração rápida (pdfplumber)
    │        │
    │        └─ (Se falhar ou layout for novo)
    │                 │
    └───────────────► └─► [02B. LLM Fallback Service] ──► Extração via Claude 3.5 / OpenAI
                                │
                                ▼
                     [03. Data Normalizer] ──► Valida Placas, Chassis e Formatos
                                │
                                ▼
                     [04. Excel Generator] ──► Preenche o template `.xlsx`