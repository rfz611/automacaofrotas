-- Tabela de Histórico de Arquivos Processados
CREATE TABLE apolices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_arquivo VARCHAR(255) NOT NULL,
    seguradora VARCHAR(100) NOT NULL,
    quantidade_itens INT NOT NULL,
    status VARCHAR(50) DEFAULT 'PROCESSADO', -- 'PROCESSADO', 'ERRO', 'AGUARDANDO_REVISAO'
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Veículos Extraídos da Frota
CREATE TABLE frota_veiculos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apolice_id UUID REFERENCES apolices(id) ON DELETE CASCADE,
    item_apolice INT,
    placa VARCHAR(10),
    marca VARCHAR(100),
    modelo VARCHAR(255),
    ano_fabricacao INT,
    ano_modelo INT,
    chassi VARCHAR(17),
    classe_bonus INT,
    codigo_fipe VARCHAR(50),
    valor_casco DECIMAL(12,2),
    rcf_danos_materiais DECIMAL(12,2),
    rcf_danos_corporais DECIMAL(12,2),
    danos_morais DECIMAL(12,2),
    app_passageiros DECIMAL(12,2),
    cobertura_vidros VARCHAR(100),
    assistencia VARCHAR(100),
    codigo_identificacao VARCHAR(100)
);