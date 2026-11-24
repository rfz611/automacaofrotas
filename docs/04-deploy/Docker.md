### 📂 `docs/04-deploy/`

#### 📄 `Docker.md`
> Garante ambiente idêntico no desenvolvimento local e no servidor.

```markdown
# 🐳 Configuração do Ambiente Docker

## 1. Mapeamento de Serviços (`docker-compose.yml`)
- `postgres`: Banco de dados relacional (Porta 5432).
- `redis`: Gerenciamento de filas assíncronas (Porta 6379).
- `backend`: Container da API / Parser Engine (Porta 3000 ou 8000).
- `frontend`: Container do Next.js (Porta 3001).

## 2. Diretrizes de Build
- Utilizar **Multi-stage builds** para manter as imagens finais leves e seguras em produção.
- Utilizar imagens de base alpinas (`node:20-alpine` ou `python:3.11-slim