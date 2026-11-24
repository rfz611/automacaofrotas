<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Front-end corretora (src/web)

- Next.js App Router, React 19, Tailwind 4. Sem biblioteca de componentes: os estilos base ficam em `app/globals.css` (`.btn`, `.field`, `.card`, `.badge`).
- Cores só por variável de tema (`bg-surface`, `text-ink-2`, `bg-brand`...). Claro e escuro são definidos em `:root` e `[data-theme="dark"]`.
- Toda chamada à API passa por `lib/api.ts` → `/api/workspace/*` (proxy para o FastAPI na porta 8000).
- Regras de pendência: `lib/review.ts`. Elas existem também em `src/workspace/review.py` (contador da lista). Mudou uma, mude a outra.
- Modo demonstração: `NEXT_PUBLIC_DEMO=1` troca a marca por "Frotas" neutra (`lib/brand.ts`).
