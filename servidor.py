"""
Servidor da Barbearia Studio Leblon
------------------------------------
Ao iniciar o servidor, será solicitado no terminal:
- Nome do Gerente
- Usuário de login
- Senha
"""

import os
import sqlite3
from datetime import date, datetime, timedelta
import getpass
import requests

from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "banco.db")
SQL_SCHEMA_PATH = os.path.join(BASE_DIR, "banco.sql")

DB_GERENTE_PATH = os.path.join(BASE_DIR, "banco_gerente.db")
SQL_GERENTE_SCHEMA_PATH = os.path.join(BASE_DIR, "banco_gerente.sql")

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao-leblon-2026")

# ============ BASEROW INTEGRATION ============
BASEROW_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_TABLE_ID = "1083808"
BASEROW_URL = "https://api.baserow.io/api/database/rows/table/" + BASEROW_TABLE_ID + "/?user_field_names=true"

def enviar_para_baserow(pedido):
    """Envia um pedido para o Baserow"""
    if not BASEROW_TOKEN:
        print("⚠️ Baserow token não configurado")
        return False
    
    try:
        data = {
            "Cliente": pedido.get('cliente_nome', ''),
            "Serviço": pedido.get('servico_nome', ''),
            "Data/Hora": pedido.get('data_agendada', '') + ' ' + (pedido.get('hora_agendada', '') if pedido.get('hora_agendada') else ''),
            "valor": f"R$ {float(pedido.get('valor', 0)):.2f}",
            "Status": pedido.get('status', 'pendente'),
            "Profissional": pedido.get('profissional', ''),
            "Pagamento": pedido.get('pagamento', ''),
            "Telefone": pedido.get('cliente_telefone', ''),
            "CPF": pedido.get('cliente_cpf', '')
        }
        
        print(f"📤 Enviando para Baserow: {data}")
        
        response = requests.post(
            BASEROW_URL,
            json=data,
            headers={
                "Authorization": f"Token {BASEROW_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"📥 Resposta Baserow: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Pedido {pedido.get('id')} enviado para Baserow!")
            return True
        else:
            print(f"❌ Erro ao enviar para Baserow: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar para Baserow: {e}")
        return False

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    if not os.path.exists(SQL_SCHEMA_PATH):
        print(f"AVISO: {SQL_SCHEMA_PATH} não encontrado.")
        return
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("banco.db antigo removido.")
    print("Criando banco.db a partir de banco.sql...")
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Banco criado com sucesso!")

def get_db_gerente():
    if "db_gerente" not in g:
        g.db_gerente = sqlite3.connect(DB_GERENTE_PATH)
        g.db_gerente.row_factory = sqlite3.Row
    return g.db_gerente

def configurar_gerente_terminal():
    print("\n" + "="*60)
    print("  CONFIGURAÇÃO DO GERENTE - Barbearia Studio Leblon")
    print("="*60)
    print("\n⚠️  CONFIGURE AS CREDENCIAIS ABAIXO:\n")
    
    nome = input("📝 Nome do Gerente: ").strip()
    while not nome:
        print("❌ O nome é obrigatório!")
        nome = input("📝 Nome do Gerente: ").strip()
    
    usuario = input("👤 Usuário de login: ").strip()
    while not usuario:
        print("❌ O usuário é obrigatório!")
        usuario = input("👤 Usuário de login: ").strip()
    
    while True:
        senha = getpass.getpass("🔑 Senha (mínimo 4 caracteres): ")
        if len(senha) < 4:
            print("❌ A senha deve ter pelo menos 4 caracteres. Tente novamente.")
            continue
        senha2 = getpass.getpass("🔑 Confirme a senha: ")
        if senha != senha2:
            print("❌ As senhas não coincidem. Tente novamente.")
            continue
        break
    
    print("\n" + "="*60)
    print("  ✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("="*60)
    print(f"  📋 Nome:    {nome}")
    print(f"  🔑 Usuário: {usuario}")
    print(f"  🔒 Senha:   {'*' * len(senha)}")
    print("="*60 + "\n")
    
    return {"nome": nome, "usuario": usuario, "senha": senha}

def init_db_gerente():
    if os.path.exists(DB_GERENTE_PATH):
        print("📁 Banco do gerente já existe. Mantendo dados existentes.")
        return
    
    print("🆕 Criando banco_gerente.db pela primeira vez...")
    conn = sqlite3.connect(DB_GERENTE_PATH)
    conn.executescript("""
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
            data_assinatura TEXT,
            profissional TEXT,
            status TEXT NOT NULL DEFAULT 'pendente',
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours'))
        );
        CREATE TABLE IF NOT EXISTS caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            pagamento TEXT,
            pedido_id INTEGER,
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours')),
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
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours')),
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
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours')),
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
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            cpf TEXT UNIQUE,
            email TEXT,
            endereco TEXT,
            numero TEXT,
            complemento TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            data_nascimento TEXT,
            genero TEXT,
            observacoes TEXT,
            data_cadastro DATETIME DEFAULT (datetime('now', '-3 hours')),
            ativo INTEGER DEFAULT 1
        );
    """)
    conn.commit()
    
    config = configurar_gerente_terminal()
    conn.execute(
        "INSERT INTO gerentes (usuario, senha_hash, nome) VALUES (?, ?, ?)",
        (config["usuario"], config["senha"], config["nome"])
    )
    
    horarios = [
        (0, '09:00', '12:00', None, None, 0),
        (1, '09:00', '19:00', '13:00', '14:00', 1),
        (2, '09:00', '19:00', '13:00', '14:00', 1),
        (3, '09:00', '19:00', '13:00', '14:00', 1),
        (4, '09:00', '19:00', '13:00', '14:00', 1),
        (5, '09:00', '19:00', '13:00', '14:00', 1),
        (6, '09:00', '18:00', '13:00', '14:00', 1),
    ]
    for h in horarios:
        conn.execute(
            "INSERT OR REPLACE INTO horarios (dia_semana, abertura, fechamento, pausa_inicio, pausa_fim, ativo) VALUES (?, ?, ?, ?, ?, ?)",
            h
        )
    
    conn.commit()
    conn.close()
    print("\n✅ Gerente configurado com sucesso!")
    print("📋 GUARDE SUAS CREDENCIAIS:")
    print(f"   Usuário: {config['usuario']}")
    print(f"   Senha:   {config['senha']}")
    print("")

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
    db2 = g.pop("db_gerente", None)
    if db2 is not None:
        db2.close()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorado(*args, **kwargs):
        if not session.get("gerente_id"):
            return jsonify({"erro": "Não autenticado"}), 401
        return f(*args, **kwargs)
    return decorado

# ============ ROTAS ============

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

@app.route("/fotos/<path:filename>")
def serve_foto(filename):
    return send_from_directory(os.path.join(BASE_DIR, "fotos"), filename)

@app.route("/gerente/login")
def pagina_login_gerente():
    return send_from_directory(BASE_DIR, "gerente_login.html")

@app.route("/gerente")
def pagina_gerente():
    if not session.get("gerente_id"):
        return redirect("/gerente/login")
    return send_from_directory(BASE_DIR, "gerente.html")

# ============ ROTAS DE LOGIN ============

@app.route("/api/gerente/login", methods=["POST"])
def gerente_login():
    dados = request.get_json(force=True, silent=True) or {}
    usuario = (dados.get("usuario") or "").strip()
    senha = dados.get("senha") or ""
    db = get_db_gerente()
    row = db.execute("SELECT * FROM gerentes WHERE usuario = ?", (usuario,)).fetchone()
    if row is None or row["senha_hash"] != senha:
        return jsonify({"erro": "Usuário ou senha inválidos"}), 401
    session["gerente_id"] = row["id"]
    session["gerente_nome"] = row["nome"]
    return jsonify({"status": "ok", "nome": row["nome"]})

@app.route("/api/gerente/logout", methods=["POST"])
def gerente_logout():
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/me")
def gerente_me():
    if not session.get("gerente_id"):
        return jsonify({"erro": "Não autenticado"}), 401
    return jsonify({"nome": session.get("gerente_nome")})

# ============ ROTAS CATÁLOGO ============

TABELAS_CATALOGO = {
    "servicos": ["nome", "preco", "duracao_min", "imagem", "categoria", "ativo", "ordem"],
    "produtos": ["nome", "preco", "imagem", "ativo", "ordem"],
    "profissionais": ["nome", "especialidade", "foto", "ativo", "ordem"],
    "assinaturas": ["nome", "preco", "descricao", "beneficios", "cor", "icone", "destaque", "ativo", "ordem"],
}

@app.route("/api/<tabela>", methods=["GET"])

def api_listar_catalogo(tabela):
    if tabela not in TABELAS_CATALOGO:
        return jsonify({"erro": "Tabela inválida"}), 404
    db = get_db()
    rows = db.execute(f"SELECT * FROM {tabela} ORDER BY ordem, id").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/<tabela>", methods=["POST"])

def api_criar_catalogo(tabela):
    if tabela not in TABELAS_CATALOGO:
        return jsonify({"erro": "Tabela inválida"}), 404
    d = request.get_json(force=True, silent=True) or {}
    if not d.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    colunas = TABELAS_CATALOGO[tabela]
    campos = []
    valores = []
    for col in colunas:
        if col in d:
            campos.append(col)
            valores.append(d.get(col))
    placeholders = ", ".join(["?"] * len(campos))
    db = get_db()
    cur = db.execute(f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({placeholders})", valores)
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/<tabela>/<int:item_id>", methods=["PUT"])

def api_editar_catalogo(tabela, item_id):
    if tabela not in TABELAS_CATALOGO:
        return jsonify({"erro": "Tabela inválida"}), 404
    d = request.get_json(force=True, silent=True) or {}
    colunas = TABELAS_CATALOGO[tabela]
    db = get_db()
    item = db.execute(f"SELECT id FROM {tabela} WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return jsonify({"erro": "Item não encontrado"}), 404
    sets = []
    valores = []
    for col in colunas:
        if col in d:
            sets.append(f"{col} = ?")
            valores.append(d.get(col))
    if not sets:
        return jsonify({"erro": "Nada para atualizar"}), 400
    valores.append(item_id)
    db.execute(f"UPDATE {tabela} SET {', '.join(sets)} WHERE id = ?", valores)
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/<tabela>/<int:item_id>", methods=["DELETE"])

def api_deletar_catalogo(tabela, item_id):
    if tabela not in TABELAS_CATALOGO:
        return jsonify({"erro": "Tabela inválida"}), 404
    db = get_db()
    item = db.execute(f"SELECT id FROM {tabela} WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return jsonify({"erro": "Item não encontrado"}), 404
    db.execute(f"DELETE FROM {tabela} WHERE id = ?", (item_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE PEDIDOS ============

@app.route("/api/pedidos", methods=["POST"])
def api_criar_pedido():
    d = request.get_json(force=True, silent=True) or {}
    campos_obrigatorios = ["tipo", "servico_nome", "cliente_nome"]
    if any(not d.get(c) for c in campos_obrigatorios):
        return jsonify({"erro": "Dados incompletos"}), 400
    db = get_db_gerente()
    
    hora_brasil = datetime.utcnow() - timedelta(hours=3)
    hora_brasil_str = hora_brasil.strftime('%Y-%m-%d %H:%M:%S')
    
    cur = db.execute(
        """INSERT INTO pedidos
           (tipo, servico_nome, valor, cliente_nome, cliente_telefone, cliente_cpf,
            data_agendada, hora_agendada, corte_em_casa, endereco,
            complemento, observacoes, pagamento, data_assinatura, profissional, status, criado_em)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente', ?)""",
        (
            d.get("tipo"),
            d.get("servico_nome"),
            float(d.get("valor") or 0),
            d.get("cliente_nome"),
            d.get("cliente_telefone"),
            d.get("cliente_cpf"),
            d.get("data_agendada"),
            d.get("hora_agendada"),
            d.get("corte_em_casa", "nao"),
            d.get("endereco"),
            d.get("complemento"),
            d.get("observacoes"),
            d.get("pagamento"),
            d.get("data_assinatura"),
            d.get("profissional"),
            hora_brasil_str
        ),
    )
    db.commit()
    
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (cur.lastrowid,)).fetchone()
    
    # Enviar para Baserow se for agendamento
    if pedido and pedido["tipo"] == "agendamento":
        try:
            enviar_para_baserow(dict(pedido))
        except Exception as e:
            print(f"Erro ao enviar para Baserow: {e}")
    
    return jsonify({"status": "ok", "id": cur.lastrowid})

# ============ ROTAS DO GERENTE ============

@app.route("/api/gerente/dashboard")

def gerente_dashboard():
    db = get_db_gerente()
    faturamento_total = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo = 'entrada'").fetchone()[0]
    saidas_total = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo = 'saida'").fetchone()[0]
    pedidos_pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'").fetchone()[0]
    hoje = date.today().isoformat()
    agendamentos_hoje = db.execute("SELECT COUNT(*) FROM pedidos WHERE tipo = 'agendamento' AND data_agendada = ?", (hoje,)).fetchone()[0]
    total_clientes = db.execute("SELECT COUNT(DISTINCT cliente_nome) FROM pedidos").fetchone()[0]
    assinaturas_ativas = db.execute("SELECT COUNT(*) FROM pedidos WHERE tipo = 'assinatura' AND status != 'cancelado'").fetchone()[0]
    comandas_abertas = db.execute("SELECT COUNT(*) FROM comandas WHERE status = 'aberta'").fetchone()[0]
    repasses_pendentes = db.execute("SELECT COUNT(*) FROM repasses WHERE status = 'pendente'").fetchone()[0]
    return jsonify({
        "faturamento_total": faturamento_total,
        "saidas_total": saidas_total,
        "saldo": faturamento_total - saidas_total,
        "pedidos_pendentes": pedidos_pendentes,
        "agendamentos_hoje": agendamentos_hoje,
        "total_clientes": total_clientes,
        "assinaturas_ativas": assinaturas_ativas,
        "comandas_abertas": comandas_abertas,
        "repasses_pendentes": repasses_pendentes,
    })

@app.route("/api/gerente/pedidos")

def gerente_listar_pedidos():
    db = get_db_gerente()
    status = request.args.get("status")
    limit = request.args.get("limit")
    if status:
        if limit:
            rows = db.execute("SELECT * FROM pedidos WHERE status = ? ORDER BY id DESC LIMIT ?", (status, int(limit))).fetchall()
        else:
            rows = db.execute("SELECT * FROM pedidos WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
    else:
        if limit:
            rows = db.execute("SELECT * FROM pedidos ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        else:
            rows = db.execute("SELECT * FROM pedidos ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["PUT"])

def gerente_atualizar_pedido(pedido_id):
    d = request.get_json(force=True, silent=True) or {}
    novo_status = d.get("status")
    if novo_status not in ("pendente", "confirmado", "concluido", "cancelado"):
        return jsonify({"erro": "Status inválido"}), 400
    db = get_db_gerente()
    pedido_antigo = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if pedido_antigo is None:
        return jsonify({"erro": "Pedido não encontrado"}), 404
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    if novo_status == "concluido":
        ja_lancado = db.execute("SELECT COUNT(*) FROM caixa WHERE pedido_id = ?", (pedido_id,)).fetchone()[0]
        if not ja_lancado:
            db.execute(
                """INSERT INTO caixa (tipo, valor, descricao, pagamento, pedido_id)
                   VALUES ('entrada', ?, ?, ?, ?)""",
                (pedido_antigo["valor"], f"{pedido_antigo['servico_nome']} - {pedido_antigo['cliente_nome']}", pedido_antigo["pagamento"] or "manual", pedido_id),
            )
    db.commit()
    pedido_atualizado = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if novo_status in ["confirmado", "concluido"] and pedido_atualizado:
        try:
            enviar_para_baserow(dict(pedido_atualizado))
        except Exception as e:
            print(f"Erro ao enviar para Baserow: {e}")
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])

def gerente_deletar_pedido(pedido_id):
    db = get_db_gerente()
    db.execute("DELETE FROM caixa WHERE pedido_id = ?", (pedido_id,))
    db.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE CLIENTES ============

@app.route("/api/gerente/clientes", methods=["GET"])

def gerente_listar_clientes():
    db = get_db_gerente()
    busca = request.args.get("busca", "").strip()
    if busca:
        rows = db.execute(
            "SELECT * FROM clientes WHERE nome LIKE ? OR telefone LIKE ? OR cpf LIKE ? ORDER BY nome",
            (f"%{busca}%", f"%{busca}%", f"%{busca}%")
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/gerente/clientes", methods=["POST"])

def gerente_criar_cliente():
    d = request.get_json(force=True, silent=True) or {}
    if not d.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if d.get("cpf"):
        db = get_db_gerente()
        existe = db.execute("SELECT id FROM clientes WHERE cpf = ?", (d.get("cpf"),)).fetchone()
        if existe:
            return jsonify({"erro": "CPF já cadastrado"}), 400
    db = get_db_gerente()
    cur = db.execute(
        """INSERT INTO clientes 
           (nome, telefone, cpf, email, endereco, numero, complemento, 
            bairro, cidade, estado, cep, data_nascimento, genero, observacoes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            d.get("nome"),
            d.get("telefone"),
            d.get("cpf"),
            d.get("email"),
            d.get("endereco"),
            d.get("numero"),
            d.get("complemento"),
            d.get("bairro"),
            d.get("cidade"),
            d.get("estado"),
            d.get("cep"),
            d.get("data_nascimento"),
            d.get("genero"),
            d.get("observacoes")
        )
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["PUT"])

def gerente_editar_cliente(cliente_id):
    d = request.get_json(force=True, silent=True) or {}
    db = get_db_gerente()
    cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    if d.get("cpf"):
        existe = db.execute("SELECT id FROM clientes WHERE cpf = ? AND id != ?", (d.get("cpf"), cliente_id)).fetchone()
        if existe:
            return jsonify({"erro": "CPF já cadastrado"}), 400
    campos = ["nome", "telefone", "cpf", "email", "endereco", "numero", "complemento", 
              "bairro", "cidade", "estado", "cep", "data_nascimento", "genero", "observacoes", "ativo"]
    updates = []
    valores = []
    for campo in campos:
        if campo in d:
            updates.append(f"{campo} = ?")
            valores.append(d.get(campo))
    if not updates:
        return jsonify({"erro": "Nada para atualizar"}), 400
    valores.append(cliente_id)
    db.execute(f"UPDATE clientes SET {', '.join(updates)} WHERE id = ?", valores)
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["DELETE"])

def gerente_deletar_cliente(cliente_id):
    db = get_db_gerente()
    db.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE COMANDAS ============

@app.route("/api/gerente/comandas", methods=["GET"])

def gerente_listar_comandas():
    db = get_db_gerente()
    status = request.args.get("status")
    if status:
        rows = db.execute("SELECT * FROM comandas WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM comandas ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/comandas", methods=["POST"])

def gerente_criar_comanda():
    d = request.get_json(force=True, silent=True) or {}
    if not d.get("cliente_nome"):
        return jsonify({"erro": "Nome do cliente é obrigatório"}), 400
    db = get_db_gerente()
    ticket = f"TICKET-{datetime.now().strftime('%Y%m%d')}-{db.execute('SELECT COUNT(*) FROM comandas').fetchone()[0] + 1:04d}"
    cur = db.execute(
        """INSERT INTO comandas (ticket, cliente_nome, cliente_telefone, profissional, servicos, valor_total, status, pagamento, observacoes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ticket,
            d.get("cliente_nome"),
            d.get("cliente_telefone"),
            d.get("profissional"),
            d.get("servicos"),
            float(d.get("valor_total") or 0),
            d.get("status", "aberta"),
            d.get("pagamento", "pendente"),
            d.get("observacoes"),
        )
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid, "ticket": ticket})

@app.route("/api/gerente/comandas/<int:comanda_id>", methods=["PUT"])

def gerente_atualizar_comanda(comanda_id):
    d = request.get_json(force=True, silent=True) or {}
    db = get_db_gerente()
    updates = []
    valores = []
    campos = ["cliente_nome", "cliente_telefone", "profissional", "servicos", "valor_total", "status", "pagamento", "observacoes"]
    for campo in campos:
        if campo in d:
            updates.append(f"{campo} = ?")
            valores.append(d.get(campo))
    if d.get("status") == "paga":
        updates.append("data_pagamento = ?")
        valores.append(datetime.now().isoformat())
    if not updates:
        return jsonify({"erro": "Nada para atualizar"}), 400
    valores.append(comanda_id)
    db.execute(f"UPDATE comandas SET {', '.join(updates)} WHERE id = ?", valores)
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/comandas/<int:comanda_id>", methods=["DELETE"])

def gerente_deletar_comanda(comanda_id):
    db = get_db_gerente()
    db.execute("DELETE FROM comandas WHERE id = ?", (comanda_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE REPASSES ============

@app.route("/api/gerente/repasses", methods=["GET"])

def gerente_listar_repasses():
    db = get_db_gerente()
    status = request.args.get("status")
    if status:
        rows = db.execute("SELECT * FROM repasses WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM repasses ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/repasses", methods=["POST"])

def gerente_criar_repasse():
    d = request.get_json(force=True, silent=True) or {}
    if not d.get("profissional") or not d.get("servico_nome"):
        return jsonify({"erro": "Profissional e serviço são obrigatórios"}), 400
    db = get_db_gerente()
    porcentagem = float(d.get("porcentagem", 50))
    valor_servico = float(d.get("valor_servico", 0))
    comissao = valor_servico * (porcentagem / 100)
    cur = db.execute(
        """INSERT INTO repasses (profissional, servico_nome, valor_servico, comissao, porcentagem, data_servico, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            d.get("profissional"),
            d.get("servico_nome"),
            valor_servico,
            comissao,
            porcentagem,
            d.get("data_servico"),
            d.get("status", "pendente"),
        )
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/repasses/<int:repasse_id>", methods=["PUT"])

def gerente_atualizar_repasse(repasse_id):
    d = request.get_json(force=True, silent=True) or {}
    db = get_db_gerente()
    novo_status = d.get("status")
    if novo_status == "pago":
        db.execute("UPDATE repasses SET status = ?, pago_em = ? WHERE id = ?", (novo_status, datetime.now().isoformat(), repasse_id))
    else:
        db.execute("UPDATE repasses SET status = ? WHERE id = ?", (novo_status, repasse_id))
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/repasses/<int:repasse_id>", methods=["DELETE"])

def gerente_deletar_repasse(repasse_id):
    db = get_db_gerente()
    db.execute("DELETE FROM repasses WHERE id = ?", (repasse_id,))
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/repasses/resumo")

def gerente_resumo_repasses():
    db = get_db_gerente()
    total_comissoes = db.execute("SELECT COALESCE(SUM(comissao),0) FROM repasses WHERE status = 'pendente'").fetchone()[0]
    total_pago = db.execute("SELECT COALESCE(SUM(comissao),0) FROM repasses WHERE status = 'pago'").fetchone()[0]
    profissionais = db.execute(
        """SELECT profissional, COUNT(*) as servicos, SUM(valor_servico) as receita, SUM(comissao) as comissao_total
           FROM repasses 
           GROUP BY profissional 
           ORDER BY comissao_total DESC"""
    ).fetchall()
    return jsonify({
        "total_pendente": total_comissoes,
        "total_pago": total_pago,
        "profissionais": [dict(r) for r in profissionais]
    })

# ============ ROTAS DE CAIXA ============

@app.route("/api/gerente/caixa", methods=["GET"])

def gerente_listar_caixa():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM caixa ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/caixa", methods=["POST"])

def gerente_criar_caixa():
    d = request.get_json(force=True, silent=True) or {}
    tipo = d.get("tipo")
    valor = d.get("valor")
    if tipo not in ("entrada", "saida") or valor is None:
        return jsonify({"erro": "Dados inválidos"}), 400
    db = get_db_gerente()
    db.execute(
        "INSERT INTO caixa (tipo, valor, descricao, pagamento) VALUES (?, ?, ?, ?)",
        (tipo, float(valor), d.get("descricao", ""), d.get("pagamento", "manual")),
    )
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/caixa/<int:caixa_id>", methods=["DELETE"])

def gerente_deletar_caixa(caixa_id):
    db = get_db_gerente()
    db.execute("DELETE FROM caixa WHERE id = ?", (caixa_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE RELATÓRIOS ============

@app.route("/api/gerente/relatorio/pdf")

def gerente_relatorio_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        db = get_db_gerente()
        pedidos = db.execute("SELECT * FROM pedidos ORDER BY id DESC").fetchall()
        comandas = db.execute("SELECT * FROM comandas ORDER BY id DESC").fetchall()
        repasses = db.execute("SELECT * FROM repasses ORDER BY id DESC").fetchall()
        caixa = db.execute("SELECT * FROM caixa ORDER BY id DESC").fetchall()
        
        total_pedidos = len(pedidos)
        total_comandas = len(comandas)
        total_repasses = len(repasses)
        valor_total = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo = 'entrada'").fetchone()[0]
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "RELATÓRIO - Barbearia Studio Leblon")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y = height - 110
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "RESUMO")
        y -= 25
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"📋 Total de Pedidos: {total_pedidos}")
        y -= 20
        c.drawString(50, y, f"📋 Total de Comandas: {total_comandas}")
        y -= 20
        c.drawString(50, y, f"💰 Repasses Pendentes: {total_repasses}")
        y -= 20
        c.drawString(50, y, f"💰 Faturamento Total: R$ {valor_total:.2f}")
        
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar PDF: {str(e)}"}), 500

# ============ ROTAS DE HORÁRIOS ============

@app.route("/api/horarios", methods=["GET"])
def api_horarios():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM horarios ORDER BY dia_semana").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/horarios", methods=["PUT"])
def api_update_horarios():
    dados = request.get_json(force=True, silent=True) or {}
    db = get_db_gerente()
    for dia, info in dados.items():
        dia_num = int(dia)
        db.execute(
            "UPDATE horarios SET abertura = ?, fechamento = ?, pausa_inicio = ?, pausa_fim = ?, ativo = ? WHERE dia_semana = ?",
            (info.get("abertura"), info.get("fechamento"), info.get("pausa_inicio"), info.get("pausa_fim"), 1 if info.get("ativo") else 0, dia_num)
        )
    db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE VERIFICAÇÃO DE HORÁRIO ============

@app.route("/api/verificar-horario", methods=["POST"])
def verificar_horario():
    dados = request.get_json(force=True, silent=True) or {}
    data = dados.get("data")
    hora = dados.get("hora")
    if not data or not hora:
        return jsonify({"erro": "Data e hora são obrigatórias"}), 400
    db = get_db_gerente()
    agendamento = db.execute(
        """SELECT id, cliente_nome, servico_nome, status FROM pedidos 
           WHERE data_agendada = ? 
           AND hora_agendada = ? 
           AND status IN ('pendente', 'confirmado')
           AND tipo = 'agendamento'""",
        (data, hora)
    ).fetchone()
    if agendamento:
        status_texto = {
            'pendente': '⏳ Pendente',
            'confirmado': '✅ Confirmado'
        }.get(agendamento["status"], agendamento["status"])
        return jsonify({
            "disponivel": False,
            "mensagem": "❌ Horário indisponível!",
            "detalhes": {
                "cliente": agendamento["cliente_nome"],
                "servico": agendamento["servico_nome"],
                "status": status_texto
            }
        })
    return jsonify({"disponivel": True, "mensagem": "✅ Horário disponível!"})

@app.route("/api/horarios-ocupados", methods=["POST"])
def horarios_ocupados():
    dados = request.get_json(force=True, silent=True) or {}
    data = dados.get("data")
    if not data:
        return jsonify({"erro": "Data é obrigatória"}), 400
    db = get_db_gerente()
    agendamentos = db.execute(
        """SELECT hora_agendada, cliente_nome, servico_nome, status FROM pedidos 
           WHERE data_agendada = ? 
           AND status IN ('pendente', 'confirmado')
           AND tipo = 'agendamento'
           ORDER BY hora_agendada""",
        (data,)
    ).fetchall()
    horarios_ocupados = []
    for agendamento in agendamentos:
        status_texto = {
            'pendente': '⏳ Pendente',
            'confirmado': '✅ Confirmado'
        }.get(agendamento["status"], agendamento["status"])
        horarios_ocupados.append({
            "hora": agendamento["hora_agendada"],
            "cliente": agendamento["cliente_nome"],
            "servico": agendamento["servico_nome"],
            "status": status_texto
        })
    return jsonify({
        "data": data,
        "horarios_ocupados": horarios_ocupados,
        "total": len(horarios_ocupados)
    })

# ============ ROTAS DE CONFIGURAÇÕES ============

@app.route("/api/gerente/configuracoes", methods=["GET"])

def gerente_get_configuracoes():
    db = get_db()
    row = db.execute("SELECT * FROM barbearia LIMIT 1").fetchone()
    if row is None:
        return jsonify({}), 404
    config = dict(row)
    try:
        config["cor_primaria"] = config.get("cor_primaria", "#3ddc84")
        config["cor_fundo"] = config.get("cor_fundo", "#0a0a0e")
        config["cor_texto"] = config.get("cor_texto", "#eeeeef")
        config["cor_card"] = config.get("cor_card", "#14141a")
        config["cor_border"] = config.get("cor_border", "#2a2a32")
    except:
        pass
    return jsonify(config)

@app.route("/api/gerente/configuracoes", methods=["PUT"])

def gerente_update_configuracoes():
    dados = request.get_json(force=True, silent=True) or {}
    db = get_db()
    colunas = db.execute("PRAGMA table_info(barbearia)").fetchall()
    colunas_nomes = [c["name"] for c in colunas]
    updates = []
    valores = []
    for key, value in dados.items():
        if key in colunas_nomes and key != "id":
            updates.append(f"{key} = ?")
            valores.append(value)
    if updates:
        valores.append(1)
        db.execute(f"UPDATE barbearia SET {', '.join(updates)} WHERE id = ?", valores)
        db.commit()
    return jsonify({"status": "ok"})

# ============ ROTAS DE PERFIL ============

@app.route("/api/gerente/alterar_nome", methods=["POST"])

def gerente_alterar_nome():
    dados = request.get_json(force=True, silent=True) or {}
    novo_nome = dados.get("novo_nome") or ""
    if not novo_nome:
        return jsonify({"erro": "Informe o novo nome"}), 400
    db = get_db_gerente()
    db.execute("UPDATE gerentes SET nome = ? WHERE id = ?", (novo_nome, session["gerente_id"]))
    db.commit()
    session["gerente_nome"] = novo_nome
    return jsonify({"status": "ok"})

@app.route("/api/gerente/alterar_login", methods=["POST"])

def gerente_alterar_login():
    dados = request.get_json(force=True, silent=True) or {}
    senha_atual = dados.get("senha_atual") or ""
    novo_usuario = dados.get("novo_usuario") or ""
    nova_senha = dados.get("nova_senha") or ""
    if not senha_atual:
        return jsonify({"erro": "A senha atual é obrigatória"}), 400
    if not novo_usuario and not nova_senha:
        return jsonify({"erro": "Informe pelo menos um campo"}), 400
    db = get_db_gerente()
    row = db.execute("SELECT * FROM gerentes WHERE id = ?", (session["gerente_id"],)).fetchone()
    if row is None:
        return jsonify({"erro": "Gerente não encontrado"}), 404
    if row["senha_hash"] != senha_atual:
        return jsonify({"erro": "Senha atual incorreta"}), 400
    updates = []
    valores = []
    if novo_usuario:
        existe = db.execute("SELECT id FROM gerentes WHERE usuario = ? AND id != ?", (novo_usuario, session["gerente_id"])).fetchone()
        if existe:
            return jsonify({"erro": "Usuário já existe"}), 400
        updates.append("usuario = ?")
        valores.append(novo_usuario)
    if nova_senha:
        if len(nova_senha) < 4:
            return jsonify({"erro": "Senha deve ter ao menos 4 caracteres"}), 400
        updates.append("senha_hash = ?")
        valores.append(nova_senha)
    if not updates:
        return jsonify({"erro": "Nenhuma alteração"}), 400
    valores.append(session["gerente_id"])
    db.execute(f"UPDATE gerentes SET {', '.join(updates)} WHERE id = ?", valores)
    db.commit()
    if novo_usuario:
        session["gerente_nome"] = novo_usuario
    return jsonify({"status": "ok"})



@app.route("/api/seed", methods=["POST"])
def seed_database():
    """Popula o banco de dados com dados iniciais"""
    db = get_db()
    
    # Verificar se já tem dados
    count = db.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]
    if count > 0:
        return jsonify({"mensagem": "Banco já populado", "servicos": count})
    
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
        db.execute(
            "INSERT INTO servicos (nome, preco, duracao_min, ativo, ordem) VALUES (?, ?, ?, ?, ?)",
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
        db.execute(
            "INSERT INTO profissionais (nome, especialidade, ativo, ordem) VALUES (?, ?, ?, ?)",
            p
        )
    
    # Inserir produtos
    produtos = [
        ('Pomada Modeladora', 35.00, 1, 1),
        ('Óleo para Barba', 28.00, 1, 2),
        ('Shampoo Anticaspa', 25.00, 1, 3),
    ]
    for p in produtos:
        db.execute(
            "INSERT INTO produtos (nome, preco, ativo, ordem) VALUES (?, ?, ?, ?)",
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
        db.execute(
            "INSERT INTO assinaturas (nome, preco, icone, ativo, ordem) VALUES (?, ?, ?, ?, ?)",
            a
        )
    
    db.commit()
    return jsonify({"mensagem": "Banco populado com sucesso!", "servicos": len(servicos)})


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🚀 INICIANDO SERVIDOR - Barbearia Studio Leblon")
    print("="*60 + "\n")
    
    init_db()
    init_db_gerente()
    
    print("\n" + "="*60)
    print("  ✅ SERVIDOR PRONTO!")
    print("="*60)
    print("  🌐 Site do cliente:    http://localhost:5000/")
    print("  🔐 Painel do gerente:  http://localhost:5000/gerente/login")
    print("="*60)
    print("  💾 Dados salvos em:")
    print(f"     📁 {DB_PATH}")
    print(f"     📁 {DB_GERENTE_PATH}")
    print("="*60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
