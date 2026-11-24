# Operações de frotas: piloto local

Dois cliques em `iniciar-frotas.bat` sobem a API (porta 8000) e a interface (porta 3001) e abrem http://127.0.0.1:3001.

No primeiro acesso, o sistema pede para criar a conta administradora. Não existe conta nem senha padrão. Essa criação só funciona no próprio computador onde o sistema roda.

## Telas

- **Apólices** (tela inicial): lista de todos os PDFs importados, com seguradora, nº de veículos, pendências, última alteração e última versão do Excel. Busca por arquivo, seguradora ou autor; filtros Com pendências, Prontas para exportar, Exportadas e Com erro; filtro por seguradora.
- **Importar PDF**: janela de arrastar e soltar que aceita vários arquivos. Eles são lidos um por vez e cada um mostra a seguradora e o nº de veículos encontrados, ou o motivo do erro. Dá para fechar a janela e deixar terminar em segundo plano.
- **Revisão da apólice**: tabela dos 17 campos.
  - Funciona como planilha: setas navegam, Enter ou começar a digitar edita, Enter confirma e desce, Tab vai para a direita, Esc cancela, Delete limpa a célula.
  - Pendências ficam em amarelo só na célula afetada. O rodapé explica a pendência da célula selecionada. As setas ao lado do contador pulam de pendência em pendência; clicar no contador mostra só os veículos com pendência.
  - **PDF** abre o original ao lado; **Histórico** mostra as versões do Excel (com download) e cada alteração com item, placa, valor antigo e novo. A largura do painel ajusta arrastando a borda.
  - Tudo é salvo sozinho (indicador "Salvo" no topo). Se outra pessoa salvou a mesma apólice ao mesmo tempo, aparece um aviso para recarregar.
  - **Exportar Excel** pede o nome do arquivo, avisa se ainda há pendências e guarda cada exportação como uma versão nova.
- **Acessos** (só administrador): cadastrar funcionário com senha inicial, desativar e reativar. Desativar encerra as sessões da pessoa na hora.
- **Meu perfil** (menu no canto inferior esquerdo): foto, troca de senha e tema Claro, Escuro ou Sistema.

## Armazenamento e acesso

O piloto usa `data/workspace.sqlite3`, fora do controle de versão. Esse banco guarda contas, PDFs, revisões, eventos e arquivos Excel. `WORKSPACE_DB` permite definir outro caminho.

O armazenamento é local: não há backup automático. Para copiar o banco em uso, use a API de backup do SQLite; não copie só o arquivo principal enquanto houver gravações (o modo WAL usa arquivos auxiliares).

Sessões duram oito horas, com cookie HttpOnly e SameSite=Strict. Senhas são guardadas com scrypt e salt. Cinco tentativas erradas bloqueiam aquele e-mail por cinco minutos.

Antes de liberar para a empresa inteira: login corporativo (Google ou Microsoft), HTTPS com cookies seguros (`COOKIE_SECURE=true`), backup automático, política de retenção e um servidor sempre ligado.

## Inicialização manual

Na raiz do projeto:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000
```

Em `src/web`:

```powershell
npm.cmd run dev -- --hostname 127.0.0.1 -p 3001
```

## Próxima etapa

Os envios agendados ainda não existem. Ver `docs/ENVIO-AUTOMATICO.md`.
