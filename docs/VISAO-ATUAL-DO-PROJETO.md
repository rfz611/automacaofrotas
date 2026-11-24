# Visao atual do projeto

Atualizado em 28/09/2026.

Este documento resume a ideia do projeto ate o momento, incluindo o problema que ele resolve, a experiencia desejada para os funcionarios da corretora, o que ja foi implementado no piloto local e quais sao os proximos passos tecnicos e de produto.

## 1. Ideia central

O projeto e uma ferramenta interna para automatizar a operacao de frotas da corretora. A funcao principal e receber uma apolice em PDF, extrair os veiculos e coberturas, permitir que um funcionario revise os dados em uma interface densa e tecnica, e gerar um Excel padronizado para uso operacional.

O sistema nao esta sendo pensado como site publico, landing page ou produto de marketing. Ele e um backoffice de trabalho, feito para funcionarios que precisam ganhar tempo, reduzir retrabalho e manter controle sobre o que foi revisado, exportado e enviado.

A visao de longo prazo e transformar esse fluxo em uma plataforma operacional completa para documentos de seguro: leitura de PDFs, revisao assistida, historico, exportacoes versionadas, permissoes, envio automatico e integracoes com seguradoras.

## 2. Problema que o projeto resolve

Hoje a corretora recebe PDFs de diferentes seguradoras, cada uma com seu proprio layout. Esses documentos contem dados de varios veiculos, como placa, modelo, ano, chassi, bonus, codigo FIPE, franquia e coberturas.

O processo manual exige que um funcionario abra o PDF, procure as informacoes veiculo por veiculo, copie os dados para uma planilha, confira campos obrigatorios e depois prepare o arquivo final. Isso consome tempo, aumenta a chance de erro humano e dificulta acompanhar o que foi alterado ou exportado.

O projeto reduz esse trabalho repetitivo ao transformar o PDF em uma base editavel, mantendo o funcionario no controle da revisao final.

## 3. Publico-alvo

O publico inicial sao os funcionarios internos da corretora que lidam com apolices, frotas e planilhas de seguradoras.

Os perfis principais sao:

- operadores que importam PDFs e revisam os dados extraidos;
- analistas que conferem pendencias e coberturas;
- administradores que criam acessos, desativam usuarios e acompanham historico;
- futuramente, responsaveis por envios para seguradoras e automacoes externas.

## 4. Experiencia desejada

A interface deve parecer uma ferramenta de operacao, nao um SaaS generico. A referencia visual e uma UI de alta densidade, parecida com paineis internos como Vercel, Linear ou Stripe, mas aplicada ao contexto da corretora.

As decisoes visuais atuais seguem estes principios:

- uso da identidade da corretora com sobriedade, sem copiar o site publico;
- modo escuro tecnico, com fundo proximo de preto mas sem preto absoluto em excesso;
- modo claro com branco tecnico e azul institucional;
- layout compacto, com fontes pequenas, numeros tabulares e linhas densas;
- tabela como centro da experiencia;
- upload discreto, integrado ao fluxo, sem componentes chamativos;
- indicacao de pendencias diretamente na celula afetada, sem pintar a linha inteira;
- navegacao lateral redimensionavel, com areas voltadas para documentos, extracao e acessos;
- perfil do usuario com foto manual e preparacao futura para foto corporativa via Google ou Microsoft.

## 5. Fluxo principal do produto

O fluxo operacional planejado e:

1. O funcionario entra no sistema com uma conta interna.
2. Ele importa uma apolice em PDF.
3. O motor identifica a seguradora e tenta extrair os veiculos.
4. O sistema salva o PDF original e os dados extraidos.
5. O funcionario revisa os 17 campos padronizados em uma tabela editavel.
6. Campos com pendencias ficam sinalizados apenas na celula correspondente.
7. O funcionario pode abrir o PDF original ao lado da tabela para comparar.
8. As alteracoes e o nome do Excel sao salvos automaticamente.
9. O funcionario exporta uma versao do Excel.
10. Cada exportacao fica registrada como uma versao independente.
11. O historico mostra alteracoes, autores, datas e versoes geradas.

## 6. Os 17 campos padronizados

A revisao de frota esta estruturada em 17 colunas, que representam o modelo de dados necessario para gerar a planilha padrao da corretora:

- item da apolice;
- placa;
- marca;
- modelo;
- ano de fabricacao;
- ano modelo;
- chassi;
- classe de bonus;
- codigo FIPE;
- franquia casco;
- RCF danos materiais;
- RCF danos corporais;
- danos morais;
- APP passageiros;
- cobertura de vidros;
- assistencia;
- codigo de identificacao.

O campo de franquia casco representa a franquia, nao o valor do veiculo. Coberturas ausentes nao devem ser inventadas pelo sistema; elas ficam em branco ou sinalizadas para revisao quando necessario.

## 7. Estado atual do piloto

O piloto local ja possui as principais bases do produto:

- tela de login local;
- criacao do primeiro administrador;
- cadastro e desativacao de funcionarios por administrador;
- sessao autenticada;
- menu de perfil, tema e saida;
- foto de perfil manual;
- temas claro, escuro e sistema;
- navegacao lateral recolhivel e redimensionavel;
- upload de PDF;
- extracao de dados de frota;
- visualizacao do PDF original ao lado da tabela;
- tabela editavel com os 17 campos;
- busca por placa, chassi, item ou modelo;
- filtro de pendencias;
- salvamento automatico das revisoes;
- historico de documentos;
- historico de eventos por documento;
- exportacoes Excel versionadas;
- aviso ao exportar quando ainda ha pendencias, permitindo que o funcionario decida continuar.

