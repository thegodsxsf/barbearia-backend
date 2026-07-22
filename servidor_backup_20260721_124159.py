"""
Barbearia - SQLite + Baserow
"""
import os
import sqlite3
from datetime import date, datetime, timedelta
import getpass
import requests
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "banco.db")
DB_GERENTE_PATH = os.path.join(BASE_DIR, "banco_gerente.db")

app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia"

# ============ BASEROW ============
BASEROW_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_TABLE_ID = "1083808"
BASEROW_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"

def enviar_pedido_baserow(pedido):
    """Envia pedido para o Baserow quando concluído"""
    if not BASEROW_TOKEN:
        return False
    
    try:
        cliente = pedido.get('cliente_nome', '') or ''
        servico = pedido.get('servico_nome', '') or ''
        valor = pedido.get('valor', 0) or 0
        data = pedido.get('data_agendada', '') or ''
        hora = pedido.get('hora_agendada', '') or ''
        data_hora = f"{data} {hora}".strip()
        if not data_hora:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        data = {
            "Cliente": cliente,
            "Serviço": servico,
            "Data/Hora": data_hora,
            "valor": f"R$ {float(valor):.2f}"
        }
        
        response = requests.post(
            BASEROW_URL,
            json=data,
            headers={
                "Authorization": f"Token {BASEROW_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Pedido enviado para Baserow!")
            return True
        else:
            print(f"⚠️ Erro Baserow: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Erro ao enviar Baserow: {e}")
        return False

# ============ CAIXA DIÁRIO ============
def init_caixa_diario():
    """Cria as tabelas de caixa diário se não existirem"""
    db = get_db_gerente()
    try:
        db.execute('''
            CREATE TABLE IF NOT EXISTS caixa_diario (
                data TEXT PRIMARY KEY,
                saldo_inicial REAL DEFAULT 0,
                entradas REAL DEFAULT 0,
                saidas REAL DEFAULT 0,
                saldo_final REAL DEFAULT 0
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS caixa_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                saldo_inicial REAL DEFAULT 0,
                entradas REAL DEFAULT 0,
                saidas REAL DEFAULT 0,
                saldo_final REAL DEFAULT 0,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

def get_caixa_dia():
    """Retorna o caixa do dia atual"""
    db = get_db_gerente()
    init_caixa_diario()
    hoje = date.today().isoformat()
    
    caixa = db.execute("SELECT * FROM caixa_diario WHERE data = ?", (hoje,)).fetchone()
    if not caixa:
        db.execute(
            "INSERT INTO caixa_diario (data, saldo_inicial, entradas, saidas, saldo_final) VALUES (?, 0, 0, 0, 0)",
            (hoje,)
        )
        db.commit()
        caixa = db.execute("SELECT * FROM caixa_diario WHERE data = ?", (hoje,)).fetchone()
    
    return caixa

def resetar_caixa_dia():
    """Reseta o caixa do dia para R$ 0,00"""
    db = get_db_gerente()
    init_caixa_diario()
    hoje = date.today().isoformat()
    
    caixa_atual = db.execute("SELECT * FROM caixa_diario WHERE data = ?", (hoje,)).fetchone()
    if caixa_atual:
        db.execute(
            "INSERT INTO caixa_historico (data, saldo_inicial, entradas, saidas, saldo_final) VALUES (?, ?, ?, ?, ?)",
            (hoje, caixa_atual[1] or 0, caixa_atual[2] or 0, caixa_atual[3] or 0, caixa_atual[4] or 0)
        )
    
    db.execute(
        "INSERT OR REPLACE INTO caixa_diario (data, saldo_inicial, entradas, saidas, saldo_final) VALUES (?, 0, 0, 0, 0)",
        (hoje,)
    )
    db.commit()
    return {"status": "ok", "mensagem": "Caixa resetado para R$ 0,00"}

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

# ============ ROTAS DE PÁGINAS ============
@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

@app.route("/fotos/<path:filename>")
def fotos_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "fotos"), filename)

@app.route("/gerente/login")
def pagina_login_gerente():
    return send_from_directory(BASE_DIR, "gerente_login.html")

@app.route("/gerente")
def pagina_gerente():
    if not session.get("gerente_id"):
        return redirect("/gerente/login")
    return send_from_directory(BASE_DIR, "gerente.html")

# ============ API PÚBLICA ============
@app.route("/api/barbearia", methods=["GET"])
def api_barbearia():
    try:
        db = get_db()
        row = db.execute("SELECT * FROM barbearia LIMIT 1").fetchone()
        if row:
            return jsonify(dict(row))
    except:
        pass
    return jsonify({
        "nome": "Leblon Studio",
        "endereco": "Av. Liberdade, 1477 - Totó, Recife - PE, 50940-280",
        "whatsapp": "558181365730",
        "logo": None
    })

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

@app.route("/api/imagens", methods=["GET"])
def api_imagens():
    try:
        db = get_db()
        rows = db.execute("SELECT * FROM imagens WHERE ativo = 1 ORDER BY ordem, id").fetchall()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

@app.route("/api/horarios", methods=["GET"])
def api_horarios_get():
    try:
        db = get_db()
        rows = db.execute("SELECT * FROM horarios ORDER BY dia_semana").fetchall()
        if rows:
            return jsonify([dict(r) for r in rows])
    except:
        pass
    return jsonify([{"dia_semana": i, "abertura": "", "fechamento": "", "ativo": 0} for i in range(7)])

@app.route("/api/horarios", methods=["PUT"])
@login_required
def api_horarios_put():
    dados = request.get_json() or {}
    db = get_db()
    try:
        for dia, info in dados.items():
            db.execute(
                "INSERT OR REPLACE INTO horarios (dia_semana, abertura, fechamento, ativo) VALUES (?, ?, ?, ?)",
                (int(dia), info.get("abertura", ""), info.get("fechamento", ""), 1 if info.get("ativo") else 0)
            )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ RECEBER PEDIDOS ============
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
    init_caixa_diario()
    
    # Pegar caixa do dia
    caixa_dia = get_caixa_dia()
    saldo_hoje = caixa_dia[4] if caixa_dia else 0
    entradas_hoje = caixa_dia[2] if caixa_dia else 0
    saidas_hoje = caixa_dia[3] if caixa_dia else 0
    saldo_inicial = caixa_dia[1] if caixa_dia else 0
    
    # Faturamento total (entradas)
    entradas = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='entrada'").fetchone()[0]
    saidas = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='saida'").fetchone()[0]
    
    # Pedidos pendentes
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status='pendente'").fetchone()[0]
    
    # Agendamentos hoje
    hoje = date.today().isoformat()
    agendamentos_hoje = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE data_agendada = ? AND status != 'cancelado'", (hoje,)
    ).fetchone()[0]
    
    # Total de clientes (distintos)
    total_clientes = db.execute("SELECT COUNT(DISTINCT cliente_nome) FROM pedidos").fetchone()[0]
    
    # Comandas abertas
    try:
        comandas_abertas = db.execute("SELECT COUNT(*) FROM comandas WHERE status='aberta'").fetchone()[0]
    except:
        comandas_abertas = 0
    
    # Repasses pendentes
    try:
        repasses_pendentes = db.execute("SELECT COUNT(*) FROM repasses WHERE status='pendente'").fetchone()[0]
    except:
        repasses_pendentes = 0
    
    return jsonify({
        "faturamento_total": entradas,
        "saidas_total": saidas,
        "saldo": saldo_hoje,
        "saldo_inicial": saldo_inicial,
        "entradas_hoje": entradas_hoje,
        "saidas_hoje": saidas_hoje,
        "pedidos_pendentes": pendentes,
        "agendamentos_hoje": agendamentos_hoje,
        "total_clientes": total_clientes,
        "assinaturas_ativas": 0,
        "comandas_abertas": comandas_abertas,
        "repasses_pendentes": repasses_pendentes
    })

@app.route("/api/gerente/pedidos", methods=["GET"])
@login_required
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
@login_required
def gerente_atualizar_pedido(pedido_id):
    try:
        dados = request.get_json(force=True, silent=True) or {}
        novo_status = dados.get("status")
        
        if not novo_status:
            return jsonify({"erro": "Status não informado"}), 400
        
        if novo_status not in ("pendente", "confirmado", "concluido", "cancelado"):
            return jsonify({"erro": "Status inválido"}), 400
        
        db = get_db_gerente()
        
        pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if not pedido:
            return jsonify({"erro": "Pedido não encontrado"}), 404
        
        servico_nome = pedido[2]
        cliente_nome = pedido[4]
        pagamento = pedido[13] if len(pedido) > 13 else "manual"
        valor = pedido[3]
        
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        
        if novo_status == "concluido":
            ja_lancado = db.execute("SELECT COUNT(*) FROM caixa WHERE pedido_id = ?", (pedido_id,)).fetchone()[0]
            if not ja_lancado:
                db.execute(
                    "INSERT INTO caixa (tipo, descricao, pagamento, valor, pedido_id) VALUES (?, ?, ?, ?, ?)",
                    ("entrada", f"{servico_nome} - {cliente_nome}", pagamento, valor, pedido_id)
                )
                # Atualizar caixa diário
                hoje = date.today().isoformat()
                caixa_dia = db.execute("SELECT * FROM caixa_diario WHERE data = ?", (hoje,)).fetchone()
                if caixa_dia:
                    novas_entradas = (caixa_dia[2] or 0) + valor
                    novo_saldo = (caixa_dia[1] or 0) + novas_entradas - (caixa_dia[3] or 0)
                    db.execute(
                        "UPDATE caixa_diario SET entradas = ?, saldo_final = ? WHERE data = ?",
                        (novas_entradas, novo_saldo, hoje)
                    )
            
            # Enviar para Baserow
            try:
                enviar_pedido_baserow({
                    "cliente_nome": cliente_nome,
                    "servico_nome": servico_nome,
                    "valor": valor,
                    "data_agendada": pedido[7] if len(pedido) > 7 else "",
                    "hora_agendada": pedido[8] if len(pedido) > 8 else ""
                })
            except:
                pass
        
        db.commit()
        return jsonify({"status": "ok"})
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    try:
        db = get_db_gerente()
        db.execute("DELETE FROM caixa WHERE pedido_id = ?", (pedido_id,))
        db.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

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

# ============ ROTAS DE CAIXA DIÁRIO ============
@app.route("/api/gerente/caixa/resetar", methods=["POST"])
@login_required
def resetar_caixa():
    try:
        resultado = resetar_caixa_dia()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/caixa/diario", methods=["GET"])
@login_required
def get_caixa_diario():
    try:
        caixa = get_caixa_dia()
        return jsonify({
            "data": caixa[0],
            "saldo_inicial": caixa[1] or 0,
            "entradas": caixa[2] or 0,
            "saidas": caixa[3] or 0,
            "saldo_final": caixa[4] or 0
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/caixa/historico", methods=["GET"])
@login_required
def get_caixa_historico():
    try:
        db = get_db_gerente()
        historico = db.execute("SELECT * FROM caixa_historico ORDER BY data DESC LIMIT 30").fetchall()
        return jsonify([dict(h) for h in historico])
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ API GERENTE - CLIENTES ============
@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    db = get_db_gerente()
    busca = request.args.get("busca")
    if busca:
        rows = db.execute("SELECT * FROM clientes WHERE nome LIKE ? ORDER BY nome", (f"%{busca}%",)).fetchall()
    else:
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

# ============ API GERENTE - COMANDAS ============
@app.route("/api/gerente/comandas", methods=["GET"])
@login_required
def gerente_listar_comandas():
    db = get_db_gerente()
    try:
        rows = db.execute("SELECT * FROM comandas ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

@app.route("/api/gerente/comandas", methods=["POST"])
@login_required
def gerente_criar_comanda():
    dados = request.get_json() or {}
    db = get_db_gerente()
    ticket = "CMD-" + datetime.now().strftime("%Y%m%d%H%M%S")
    cur = db.execute(
        """INSERT INTO comandas (ticket, cliente_nome, cliente_telefone, profissional, servicos, valor_total, status, pagamento)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (ticket, dados.get('cliente_nome'), dados.get('cliente_telefone'), dados.get('profissional'),
         dados.get('servicos'), dados.get('valor_total', 0), dados.get('status', 'aberta'), dados.get('pagamento'))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/comandas/<int:comanda_id>", methods=["DELETE"])
@login_required
def gerente_deletar_comanda(comanda_id):
    db = get_db_gerente()
    db.execute("DELETE FROM comandas WHERE id=?", (comanda_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ API GERENTE - REPASSES ============
@app.route("/api/gerente/repasses", methods=["GET"])
@login_required
def gerente_listar_repasses():
    db = get_db_gerente()
    try:
        rows = db.execute("SELECT * FROM repasses ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

@app.route("/api/gerente/repasses/resumo", methods=["GET"])
@login_required
def gerente_repasses_resumo():
    db = get_db_gerente()
    try:
        pendente = db.execute("SELECT COALESCE(SUM(comissao),0) FROM repasses WHERE status='pendente'").fetchone()[0]
        pago = db.execute("SELECT COALESCE(SUM(comissao),0) FROM repasses WHERE status='pago'").fetchone()[0]
    except:
        pendente, pago = 0, 0
    return jsonify({"total_pendente": pendente, "total_pago": pago})

@app.route("/api/gerente/repasses", methods=["POST"])
@login_required
def gerente_criar_repasse():
    dados = request.get_json() or {}
    db = get_db_gerente()
    porcentagem = dados.get('porcentagem', 50)
    valor_servico = dados.get('valor_servico', 0)
    comissao = valor_servico * (porcentagem / 100)
    cur = db.execute(
        """INSERT INTO repasses (profissional, servico_nome, valor_servico, comissao, status)
           VALUES (?, ?, ?, ?, ?)""",
        (dados.get('profissional'), dados.get('servico_nome'), valor_servico, comissao, dados.get('status', 'pendente'))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/repasses/<int:repasse_id>", methods=["DELETE"])
@login_required
def gerente_deletar_repasse(repasse_id):
    db = get_db_gerente()
    db.execute("DELETE FROM repasses WHERE id=?", (repasse_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ API GERENTE - CAIXA ============
@app.route("/api/gerente/caixa", methods=["GET"])
@login_required
def gerente_listar_caixa():
    db = get_db_gerente()
    try:
        rows = db.execute("SELECT * FROM caixa ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

@app.route("/api/gerente/caixa", methods=["POST"])
@login_required
def gerente_criar_caixa():
    dados = request.get_json() or {}
    db = get_db_gerente()
    cur = db.execute(
        "INSERT INTO caixa (tipo, descricao, pagamento, valor) VALUES (?, ?, ?, ?)",
        (dados.get('tipo'), dados.get('descricao'), dados.get('pagamento'), dados.get('valor', 0))
    )
    db.commit()
    return jsonify({"status": "ok", "id": cur.lastrowid})

@app.route("/api/gerente/caixa/<int:caixa_id>", methods=["DELETE"])
@login_required
def gerente_deletar_caixa(caixa_id):
    db = get_db_gerente()
    db.execute("DELETE FROM caixa WHERE id=?", (caixa_id,))
    db.commit()
    return jsonify({"status": "ok"})

# ============ API GERENTE - PERFIL ============
@app.route("/api/gerente/alterar_nome", methods=["POST"])
@login_required
def gerente_alterar_nome():
    dados = request.get_json() or {}
    novo_nome = dados.get("novo_nome", "").strip()
    if not novo_nome:
        return jsonify({"erro": "Nome inválido"}), 400
    db = get_db_gerente()
    db.execute("UPDATE gerentes SET nome=? WHERE id=?", (novo_nome, session["gerente_id"]))
    db.commit()
    session["gerente_nome"] = novo_nome
    return jsonify({"status": "ok"})

@app.route("/api/gerente/alterar_login", methods=["POST"])
@login_required
def gerente_alterar_login():
    dados = request.get_json() or {}
    senha_atual = dados.get("senha_atual", "")
    novo_usuario = dados.get("novo_usuario", "").strip()
    nova_senha = dados.get("nova_senha", "")
    db = get_db_gerente()
    row = db.execute("SELECT * FROM gerentes WHERE id = ?", (session["gerente_id"],)).fetchone()
    if not row or row["senha_hash"] != senha_atual:
        return jsonify({"erro": "Senha atual incorreta"}), 401
    if novo_usuario:
        db.execute("UPDATE gerentes SET usuario=? WHERE id=?", (novo_usuario, session["gerente_id"]))
    if nova_senha:
        db.execute("UPDATE gerentes SET senha_hash=? WHERE id=?", (nova_senha, session["gerente_id"]))
    db.commit()
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/relatorio/pdf", methods=["GET"])
@login_required
def gerente_relatorio_pdf():
    return jsonify({"erro": "Geração de PDF ainda não implementada"}), 501

# ============ INICIAR ============


# ============ CRUD SERVIÇOS ============
@app.route("/api/servicos", methods=["POST"])
@login_required
def api_criar_servico():
    try:
        dados = request.get_json(force=True, silent=True) or {}
        if not dados.get("nome"):
            return jsonify({"erro": "Nome é obrigatório"}), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO servicos (nome, preco, duracao_min, ativo, ordem) VALUES (?, ?, ?, ?, ?)",
            (dados.get('nome'), dados.get('preco', 0), dados.get('duracao_min', 30),
             dados.get('ativo', 1), dados.get('ordem', 0))
        )
        db.commit()
        return jsonify({"status": "ok", "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/servicos/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_servico(item_id):
    try:
        dados = request.get_json(force=True, silent=True) or {}
        db = get_db()
        db.execute(
            "UPDATE servicos SET nome=?, preco=?, duracao_min=?, ativo=? WHERE id=?",
            (dados.get('nome'), dados.get('preco', 0), dados.get('duracao_min', 30),
             dados.get('ativo', 1), item_id)
        )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/servicos/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_servico(item_id):
    try:
        db = get_db()
        db.execute("DELETE FROM servicos WHERE id=?", (item_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ CRUD PRODUTOS ============
@app.route("/api/produtos", methods=["POST"])
@login_required
def api_criar_produto():
    try:
        dados = request.get_json(force=True, silent=True) or {}
        if not dados.get("nome"):
            return jsonify({"erro": "Nome é obrigatório"}), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO produtos (nome, preco, ativo, ordem) VALUES (?, ?, ?, ?)",
            (dados.get('nome'), dados.get('preco', 0), dados.get('ativo', 1), dados.get('ordem', 0))
        )
        db.commit()
        return jsonify({"status": "ok", "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/produtos/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_produto(item_id):
    try:
        dados = request.get_json(force=True, silent=True) or {}
        db = get_db()
        db.execute(
            "UPDATE produtos SET nome=?, preco=?, ativo=? WHERE id=?",
            (dados.get('nome'), dados.get('preco', 0), dados.get('ativo', 1), item_id)
        )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/produtos/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_produto(item_id):
    try:
        db = get_db()
        db.execute("DELETE FROM produtos WHERE id=?", (item_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ CRUD PROFISSIONAIS ============
@app.route("/api/profissionais", methods=["POST"])
@login_required
def api_criar_profissional():
    try:
        dados = request.get_json(force=True, silent=True) or {}
        if not dados.get("nome"):
            return jsonify({"erro": "Nome é obrigatório"}), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO profissionais (nome, especialidade, ativo, ordem) VALUES (?, ?, ?, ?)",
            (dados.get('nome'), dados.get('especialidade', ''), dados.get('ativo', 1), dados.get('ordem', 0))
        )
        db.commit()
        return jsonify({"status": "ok", "id": cur.lastrowid})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/profissionais/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_profissional(item_id):
    try:
        dados = request.get_json(force=True, silent=True) or {}
        db = get_db()
        db.execute(
            "UPDATE profissionais SET nome=?, especialidade=?, ativo=? WHERE id=?",
            (dados.get('nome'), dados.get('especialidade', ''), dados.get('ativo', 1), item_id)
        )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/profissionais/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_profissional(item_id):
    try:
        db = get_db()
        db.execute("DELETE FROM profissionais WHERE id=?", (item_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ CRUD ASSINATURAS ============
@app.route("/api/assinaturas", methods=["POST"])
@login_required
def api_criar_assinatura():
    try:
        dados = request.get_json(force=True, silent=True) or {}
        if not dados.get("nome"):
            return jsonify({"erro": "Nome é obrigatório"}), 400
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
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/assinaturas/<int:item_id>", methods=["PUT"])
@login_required
def api_atualizar_assinatura(item_id):
    try:
        dados = request.get_json(force=True, silent=True) or {}
        db = get_db()
        db.execute(
            "UPDATE assinaturas SET nome=?, preco=?, icone=?, descricao=?, destaque=?, ativo=? WHERE id=?",
            (dados.get('nome'), dados.get('preco', 0), dados.get('icone', '⭐'),
             dados.get('descricao', ''), dados.get('destaque', 0), dados.get('ativo', 1), item_id)
        )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/assinaturas/<int:item_id>", methods=["DELETE"])
@login_required
def api_deletar_assinatura(item_id):
    try:
        db = get_db()
        db.execute("DELETE FROM assinaturas WHERE id=?", (item_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 SQLite + Baserow + Caixa Diário")
    print("="*60)
    app.run(debug=True, host="0.0.0.0", port=5000)
