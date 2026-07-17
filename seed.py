import sqlite3
import os

# Conectar ao banco de dados
db_path = os.path.join(os.path.dirname(__file__), "data", "banco.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Inserir serviços
servicos = [
    ('Corte Masculino', 45.00, 30, 1, 1),
    ('Barba', 35.00, 20, 1, 2),
    ('Corte + Barba', 70.00, 50, 1, 3),
    ('Sobrancelha', 15.00, 15, 1, 4),
    ('Hidratação', 50.00, 45, 1, 5),
    ('Corte Infantil', 30.00, 30, 1, 6),
    ('Luzes/Platinado', 60.00, 60, 1, 7),
]

for s in servicos:
    cursor.execute(
        "INSERT OR IGNORE INTO servicos (nome, preco, duracao_min, ativo, ordem) VALUES (?, ?, ?, ?, ?)",
        s
    )

# Inserir profissionais
profissionais = [
    ('Kekeu', 'Cortes e barba', 1, 1),
    ('Cristiano', 'Gerente', 1, 2),
    ('Henrique', 'Especialista em barba', 1, 3),
    ('Gabriel', 'Cortes modernos', 1, 4),
]

for p in profissionais:
    cursor.execute(
        "INSERT OR IGNORE INTO profissionais (nome, especialidade, ativo, ordem) VALUES (?, ?, ?, ?)",
        p
    )

# Inserir produtos
produtos = [
    ('Pomada Modeladora', 35.00, 1, 1),
    ('Óleo para Barba', 28.00, 1, 2),
    ('Shampoo Anticaspa', 25.00, 1, 3),
]

for p in produtos:
    cursor.execute(
        "INSERT OR IGNORE INTO produtos (nome, preco, ativo, ordem) VALUES (?, ?, ?, ?)",
        p
    )

# Inserir assinaturas
assinaturas = [
    ('Plano Bronze', 20.00, '🥉', 1, 1),
    ('Plano Prata', 35.00, '🥈', 1, 2),
    ('Plano Ouro', 55.00, '🥇', 1, 3),
    ('Plano Diamante', 80.00, '💎', 1, 4),
]

for a in assinaturas:
    cursor.execute(
        "INSERT OR IGNORE INTO assinaturas (nome, preco, icone, ativo, ordem) VALUES (?, ?, ?, ?, ?)",
        a
    )

conn.commit()
conn.close()

print("✅ Banco de dados populado com sucesso!")
