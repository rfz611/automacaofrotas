RN-01 (Validação de Chassi): Todo chassi deve conter exatamente 17 caracteres alfanuméricos. Se for menor ou maior, a linha deve ser marcada com flag de atenção no preview.

RN-02 (Padronização de Placa): Placas devem ser convertidas automaticamente para caixa alta e sem hífen (ex: ABC-1234 ou ABC1D23 viram ABC1234 e ABC1D23).

RN-03 (Formatos de Moeda): Valores numéricos das colunas de prêmio e coberturas (Casco, RCF, DMO, APP) devem ser salvos em padrão decimal de banco de dados (Float/Decimal), mas formatados como moeda brasileira (R$ 0.000,00) na exportação da planilha.

RN-04 (Itens Duplicados): O sistema deve alertar o usuário se houver mais de um veículo com a mesma placa ou chassi dentro do mesmo arquivo PDF.

RN-05 (Consolidação por Veículo): Continuações do mesmo item em páginas diferentes devem ser unidas pela combinação de item, placa e chassi. Cada veículo deve gerar uma única linha e nenhuma informação pode ser herdada do item anterior ou seguinte.

RN-06 (Coberturas sem Inferência): RCF DM, RCF DC e DMO variam por proposta. Valores ausentes permanecem vazios para revisão e nunca recebem defaults.

RN-07 (Revisão por Exceção): Um layout novo deve ser validado com arquivo representativo e convertido em teste de referência. Arquivos posteriores do mesmo layout passam por validações automáticas de quantidade, sequência, identidade, duplicidade e formato; a revisão humana concentra-se nos itens sinalizados.

RN-08 (Casco): A coluna CASCO recebe a franquia do veículo quando ela estiver explicitamente informada. Casco não contratado permanece vazio; prêmio, LMI numérico e valores sintéticos como zero não substituem a franquia.

RN-09 (Cobertura de Vidros): A simples presença de termos como para-brisa ou vidros em tabelas de participação/franquia não comprova contratação. A coluna recebe o limite (LMI) da cobertura de vidros, em R$. Quando o PDF não traz limite (ex.: Sura, que só informa o prêmio do serviço, e Bradesco, que só cita a cláusula), a coluna fica vazia; prêmio não substitui o limite.
