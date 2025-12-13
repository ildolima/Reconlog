-- Schema do Sistema de Controle de Produção
-- Execute este script no console MySQL do PythonAnywhere

SET FOREIGN_KEY_CHECKS = 0;

-- Tabela de Usuários
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    nivel_acesso ENUM('admin', 'supervisor', 'operador') DEFAULT 'operador',
    turno ENUM('manha', 'tarde', 'noite', 'madrugada') DEFAULT 'manha',
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_login DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela de Produtos/Itens
CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    unidade_medida VARCHAR(20) DEFAULT 'UN',
    peso_unitario DECIMAL(10,3),
    especificacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela de Ordens de Produção
CREATE TABLE ordens_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_ordem VARCHAR(50) UNIQUE NOT NULL,
    produto_id INT NOT NULL,
    
    -- Dados da Ordem
    data_ordem DATE NOT NULL,
    turno ENUM('manha', 'tarde', 'noite', 'madrugada') NOT NULL,
    usuario_responsavel_id INT NOT NULL,
    
    -- Quantidades Planejadas
    quantidade_planejada DECIMAL(10,2) NOT NULL,
    peso_planejado DECIMAL(10,3),
    
    -- Quantidades Realizadas
    quantidade_produzida DECIMAL(10,2) DEFAULT 0,
    peso_produzido DECIMAL(10,3) DEFAULT 0,
    
    -- Controle de Qualidade
    quantidade_aprovada DECIMAL(10,2) DEFAULT 0,
    quantidade_rejeitada DECIMAL(10,2) DEFAULT 0,
    motivo_rejeicao TEXT,
    
    -- Tempos
    hora_inicio TIME,
    hora_fim TIME,
    tempo_producao_minutos INT,
    tempo_parada_minutos INT DEFAULT 0,
    motivo_parada TEXT,
    
    -- Status
    status ENUM('planejada', 'em_producao', 'pausada', 'finalizada', 'cancelada') DEFAULT 'planejada',
    
    -- Observações
    observacoes TEXT,
    problemas_encontrados TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (usuario_responsavel_id) REFERENCES usuarios(id),
    
    INDEX idx_numero_ordem (numero_ordem),
    INDEX idx_data_ordem (data_ordem),
    INDEX idx_status (status),
    INDEX idx_turno (turno)
);

-- Tabela de Apontamentos de Produção (Registros por Hora)
CREATE TABLE apontamentos_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL,
    usuario_id INT NOT NULL,
    
    -- Dados do Apontamento
    data_apontamento DATE NOT NULL,
    hora_apontamento TIME NOT NULL,
    
    -- Quantidades no Período
    quantidade_periodo DECIMAL(10,2) NOT NULL,
    peso_periodo DECIMAL(10,3),
    
    -- Qualidade no Período
    quantidade_aprovada_periodo DECIMAL(10,2) DEFAULT 0,
    quantidade_rejeitada_periodo DECIMAL(10,2) DEFAULT 0,
    
    -- Observações do Período
    observacoes_periodo TEXT,
    problemas_periodo TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    
    INDEX idx_ordem_data (ordem_producao_id, data_apontamento),
    INDEX idx_data_hora (data_apontamento, hora_apontamento)
);

-- Tabela de Paradas de Produção
CREATE TABLE paradas_producao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_producao_id INT NOT NULL,
    usuario_id INT NOT NULL,
    
    -- Dados da Parada
    data_parada DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME,
    duracao_minutos INT,
    
    -- Motivo da Parada
    tipo_parada ENUM('manutencao', 'falta_material', 'problema_qualidade', 'troca_produto', 'almoco', 'outros') NOT NULL,
    motivo_detalhado TEXT,
    
    -- Status
    status ENUM('ativa', 'finalizada') DEFAULT 'ativa',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ordem_producao_id) REFERENCES ordens_producao(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    
    INDEX idx_ordem_data (ordem_producao_id, data_parada),
    INDEX idx_tipo_parada (tipo_parada)
);

-- Inserir dados iniciais
INSERT INTO usuarios (nome, email, senha_hash, nivel_acesso, turno) VALUES 
('Administrador', 'admin@producao.com', 'pbkdf2:sha256:260000$salt$hash', 'admin', 'manha'),
('Supervisor Manhã', 'supervisor.manha@producao.com', 'pbkdf2:sha256:260000$salt$hash', 'supervisor', 'manha'),
('Supervisor Tarde', 'supervisor.tarde@producao.com', 'pbkdf2:sha256:260000$salt$hash', 'supervisor', 'tarde'),
('Operador 1', 'operador1@producao.com', 'pbkdf2:sha256:260000$salt$hash', 'operador', 'manha'),
('Operador 2', 'operador2@producao.com', 'pbkdf2:sha256:260000$salt$hash', 'operador', 'tarde');

-- Produtos de exemplo
INSERT INTO produtos (codigo, nome, descricao, unidade_medida, peso_unitario) VALUES 
('PROD001', 'Produto A', 'Descrição do Produto A', 'UN', 1.500),
('PROD002', 'Produto B', 'Descrição do Produto B', 'KG', 2.300),
('PROD003', 'Produto C', 'Descrição do Produto C', 'UN', 0.750),
('PROD004', 'Produto D', 'Descrição do Produto D', 'L', 1.000),
('PROD005', 'Produto E', 'Descrição do Produto E', 'UN', 3.200);

SET FOREIGN_KEY_CHECKS = 1;