# Frontend (src/web)

- **Framework:** Next.js 16 (App Router), React 19, TypeScript
- **Estilo:** Tailwind CSS 4 com variáveis de tema (claro e escuro) em `app/globals.css`. Sem biblioteca de componentes.
- **Ícones:** lucide-react
- **Fontes:** Inter (interface) e JetBrains Mono (placa, chassi, FIPE, C.I.)
- **API:** `lib/api.ts` chama `/api/workspace/*`, que o Next repassa para o FastAPI (`PARSER_API_URL`, padrão `http://127.0.0.1:8000`).

## Rotas

| Rota | Tela |
| --- | --- |
| `/entrar` | Login e criação do primeiro administrador |
| `/` | Lista de apólices e importação de PDFs |
| `/apolices/[id]` | Revisão: tabela dos 17 campos, PDF, histórico, exportação |
| `/acessos` | Gestão de funcionários (só administrador) |

## Regras de pendência

Ficam em `lib/review.ts` e são repetidas em `src/workspace/review.py` (usado para o contador da lista). Ao mudar uma regra, mude as duas e rode `tests/test_review_pending.py`.