Esse estado ja permite testar o fluxo principal: importar PDF, revisar, corrigir, salvar e exportar Excel.

## 8. Arquitetura atual

O projeto esta dividido em frontend, API, motor de extracao e armazenamento local.

O frontend usa Next.js, React, TypeScript e Tailwind. Ele concentra a experiencia de trabalho: login, documentos, extracao, tabela, historico, perfil, tema e gestao de acessos.

A API atual usa FastAPI em Python. Ela recebe PDFs, chama o pipeline de extracao, protege rotas autenticadas, salva documentos, revisoes, eventos, exportacoes e usuarios.

O banco local e SQLite, armazenado em `data/workspace.sqlite3`. Ele guarda contas, sessoes, PDFs, dados extraidos, revisoes, exportacoes, eventos e fotos de perfil.

O motor de extracao usa parsers deterministicos para layouts conhecidos e pode evoluir com fallback de IA quando um layout ainda nao for coberto.

## 9. Seguranca e acesso

No piloto local, o sistema ja tem algumas protecoes importantes:

- nao existe senha padrao;
- o primeiro acesso cria a conta administradora local;
- funcionarios sao cadastrados pelo administrador;
- senhas sao armazenadas como hash com salt;
- sessoes usam cookie HttpOnly e SameSite=Strict;
- tentativas incorretas de login sao limitadas;
- PDFs, revisoes e exportacoes exigem autenticacao;
- desativar um funcionario encerra suas sessoes.

Para uso real dentro da empresa, ainda e necessario evoluir a seguranca:

- login corporativo com Google Workspace ou Microsoft Entra ID;
- MFA quando aplicavel;
- HTTPS;
- cookies seguros em producao;
- backup automatico;
- politica de retencao de documentos;
- recuperacao de acesso;
- hospedagem continua, fora da maquina local.

## 10. Historico e rastreabilidade

Uma decisao importante do produto e nao tratar o Excel como um arquivo solto sem contexto. Cada documento importado passa a ter historico.

O sistema registra:

- quem importou o PDF;
- quando a extracao ocorreu;
- qual revisao esta ativa;
- quais campos foram alterados;
- quem fez as alteracoes;
- quais versoes de Excel foram geradas;
- quais arquivos podem ser baixados novamente.

Isso permite auditar o trabalho, retomar revisoes e evitar perda de informacao quando a equipe troca de turno ou quando um arquivo precisa ser conferido depois.

## 11. Envio automatico

O envio automatico ainda nao esta implementado. A ideia, ate o momento, e que o funcionario consiga preparar uma versao do Excel e agendar o envio para uma seguradora ou destino definido.

O fluxo recomendado e:

1. O funcionario gera uma exportacao imutavel do Excel.
2. Ele escolhe o destino, canal e horario de envio.
3. O sistema mostra um resumo com arquivo, versao, destino, data e hora.
4. O funcionario confirma o agendamento.
5. Um servico em execucao continua realiza o envio no horario combinado.
6. O resultado fica registrado: agendado, enviado, falha, cancelado ou resultado incerto.

A principal decisao pendente e o canal real usado pela corretora. Pode ser e-mail, API oficial de seguradora, portal de seguradora ou um fluxo orquestrado por n8n.

n8n e API nao sao opcoes opostas. Uma API pode ser o canal de entrega, enquanto o n8n pode coordenar horarios, repeticoes e chamadas externas. O sistema principal deve continuar sendo a fonte de verdade dos arquivos, versoes, autorizacoes e historico.

Para envios de madrugada, como 00:00 ou 03:00, a aplicacao precisa estar em um servidor sempre ligado. Um computador local desligado nao garante execucao.

## 12. Ordem recomendada de evolucao

A ordem atual do projeto e:

1. Aplicar a marca no cabecalho e definir a identidade do login.
2. Implementar login, salvamento das revisoes e historico de documentos.
3. Acrescentar PDF lado a lado, busca e filtros de pendencias.
4. Versionar exportacoes e registrar alteracoes.
5. Testar uma integracao com uma seguradora ou canal real de entrega.

As quatro primeiras etapas ja foram implementadas no piloto local. A quinta depende de escolher o primeiro canal de entrega e o primeiro teste autorizado.

## 13. Proximas melhorias de produto

As proximas melhorias mais importantes sao:

- melhorar a tela de historico para mostrar placa e item junto com cada alteracao;
- criar uma area de agendamentos de envio;
- definir o primeiro canal de envio automatico;
- preparar autenticacao corporativa;
- criar backup automatico;
- hospedar o sistema em ambiente sempre ligado;
- melhorar filtros por seguradora, status, data e pendencias;
- criar dashboard operacional com volume processado, tempo economizado e taxa de pendencias;
- permitir anexar observacoes internas por documento;
- permitir comparar exportacoes;
- melhorar o controle de permissoes por perfil.

## 14. Visao de longo prazo

No longo prazo, o sistema pode deixar de ser apenas um conversor de PDF para Excel e se tornar uma central operacional de documentos de seguro.

Essa central poderia:

- aprender com correcoes humanas;
- sugerir ajustes automaticos;
- detectar mudancas de layout de seguradoras;
- medir produtividade da equipe;
- enviar arquivos automaticamente;
- integrar com seguradoras;
- armazenar evidencias e logs;
- padronizar processos entre funcionarios;
- futuramente, ser adaptada para outras corretoras.

O foco imediato, porem, continua sendo validar bem o fluxo principal da corretora: extrair, revisar, corrigir, exportar e manter historico confiavel.

