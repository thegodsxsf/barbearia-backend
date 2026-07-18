"""
Servidor Barbearia - SQLite + Baserow
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

app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia"

# ============ BASEROW ============
BASEROW_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_TABLE_ID = "1083808"
BASEROW_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"

def enviar_para_baserow(pedido):
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
        response = requests.post(
            BASEROW_URL,
            json=data,
            headers={"Authorization": f"Token {BASEROW_TOKEN}", "Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ Pedido enviado para Baserow!")
            return True
        return False
    except Exception as e:
        print(f"❌ Erro Baserow: {e}")
        return False

# ============ SQLITE ============
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    if os.path.exists(DB_PATH):
        return
    print("🆕 Criando banco.db...")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL DEFAULT 0,
            duracao_min INTEGER DEFAULT 30,
            ativo INTEGER DEFAULT 1,
            ordem INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            ordem INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS profissionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            especialidade TEXT,
            ativo INTEGER DEFAULT 1,
            ordem INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS assinaturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL DEFAULT 0,
            descricao TEXT,
            icone TEXT DEFAULT '⭐',
            ativo INTEGER DEFAULT 1,
            ordem INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS barbearia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT DEFAULT 'Barbearia Studio Leblon',
            endereco TEXT DEFAULT 'Rua Maganel, nº 1477, Curado, Recife, PE',
            whatsapp TEXT DEFAULT '5581995654683'
        );
    """)
    # Dados iniciais
    servicos = [
        ('Corte Masculino', 45.00, 30),
        ('Barba', 35.00, 20),
        ('Corte + Barba', 70.00, 50),
        ('Sobrancelha', 15.00, 15),
        ('Hidratação', 50.00, 45),
        ('Corte Infantil', 30.00, 30),
        ('Luzes/Platinado', 60.00, 60),
    ]
    for s in servicos:
        conn.execute("INSERT INTO servicos (nome, preco, duracao_min) VALUES (?, ?, ?)", s)
    
    profissionais = [
        ('Kekeu', 'Cortes e barba'),
        ('Cristiano', 'Gerente'),
        ('Henrique', 'Especialista em barba'),
        ('Gabriel', 'Cortes modernos'),
    ]
    for p in profissionais:
        conn.execute("INSERT INTO profissionais (nome, especialidade) VALUES (?, ?)", p)
    
    conn.execute("INSERT INTO barbearia (nome, endereco) VALUES ('Barbearia Studio Leblon', 'Rua Maganel, nº 1477, Curado, Recife, PE')")
    conn.commit()
    conn.close()
    print("✅ banco.db criado!")

def get_db_gerente():
    if "db_gerente" not in g:
        g.db_gerente = sqlite3.connect(DB_GERENTE_PATH)
        g.db_gerente.row_factory = sqlite3.Row
    return g.db_gerente

