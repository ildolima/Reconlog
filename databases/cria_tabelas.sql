-- Arquivo: cria_tabelas.sql
-- Script para criar a estrutura do banco de dados para o sistema de produção.

-- Tabela principal para armazenar os dados da Ordem de Produção
CREATE TABLE ordem_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_sequencial INT UNIQUE NOT NULL,
    tipo_contrato VARCHAR(100),
    tipo_op VARCHAR(100),
    cliente VARCHAR(255),
    codigo VARCHAR(255),
    quantidade INT,
    largura DECIMAL(10, 2),
    comprimento DECIMAL(10, 2),
    pe_direito DECIMAL(10, 2),
    piso VARCHAR(255),
    data_emissao DATE,
    data_inicio_previsto DATE,
    data_termino_previsto DATE,
    data_carregamento DATE,
    setor VARCHAR(255),
    acessorios TEXT,
    observacoes TEXT
);

-- Tabela para os itens do Romaneio, ligada a uma Ordem de Produção
CREATE TABLE romaneio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    quantidade INT,
    materia_prima_utilizada DECIMAL(10, 2),
    FOREIGN KEY (ordem_producao_id) REFERENCES ordem_producao(id)
);

-- Tabela para os Apontamentos de produção, ligada a uma Ordem de Produção
CREATE TABLE apontamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL,
    turno VARCHAR(100),
    processo VARCHAR(255),
    maquina_operacao VARCHAR(255),
    operador VARCHAR(255),
    data_inicio DATE,
    hora_inicio TIME,
    data_termino DATE,
    hora_termino TIME,
    qualidade_aprovado BOOLEAN,
    FOREIGN KEY (ordem_producao_id) REFERENCES ordem_producao(id)
);