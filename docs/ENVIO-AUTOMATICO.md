# Revisão do roteiro e preparação dos envios

Verificação: 28/09/2026. Este documento descreve o estado encontrado e a próxima implementação; não representa um serviço de envio já ativo.

## Roteiro original

| Etapa | Situação no piloto local | Evidência |
| --- | --- | --- |
| Marca e identidade do login | Implementada | Brand, WorkspaceHeader, Login e temas em globals.css |
| Login, salvamento e histórico | Implementada localmente | Sessões autenticadas, salvamento automático com controle de revisão, documentos em SQLite |
| PDF lado a lado, busca e pendências | Implementada | Visualização do original, busca por placa/chassi/item/modelo e filtro de pendências em page.tsx |
| Versões de exportação e alterações | Implementada | Binários Excel independentes por versão, eventos com autor e data, valores anteriores e novos |
| Teste de integração com uma seguradora | Pendente | Nenhum canal de entrega, destinatário ou credencial de integração configurado; não existe agendador de envio |

Os testes de workspace foram executados em banco temporário separado: acesso e revogação, persistência, conflito de revisões, imutabilidade de exportações, importação do PDF de exemplo e foto de perfil. A presença dos controles de PDF/busca/filtro foi conferida no código; esta rodada não fez uma nova revisão visual autenticada de todas as telas.

O piloto não equivale a uma implantação corporativa: autenticação federada/MFA, backup automático e execução contínua em servidor ainda não estão configurados. O histórico de alterações registra o identificador do veículo, mas a tela de detalhes ainda pode melhorar exibindo placa/item junto ao campo alterado.

## Primeiro fluxo de envio

Objetivo: o operador prepara durante o expediente uma versão do Excel para entrega em uma data e hora determinadas, inclusive 00:00 ou 03:00.

1. Selecionar uma exportação existente e imutável. Edições posteriores no documento não alteram o anexo agendado.
2. Informar seguradora/destino, canal de entrega e destinatários exigidos pelo canal. Para e-mail, incluir assunto e mensagem.
3. Selecionar data, hora e fuso explícito, inicialmente America/Sao_Paulo. Converter o instante para UTC no armazenamento. Não presumir recorrência diária.
4. Exibir resumo com arquivo, versão, destino e horário; registrar a confirmação do funcionário que autorizou o envio.
5. Manter o agendamento e as tentativas em armazenamento persistente. Fechar o navegador não pode interromper a execução.
6. Permitir cancelar antes de iniciar o envio. Alterar anexo/destinatário de um envio confirmado deve exigir nova confirmação.
7. Registrar estados separados: rascunho, agendado, em execução, aceito pelo provedor, falha, resultado incerto e cancelado. Aceitação pelo provedor não comprova recebimento ou leitura pela seguradora.
8. Guardar identificador do provedor e das tentativas. Usar chave de idempotência quando disponível. Se houver timeout depois de uma possível aceitação, reconciliar o resultado antes de repetir, evitando duplicidade.
9. Se o serviço ficar indisponível no horário, marcar o envio como atrasado e pedir decisão do operador; não disparar automaticamente horas depois sem uma política acordada.

## Canal e execução

O canal precisa refletir como a empresa entrega hoje:

- E-mail: conectar a caixa corporativa autorizada e confirmar que a seguradora recebe o Excel nesse endereço.
- API: obter documentação, ambiente de testes e acesso oficial da seguradora.
- Portal: verificar integração oficial e condições de uso antes de decidir por automação do navegador; não presumir que existe API.

API e n8n não são alternativas equivalentes: uma API pode ser o canal de entrega, enquanto o n8n pode coordenar sua execução. A escolha depende do canal, da hospedagem e de quem dará manutenção. O sistema deve continuar sendo a fonte dos arquivos, versões e autorizações.

Para operar com o computador do usuário desligado, será necessário um serviço hospedado continuamente, com armazenamento persistente. A aplicação local atual não garante execução durante a madrugada.

## Informações necessárias para o primeiro teste real

- Canal atual de entrega: e-mail, portal ou API.
- Uma seguradora e destino de teste autorizado, além de um arquivo sem dados reais ou autorizado para esse teste.
- Conta remetente/provedor, se for e-mail; documentação e sandbox, se for API.
- Onde o serviço poderá permanecer em execução.

Credenciais devem ser configuradas no ambiente do servidor, não enviadas pela conversa. Até esses dados serem definidos, não haverá disparos externos. O primeiro teste deverá acompanhar o resultado até a confirmação disponível no canal, antes de expandir para outros destinos.

## Atualização 10/11/2026 — o que já sabemos e o que perguntar ao Robert

Sabemos: o envio hoje é feito **pelo portal da seguradora**; o portal só libera o envio **de madrugada**; os envios **se repetem toda semana/mês**; **não há computador ligado de madrugada**, então a execução precisaria ser na nuvem.

Perguntas pendentes:
1. Quais seguradoras recebem esses envios e por quais portais?
2. Qual é exatamente a janela de horário liberada (início e fim) em cada portal?
3. O login do portal pede código no celular (2 etapas) ou CAPTCHA?
4. A seguradora oferece outro canal automático (e-mail, SFTP ou API)? Perguntar ao gerente da conta.
5. O arquivo enviado é sempre o mesmo ou muda a cada envio? Ele sai do próprio sistema de Frotas?
6. Qual provedor de e-mail a empresa usa (Microsoft 365, Google Workspace, outro)?

Decisão adiada até essas respostas. Automação de portal via navegador é a última opção (frágil e pode violar os termos de uso).