def init_db_gerente():
    if os.path.exists(DB_GERENTE_PATH):
        return
    print("🆕 Criando banco_gerente.db...")
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
            valor REAL DEFAULT 0,
            cliente_nome TEXT NOT NULL,
            cliente_telefone TEXT,
            cliente_cpf TEXT,
            data_agendada TEXT,
            hora_agendada TEXT,
            profissional TEXT,
            pagamento TEXT,
            status TEXT DEFAULT 'pendente',
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours'))
        );
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            cpf TEXT,
            endereco TEXT,
            data_cadastro DATETIME DEFAULT (datetime('now', '-3 hours'))
        );
        CREATE TABLE IF NOT EXISTS caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            pedido_id INTEGER,
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours'))
        );
        CREATE TABLE IF NOT EXISTS comandas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket TEXT NOT NULL,
            cliente_nome TEXT NOT NULL,
            valor_total REAL DEFAULT 0,
            status TEXT DEFAULT 'aberta',
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours'))
        );
        CREATE TABLE IF NOT EXISTS repasses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profissional TEXT NOT NULL,
            servico_nome TEXT NOT NULL,
            valor_servico REAL NOT NULL,
            comissao REAL NOT NULL,
            status TEXT DEFAULT 'pendente',
            criado_em DATETIME DEFAULT (datetime('now', '-3 hours'))
        );
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana INTEGER NOT NULL,
            abertura TEXT NOT NULL,
            fechamento TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        );
    """)
    conn.execute("INSERT INTO gerentes (usuario, senha_hash, nome) VALUES ('barbe', 'barbe', 'Gerente')")
    horarios = [
        (0, '09:00', '12:00', 0),
        (1, '09:00', '19:00', 1),
        (2, '09:00', '19:00', 1),
        (3, '09:00', '19:00', 1),
        (4, '09:00', '19:00', 1),
        (5, '09:00', '19:00', 1),
        (6, '09:00', '18:00', 1),
    ]
    for h in horarios:
        conn.execute("INSERT INTO horarios (dia_semana, abertura, fechamento, ativo) VALUES (?, ?, ?, ?)", h)
    conn.commit()
    conn.close()
    print("✅ banco_gerente.db criado!")

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()
    db2 = g.pop("db_gerente", None)
    if db2:
        db2.close()

# ============ LOGIN ============
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorado(*args, **kwargs):
        if not session.get("gerente_id"):
            return jsonify({"erro": "Não autenticado"}), 401
        return f(*args, **kwargs)
    return decorado

@app.route("/api/gerente/login", methods=["POST"])
def gerente_login():
    dados = request.get_json() or {}
    usuario = dados.get("usuario", "").strip()
    senha = dados.get("senha", "")
    db = get_db_gerente()
    row = db.execute("SELECT * FROM gerentes WHERE usuario = ?", (usuario,)).fetchone()
    if not row or row["senha_hash"] != senha:
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

# ============ ROTAS PÚBLICAS ============
@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

@app.route("/gerente/login")
def pagina_login_gerente():
    return send_from_directory(BASE_DIR, "gerente_login.html")

@app.route("/gerente")
def pagina_gerente():
    if not session.get("gerente_id"):
        return redirect("/gerente/login")
    return send_from_directory(BASE_DIR, "gerente.html")

@app.route("/api/servicos", methods=["GET"])
def api_servicos():
    db = get_db()
    rows = db.execute("SELECT * FROM servicos WHERE ativo = 1 ORDER BY ordem").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    db = get_db()
    rows = db.execute("SELECT * FROM profissionais WHERE ativo = 1 ORDER BY ordem").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/assinaturas", methods=["GET"])
def api_assinaturas():
    db = get_db()
    rows = db.execute("SELECT * FROM assinaturas WHERE ativo = 1 ORDER BY ordem").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    db = get_db()
    rows = db.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY ordem").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/horarios", methods=["GET"])
def api_horarios():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM horarios ORDER BY dia_semana").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/verificar-horario", methods=["POST"])
def verificar_horario():
    return jsonify({"disponivel": True})

@app.route("/api/horarios-ocupados", methods=["POST"])
def horarios_ocupados():
    return jsonify({"horarios_ocupados": [], "total": 0})

# ============ ROTAS GERENTE ============
@app.route("/api/gerente/dashboard")
@login_required
def gerente_dashboard():
    db = get_db_gerente()
    faturamento = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='entrada'").fetchone()[0]
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status='pendente'").fetchone()[0]
    return jsonify({
        "faturamento_total": faturamento,
        "saldo": faturamento,
        "pedidos_pendentes": pendentes,
        "agendamentos_hoje": 0,
        "total_clientes": 0,
        "assinaturas_ativas": 0,
        "comandas_abertas": 0,
        "repasses_pendentes": 0
    })

@app.route("/api/gerente/pedidos", methods=["GET"])
@login_required
def gerente_listar_pedidos():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM pedidos ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/pedidos", methods=["POST"])
@login_required
def gerente_criar_pedido():
    dados = request.get_json() or {}
    db = get_db_gerente()
    cur = db.execute(
        """INSERT INTO pedidos (tipo, servico_nome, valor, cliente_nome, cliente_telefone, 
            cliente_cpf, data_agendada, hora_agendada, profissional, pagamento, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente')""",
        (dados.get('tipo'), dados.get('servico_nome'), dados.get('valor', 0),
         dados.get('cliente_nome'), dados.get('cliente_telefone'), dados.get('cliente_cpf'),
         dados.get('data_agendada'), dados.get('hora_agendada'), dados.get('profissional'),
         dados.get('pagamento'))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["PUT"])
