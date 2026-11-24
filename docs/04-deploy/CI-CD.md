# 🔄 Pipeline de CI/CD (GitHub Actions)

## Triggers
- Executado em `pull_request` e `push` na branch `main`.

## Etapas da Pipeline
1. **Lint & Format:** Executa ESLint e Prettier para garantir conformidade de código.
2. **Typecheck:** Executa `tsc --noEmit` para validar a integridade dos tipos TypeScript.
3. **Automated Tests:** Executa os testes unitários do Parser Engine.
4. **Build & Deploy:** 
   - Se os testes passarem na branch `main`, gera a imagem Docker.
   - Faz o push para o Container Registry e aplica o deploy automático na VPS/AWS.