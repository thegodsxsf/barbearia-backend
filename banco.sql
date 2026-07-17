-- ============================================================
-- BANCO DE DADOS - Barbearia Studio Leblon
-- ============================================================

CREATE TABLE IF NOT EXISTS barbearia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    endereco TEXT NOT NULL,
    logo TEXT DEFAULT 'static/logo.jpeg',
    whatsapp TEXT NOT NULL DEFAULT '558181365730'
);

CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    duracao_min INTEGER NOT NULL,
    imagem TEXT DEFAULT 'static/logo.jpeg',
    categoria TEXT DEFAULT 'servicos',
    ativo INTEGER DEFAULT 1,
    ordem INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS assinaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    descricao TEXT,
    beneficios TEXT,
    cor TEXT DEFAULT '#3ddc84',
    icone TEXT DEFAULT '⭐',
    destaque INTEGER DEFAULT 0,
    ativo INTEGER DEFAULT 1,
    ordem INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS profissionais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    especialidade TEXT,
    foto TEXT DEFAULT 'static/logo.jpeg',
    ativo INTEGER DEFAULT 1,
    ordem INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    imagem TEXT DEFAULT 'static/logo.jpeg',
    ativo INTEGER DEFAULT 1,
    ordem INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS imagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    arquivo TEXT NOT NULL,
    descricao TEXT,
    categoria TEXT DEFAULT 'geral',
    ativo INTEGER DEFAULT 1,
    ordem INTEGER DEFAULT 0,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO barbearia (id, nome, endereco, logo, whatsapp) VALUES
(1, 'Barbearia Studio Leblon', 'Av. Liberdade, 1477 - Totó, Recife - PE, 50940-280', 'static/logo.jpeg', '558181365730');

INSERT OR REPLACE INTO servicos (id, nome, preco, duracao_min, categoria, ordem) VALUES
(1, 'Sobrancelha', 5.00, 5, 'servicos', 1),
(2, 'Corte Infantil', 30.00, 30, 'servicos', 2),
(3, 'Barba + Sobrancelha', 20.00, 20, 'servicos', 3),
(4, 'Barba', 15.00, 15, 'servicos', 4),
(5, 'Acabamento (Pezinho)', 5.00, 15, 'servicos', 5),
(6, 'Corte + Barba + Sobrancelha', 45.00, 65, 'servicos', 6),
(7, 'Luzes/platinado', 60.00, 60, 'servicos', 7);

INSERT OR REPLACE INTO assinaturas (id, nome, preco, descricao, beneficios, cor, icone, destaque, ordem) VALUES
(1, 'Plano Bronze', 20.00, 'Para quem quer o básico com qualidade', '1 Corte por mês|Barba simples|Sobrancelha básica', '#cd7f32', '🥉', 0, 1),
(2, 'Plano Prata', 35.00, 'O equilíbrio perfeito entre custo e benefício', '2 Cortes por mês|Barba completa|Sobrancelha completa|Acabamento premium', '#c0c0c0', '🥈', 0, 2),
(3, 'Plano Ouro', 55.00, 'O plano mais completo para você ficar impecável', 'Cortes ilimitados|Barba premium|Sobrancelha premium|Luzes inclusas|Acabamento VIP', '#ffd700', '🥇', 1, 3),
(4, 'Plano Diamante', 80.00, 'Experiência VIP com atendimento prioritário', 'Cortes ilimitados|Barba luxo|Sobrancelha luxo|Luzes e coloração|Acabamento VIP|Atendimento prioritário|Agendamento exclusivo', '#b9f2ff', '💎', 0, 4);

INSERT OR REPLACE INTO profissionais (id, nome, especialidade, ordem) VALUES
(1, 'Kekeu', 'Cortes e barba', 1),
(2, 'Cristiano', 'Gerente', 2),
(3, 'Henrique', 'Especialista em barba', 3),
(4, 'Gabriel', 'Cortes modernos', 4);

INSERT OR REPLACE INTO produtos (id, nome, preco, ordem) VALUES
(1, 'Pomada Modeladora', 35.00, 1),
(2, 'Óleo para Barba', 28.00, 2),
(3, 'Shampoo Anticaspa', 25.00, 3);

INSERT OR REPLACE INTO imagens (id, nome, arquivo, descricao, categoria, ordem) VALUES
(1, 'Barbearia Exterior', 'fachada.jpg', 'Vista externa da barbearia', 'ambiente', 1),
(2, 'Interior', 'interior.jpg', 'Ambiente interno da barbearia', 'ambiente', 2),
(3, 'Equipe', 'equipe.jpg', 'Nossa equipe de profissionais', 'equipe', 3);