@login_required
def gerente_atualizar_pedido(pedido_id):
    dados = request.get_json() or {}
    status = dados.get('status')
    db = get_db_gerente()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
    if status == 'concluido':
        pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if pedido:
            db.execute("INSERT INTO caixa (tipo, valor, descricao, pedido_id) VALUES ('entrada', ?, ?, ?)",
                      (pedido['valor'], pedido['servico_nome'] + ' - ' + pedido['cliente_nome'], pedido_id))
            enviar_para_baserow(dict(pedido))
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    db = get_db_gerente()
    db.execute("DELETE FROM caixa WHERE pedido_id = ?", (pedido_id,))
    db.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/clientes", methods=["POST"])
@login_required
def gerente_criar_cliente():
    dados = request.get_json() or {}
    db = get_db_gerente()
    cur = db.execute(
        "INSERT INTO clientes (nome, telefone, cpf, endereco) VALUES (?, ?, ?, ?)",
        (dados.get('nome'), dados.get('telefone'), dados.get('cpf'), dados.get('endereco'))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/comandas", methods=["GET"])
@login_required
def gerente_listar_comandas():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM comandas ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/comandas", methods=["POST"])
@login_required
def gerente_criar_comanda():
    dados = request.get_json() or {}
    db = get_db_gerente()
    ticket = f"TICKET-{datetime.now().strftime('%Y%m%d')}-{db.execute('SELECT COUNT(*) FROM comandas').fetchone()[0] + 1:04d}"
    cur = db.execute(
        "INSERT INTO comandas (ticket, cliente_nome, valor_total) VALUES (?, ?, ?)",
        (ticket, dados.get('cliente_nome'), dados.get('valor_total', 0))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid, "ticket": ticket})

@app.route("/api/gerente/repasses", methods=["GET"])
@login_required
def gerente_listar_repasses():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM repasses ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/repasses", methods=["POST"])
@login_required
def gerente_criar_repasse():
    dados = request.get_json() or {}
    db = get_db_gerente()
    comissao = dados.get('valor_servico', 0) * 0.5
    cur = db.execute(
        "INSERT INTO repasses (profissional, servico_nome, valor_servico, comissao) VALUES (?, ?, ?, ?)",
        (dados.get('profissional'), dados.get('servico_nome'), dados.get('valor_servico', 0), comissao)
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/caixa", methods=["GET"])
@login_required
def gerente_listar_caixa():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM caixa ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/caixa", methods=["POST"])
@login_required
def gerente_criar_caixa():
    dados = request.get_json() or {}
    db = get_db_gerente()
    cur = db.execute(
        "INSERT INTO caixa (tipo, valor, descricao) VALUES (?, ?, ?)",
        (dados.get('tipo'), dados.get('valor'), dados.get('descricao'))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/configuracoes", methods=["GET"])
@login_required
def gerente_get_configuracoes():
    db = get_db()
    row = db.execute("SELECT * FROM barbearia LIMIT 1").fetchone()
    return jsonify(dict(row) if row else {})

@app.route("/api/gerente/configuracoes", methods=["PUT"])
@login_required
def gerente_update_configuracoes():
    return jsonify({"status": "ok"})

@app.route("/api/gerente/relatorio/pdf")
@login_required
def gerente_relatorio_pdf():
    return jsonify({"erro": "Função em desenvolvimento"})

@app.route("/config.js")
def serve_config():
    return send_from_directory(BASE_DIR, "config.js")

# ============ INICIAR ============
if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 SQLite + Baserow")
    print("="*60)
    init_db()
    init_db_gerente()
    print("\n✅ Servidor pronto!")
    print("🔗 http://localhost:5000")
    print("🔐 /gerente/login (barbe/barbe)")
    app.run(debug=True, host="0.0.0.0", port=5000)
