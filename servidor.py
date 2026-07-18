"""
Servidor Barbearia - SQLite
"""
import os
import sqlite3
from datetime import date, datetime, timedelta
import getpass
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "banco.db")
DB_GERENTE_PATH = os.path.join(BASE_DIR, "banco_gerente.db")

app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia"

# ============ SQLITE ============
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_db_gerente():
    if "db_gerente" not in g:
        g.db_gerente = sqlite3.connect(DB_GERENTE_PATH)
        g.db_gerente.row_factory = sqlite3.Row
    return g.db_gerente

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

# ============ ROTAS ============
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

# ============ API PÚBLICA ============
@app.route("/api/servicos", methods=["GET"])
def api_servicos():
    db = get_db()
    rows = db.execute("SELECT * FROM servicos WHERE ativo = 1 ORDER BY ordem, id").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    db = get_db()
    rows = db.execute("SELECT * FROM profissionais WHERE ativo = 1 ORDER BY ordem, id").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/assinaturas", methods=["GET"])
def api_assinaturas():
    db = get_db()
    rows = db.execute("SELECT * FROM assinaturas WHERE ativo = 1 ORDER BY ordem, id").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    db = get_db()
    rows = db.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY ordem, id").fetchall()
    return jsonify([dict(r) for r in rows])

# ============ API GERENTE ============
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

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["PUT"])
@login_required
def gerente_atualizar_pedido(pedido_id):
    dados = request.get_json() or {}
    status = dados.get("status")
    db = get_db_gerente()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    db = get_db_gerente()
    db.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    db.commit()
    return jsonify({"status": "ok"})

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

# ============ INICIAR ============
# ============================================================
# ROTAS QUE ESTAVAM FALTANDO
# ============================================================

# ---- Recebe pedidos vindos do site (index.html) ----
@app.route("/api/pedidos", methods=["POST"])
def api_criar_pedido():
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


# ---- CRUD de Serviços ----
@app.route("/api/servicos", methods=["POST"])
@login_required
def api_criar_servico():
    dados = request.get_json() or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO servicos (nome, preco, duracao_min, ativo, ordem) VALUES (?, ?, ?, ?, ?)",
        (dados.get('nome'), dados.get('preco', 0), dados.get('duracao_min', 30),
         dados.get('ativo', 1), dados.get('ordem', 0))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/servicos/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_servico(item_id):
    dados = request.get_json() or {}
    db = get_db()
    db.execute(
        "UPDATE servicos SET nome=?, preco=?, duracao_min=?, ativo=? WHERE id=?",
        (dados.get('nome'), dados.get('preco', 0), dados.get('duracao_min', 30),
         dados.get('ativo', 1), item_id)
    )
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/servicos/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_servico(item_id):
    db = get_db()
    db.execute("DELETE FROM servicos WHERE id=?", (item_id,))
    db.commit()
    return jsonify({"status": "ok"})


# ---- CRUD de Produtos ----
@app.route("/api/produtos", methods=["POST"])
@login_required
def api_criar_produto():
    dados = request.get_json() or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO produtos (nome, preco, ativo, ordem) VALUES (?, ?, ?, ?)",
        (dados.get('nome'), dados.get('preco', 0), dados.get('ativo', 1), dados.get('ordem', 0))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/produtos/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_produto(item_id):
    dados = request.get_json() or {}
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome=?, preco=?, ativo=? WHERE id=?",
        (dados.get('nome'), dados.get('preco', 0), dados.get('ativo', 1), item_id)
    )
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/produtos/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_produto(item_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id=?", (item_id,))
    db.commit()
    return jsonify({"status": "ok"})


# ---- CRUD de Profissionais ----
@app.route("/api/profissionais", methods=["POST"])
@login_required
def api_criar_profissional():
    dados = request.get_json() or {}
    db = get_db()
    cur = db.execute(
        "INSERT INTO profissionais (nome, especialidade, ativo, ordem) VALUES (?, ?, ?, ?)",
        (dados.get('nome'), dados.get('especialidade', ''), dados.get('ativo', 1), dados.get('ordem', 0))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/profissionais/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_profissional(item_id):
    dados = request.get_json() or {}
    db = get_db()
    db.execute(
        "UPDATE profissionais SET nome=?, especialidade=?, ativo=? WHERE id=?",
        (dados.get('nome'), dados.get('especialidade', ''), dados.get('ativo', 1), item_id)
    )
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/profissionais/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_profissional(item_id):
    db = get_db()
    db.execute("DELETE FROM profissionais WHERE id=?", (item_id,))
    db.commit()
    return jsonify({"status": "ok"})


# ---- CRUD de Assinaturas (Planos) ----
@app.route("/api/assinaturas", methods=["POST"])
@login_required
def api_criar_assinatura():
    dados = request.get_json() or {}
    db = get_db()
    cur = db.execute(
        """INSERT INTO assinaturas (nome, preco, icone, descricao, destaque, ativo, ordem, beneficios, cor)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (dados.get('nome'), dados.get('preco', 0), dados.get('icone', '⭐'),
         dados.get('descricao', ''), dados.get('destaque', 0), dados.get('ativo', 1),
         dados.get('ordem', 0), dados.get('beneficios', ''), dados.get('cor', '#3ddc84'))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/assinaturas/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_assinatura(item_id):
    dados = request.get_json() or {}
    db = get_db()
    db.execute(
        "UPDATE assinaturas SET nome=?, preco=?, icone=?, descricao=?, destaque=?, ativo=? WHERE id=?",
        (dados.get('nome'), dados.get('preco', 0), dados.get('icone', '⭐'),
         dados.get('descricao', ''), dados.get('destaque', 0), dados.get('ativo', 1), item_id)
    )
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/assinaturas/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_assinatura(item_id):
    db = get_db()
    db.execute("DELETE FROM assinaturas WHERE id=?", (item_id,))
    db.commit()
    return jsonify({"status": "ok"})


# ---- Editar/Excluir Clientes ----
@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["PUT"])
@login_required
def gerente_atualizar_cliente(cliente_id):
    dados = request.get_json() or {}
    db = get_db_gerente()
    db.execute(
        "UPDATE clientes SET nome=?, telefone=?, cpf=?, endereco=? WHERE id=?",
        (dados.get('nome'), dados.get('telefone'), dados.get('cpf'), dados.get('endereco'), cliente_id)
    )
    db.commit()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["DELETE"])
@login_required
def gerente_deletar_cliente(cliente_id):
    db = get_db_gerente()
    db.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    db.commit()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 SQLite")
    print("="*60)
    app.run(debug=True, host="0.0.0.0", port=5000)
