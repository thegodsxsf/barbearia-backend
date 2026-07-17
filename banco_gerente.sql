CREATE TABLE IF NOT EXISTS gerentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    nome TEXT DEFAULT 'Gerente'
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    servico_nome TEXT NOT NULL,
    valor REAL NOT NULL DEFAULT 0,
    cliente_nome TEXT NOT NULL,
    cliente_telefone TEXT,
    cliente_cpf TEXT,
    data_agendada TEXT,
    hora_agendada TEXT,
    corte_em_casa TEXT DEFAULT 'nao',
    endereco TEXT,
    complemento TEXT,
    observacoes TEXT,
    pagamento TEXT,
    profissional TEXT,
    data_assinatura TEXT,
    status TEXT NOT NULL DEFAULT 'pendente',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS caixa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    valor REAL NOT NULL,
    descricao TEXT,
    pagamento TEXT,
    pedido_id INTEGER,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

CREATE TABLE IF NOT EXISTS comandas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT NOT NULL UNIQUE,
    cliente_nome TEXT NOT NULL,
    cliente_telefone TEXT,
    profissional TEXT,
    servicos TEXT,
    valor_total REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'aberta',
    pagamento TEXT DEFAULT 'pendente',
    observacoes TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_pagamento DATETIME
);

CREATE TABLE IF NOT EXISTS repasses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional TEXT NOT NULL,
    servico_nome TEXT NOT NULL,
    valor_servico REAL NOT NULL,
    comissao REAL NOT NULL,
    porcentagem REAL DEFAULT 50,
    data_servico DATETIME,
    status TEXT DEFAULT 'pendente',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    pago_em DATETIME
);

CREATE TABLE IF NOT EXISTS horarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia_semana INTEGER NOT NULL,
    abertura TEXT NOT NULL,
    fechamento TEXT NOT NULL,
    pausa_inicio TEXT,
    pausa_fim TEXT,
    ativo INTEGER DEFAULT 1
);

INSERT OR REPLACE INTO gerentes (id, usuario, senha_hash, nome) VALUES 
(1, 'barbe', 'barbe', 'Gerente');

INSERT OR REPLACE INTO horarios (id, dia_semana, abertura, fechamento, pausa_inicio, pausa_fim, ativo) VALUES
(1, 0, '09:00', '12:00', NULL, NULL, 1),
(2, 1, '09:00', '19:00', '12:00', '14:30', 1),
(3, 2, '09:00', '19:00', '12:00', '14:30', 1),
(4, 3, '09:00', '19:00', '12:00', '14:30', 1),
(5, 4, '09:00', '19:00', '12:00', '14:30', 1),
(6, 5, '09:00', '19:00', '12:00', '14:30', 1),
(7, 6, '09:00', '18:00', '12:00', '14:30', 1);
