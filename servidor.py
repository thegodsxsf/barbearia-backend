import os
import sqlite3
from datetime import date, datetime, timedelta
import requests
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "banco.db")
DB_GERENTE_PATH = os.path.join(BASE_DIR, "banco_gerente.db")

app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia"

# ============ BASEROW CONFIGS ============
BASEROW_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_TABLE_ID = "1083808"
BASEROW_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"

BASEROW_TOKEN_PLANOS = "QkqtK3vb5i6mxWLl2aPl23auZBn6VsXx"
BASEROW_TABLE_PLANOS_ID = "1090225"
BASEROW_URL_PLANOS = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_PLANOS_ID}/?user_field_names=true"

BASEROW_TOKEN_EQUIPE = "PcDmkO9N9yOr1appjvn3sPrRl6rQrv5q"
BASEROW_TABLE_EQUIPE_ID = "1090262"
BASEROW_URL_EQUIPE = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_EQUIPE_ID}/?user_field_names=true"

BASEROW_TOKEN_PRODUTOS = "UwjXa3HePyc6ClaA66AyZYevyjoEHmAf"
BASEROW_TABLE_PRODUTOS_ID = "1090278"
BASEROW_URL_PRODUTOS = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_PRODUTOS_ID}/?user_field_names=true"

BASEROW_TOKEN_ASSINANTES = "Yy9lUDvUu6jCIE13khP6ZUOlVO2tQkqm"
BASEROW_TABLE_ASSINANTES_ID = "1090158"
BASEROW_URL_ASSINANTES = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ASSINANTES_ID}/?user_field_names=true"

# ============ FUNÇÕES BASEROW ============
def listar_produtos_baserow():
    try:
        response = requests.get(BASEROW_URL_PRODUTOS, headers={"Authorization": f"Token {BASEROW_TOKEN_PRODUTOS}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            produtos = data.get('results', [])
            resultado = []
            for p in produtos:
                try:
                    preco_str = p.get('preço', '0').replace('R$', '').replace(',', '.').strip()
                    preco = float(preco_str) if preco_str else 0
                except:
                    preco = 0
                resultado.append({'id': p.get('id'), 'nome': p.get('nome', ''), 'preco': preco, 'ativo': 1})
            return resultado
        return []
    except:
        return []

def criar_produto_baserow(dados):
    try:
        dados_envio = {
            "nome": dados.get('nome', ''),
            "preço": f"R$ {float(dados.get('preco', 0)):.2f}".replace('.', ',')
        }
        response = requests.post(BASEROW_URL_PRODUTOS, json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_PRODUTOS}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            return response.json().get('id')
        return None
    except:
        return None

def atualizar_produto_baserow(produto_id, dados):
    try:
        dados_envio = {}
        if 'nome' in dados:
            dados_envio['nome'] = dados['nome']
        if 'preco' in dados:
            dados_envio['preço'] = f"R$ {float(dados['preco']):.2f}".replace('.', ',')
        if not dados_envio:
            return True
        response = requests.patch(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_PRODUTOS_ID}/{produto_id}/?user_field_names=true", json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_PRODUTOS}", "Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

def deletar_produto_baserow(produto_id):
    try:
        response = requests.delete(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_PRODUTOS_ID}/{produto_id}/?user_field_names=true", headers={"Authorization": f"Token {BASEROW_TOKEN_PRODUTOS}"}, timeout=10)
        return response.status_code in [200, 204]
    except:
        return False

def listar_equipe_baserow():
    try:
        response = requests.get(BASEROW_URL_EQUIPE, headers={"Authorization": f"Token {BASEROW_TOKEN_EQUIPE}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            membros = data.get('results', [])
            return [{'id': m.get('id'), 'nome': m.get('nome', ''), 'especialidade': m.get('especialidade', ''), 'ativo': 1} for m in membros]
        return []
    except:
        return []

def criar_membro_equipe_baserow(dados):
    try:
        dados_envio = {"nome": dados.get('nome', ''), "especialidade": dados.get('especialidade', '')}
        response = requests.post(BASEROW_URL_EQUIPE, json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_EQUIPE}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            return response.json().get('id')
        return None
    except:
        return None

def atualizar_membro_equipe_baserow(membro_id, dados):
    try:
        dados_envio = {}
        if 'nome' in dados:
            dados_envio['nome'] = dados['nome']
        if 'especialidade' in dados:
            dados_envio['especialidade'] = dados['especialidade']
        if not dados_envio:
            return True
        response = requests.patch(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_EQUIPE_ID}/{membro_id}/?user_field_names=true", json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_EQUIPE}", "Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

def deletar_membro_equipe_baserow(membro_id):
    try:
        response = requests.delete(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_EQUIPE_ID}/{membro_id}/?user_field_names=true", headers={"Authorization": f"Token {BASEROW_TOKEN_EQUIPE}"}, timeout=10)
        return response.status_code in [200, 204]
    except:
        return False

def listar_planos_baserow():
    try:
        response = requests.get(BASEROW_URL_PLANOS, headers={"Authorization": f"Token {BASEROW_TOKEN_PLANOS}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            planos = data.get('results', [])
            resultado = []
            for p in planos:
                try:
                    preco_str = p.get('preço', '0').replace('R$', '').replace(',', '.').strip()
                    preco = float(preco_str) if preco_str else 0
                except:
                    preco = 0
                resultado.append({'id': p.get('id'), 'nome': p.get('nome', ''), 'preco': preco, 'descricao': p.get('descrição', ''), 'icone': '⭐', 'destaque': 0, 'ativo': 1, 'cor': '#3ddc84'})
            return resultado
        return []
    except:
        return []

def criar_plano_baserow(dados):
    try:
        dados_envio = {
            "nome": dados.get('nome', ''),
            "preço": f"R$ {float(dados.get('preco', 0)):.2f}".replace('.', ','),
            "descrição": dados.get('descricao', '')
        }
        response = requests.post(BASEROW_URL_PLANOS, json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_PLANOS}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            return response.json().get('id')
        return None
    except:
        return None

def atualizar_plano_baserow(plano_id, dados):
    try:
        dados_envio = {}
        if 'nome' in dados:
            dados_envio['nome'] = dados['nome']
        if 'preco' in dados:
            dados_envio['preço'] = f"R$ {float(dados['preco']):.2f}".replace('.', ',')
        if 'descricao' in dados:
            dados_envio['descrição'] = dados['descricao']
        if not dados_envio:
            return True
        response = requests.patch(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_PLANOS_ID}/{plano_id}/?user_field_names=true", json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_PLANOS}", "Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

def deletar_plano_baserow(plano_id):
    try:
        response = requests.delete(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_PLANOS_ID}/{plano_id}/?user_field_names=true", headers={"Authorization": f"Token {BASEROW_TOKEN_PLANOS}"}, timeout=10)
        return response.status_code in [200, 204]
    except:
        return False

def listar_assinantes_baserow():
    try:
        response = requests.get(BASEROW_URL_ASSINANTES, headers={"Authorization": f"Token {BASEROW_TOKEN_ASSINANTES}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            assinantes = data.get('results', [])
            resultado = []
            for a in assinantes:
                resultado.append({
                    'id': a.get('id'),
                    'nome': a.get('nome', 'Sem nome'),
                    'telefone': a.get('contato', ''),
                    'nascimento': a.get('nascimento', ''),
                    'plano': a.get('plano', ''),
                    'valor': 0,
                    'status': 'ativo' if a.get('Active') == 'Sim' else 'cancelado',
                    'criado_em': a.get('created_on', '')
                })
            return resultado
        return []
    except:
        return []

def criar_assinante_baserow(dados):
    try:
        dados_envio = {
            "nome": dados.get('nome', ''),
            "contato": dados.get('telefone', ''),
            "Active": "Sim" if dados.get('status') == 'ativo' else "Nao",
            "nascimento": dados.get('nascimento', ''),
            "plano": dados.get('plano', ''),
            "valor": dados.get('valor', 0)
        }
        response = requests.post(BASEROW_URL_ASSINANTES, json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_ASSINANTES}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            return response.json().get('id')
        return None
    except:
        return None

def atualizar_assinante_baserow(assinante_id, dados):
    try:
        dados_envio = {}
        if 'nome' in dados:
            dados_envio['nome'] = dados['nome']
        if 'telefone' in dados:
            dados_envio['contato'] = dados['telefone']
        if 'status' in dados:
            dados_envio['Active'] = "Sim" if dados['status'] == 'ativo' else "Nao"
        if 'nascimento' in dados:
            dados_envio['nascimento'] = dados['nascimento']
        if 'plano' in dados:
            dados_envio['plano'] = dados['plano']
        if 'valor' in dados:
            dados_envio['valor'] = dados['valor']
        if not dados_envio:
            return True
        response = requests.patch(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ASSINANTES_ID}/{assinante_id}/?user_field_names=true", json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_ASSINANTES}", "Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

def deletar_assinante_baserow(assinante_id):
    try:
        response = requests.delete(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ASSINANTES_ID}/{assinante_id}/?user_field_names=true", headers={"Authorization": f"Token {BASEROW_TOKEN_ASSINANTES}"}, timeout=10)
        return response.status_code in [200, 204]
    except:
        return False

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

# ============ ROTAS PÁGINAS ============
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
    return jsonify({"nome": "Leblon Studio", "endereco": "Av. Liberdade, 1477 - Totó, Recife - PE", "whatsapp": "558181365730"})

@app.route("/api/servicos", methods=["GET"])
def api_servicos_get():
    try:
        db = get_db()
        rows = db.execute("SELECT * FROM servicos WHERE ativo = 1 ORDER BY ordem, id").fetchall()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    return jsonify(listar_equipe_baserow())

@app.route("/api/assinaturas", methods=["GET"])
def api_assinaturas():
    return jsonify(listar_planos_baserow())

@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    return jsonify(listar_produtos_baserow())

@app.route("/api/imagens", methods=["GET"])
def api_imagens():
    try:
        db = get_db()
        rows = db.execute("SELECT * FROM imagens WHERE ativo = 1 ORDER BY ordem, id").fetchall()
        return jsonify([dict(r) for r in rows])
    except:
        return jsonify([])

# ============ API GERENTE LOGIN ============
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

# ============ DASHBOARD (CORRIGIDO) ============
@app.route("/api/gerente/dashboard")
@login_required
def gerente_dashboard():
    db = get_db_gerente()
    
    # FATURAMENTO TOTAL (histórico completo da tabela caixa)
    faturamento_total = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='entrada'").fetchone()[0] or 0
    saidas_total = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='saida'").fetchone()[0] or 0
    
    # SALDO DO DIA (da tabela caixa_diario)
    hoje = date.today().isoformat()
    caixa_dia = db.execute("SELECT * FROM caixa_diario WHERE data = ?", (hoje,)).fetchone()
    
    if caixa_dia:
        saldo_atual = caixa_dia[4] if caixa_dia[4] else 0
        entradas_hoje = caixa_dia[2] if caixa_dia[2] else 0
        saidas_hoje = caixa_dia[3] if caixa_dia[3] else 0
        saldo_inicial = caixa_dia[1] if caixa_dia[1] else 0
    else:
        saldo_atual = 0
        entradas_hoje = 0
        saidas_hoje = 0
        saldo_inicial = 0
        db.execute(
            "INSERT INTO caixa_diario (data, saldo_inicial, entradas, saidas, saldo_final) VALUES (?, 0, 0, 0, 0)",
            (hoje,)
        )
        db.commit()
    
    # Pedidos
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status='pendente'").fetchone()[0] or 0
    agendamentos_hoje = db.execute("SELECT COUNT(*) FROM pedidos WHERE data_agendada = ? AND status != 'cancelado'", (hoje,)).fetchone()[0] or 0
    total_clientes = db.execute("SELECT COUNT(DISTINCT cliente_nome) FROM pedidos").fetchone()[0] or 0
    
    planos = listar_planos_baserow()
    equipe = listar_equipe_baserow()
    produtos = listar_produtos_baserow()
    
    return jsonify({
        "faturamento_total": faturamento_total,
        "saidas_total": saidas_total,
        "saldo": saldo_atual,  # SALDO DO DIA (vem do caixa_diario)
        "saldo_inicial": saldo_inicial,
        "entradas_hoje": entradas_hoje,
        "saidas_hoje": saidas_hoje,
        "pedidos_pendentes": pendentes,
        "agendamentos_hoje": agendamentos_hoje,
        "total_clientes": total_clientes,
        "assinaturas_ativas": len(planos),
        "comandas_abertas": 0,
        "repasses_pendentes": 0,
        "total_equipe": len(equipe),
        "total_produtos": len(produtos)
    })

# ============ PEDIDOS ============
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
        
        valor = pedido[3]
        servico = pedido[2]
        cliente = pedido[4]
        pagamento = pedido[10] if len(pedido) > 10 else "manual"
        status_atual = pedido[11] if len(pedido) > 11 else "pendente"
        
        if novo_status == "concluido" and status_atual != "concluido":
            ja_lancado = db.execute("SELECT COUNT(*) FROM caixa WHERE pedido_id = ?", (pedido_id,)).fetchone()[0]
            if not ja_lancado:
                db.execute(
                    "INSERT INTO caixa (tipo, descricao, pagamento, valor, pedido_id) VALUES (?, ?, ?, ?, ?)",
                    ("entrada", f"{servico} - {cliente}", pagamento, valor, pedido_id)
                )
                hoje = date.today().isoformat()
                caixa_dia = db.execute("SELECT * FROM caixa_diario WHERE data = ?", (hoje,)).fetchone()
                if caixa_dia:
                    novas_entradas = (caixa_dia[2] or 0) + valor
                    novo_saldo = (caixa_dia[1] or 0) + novas_entradas - (caixa_dia[3] or 0)
                    db.execute(
                        "UPDATE caixa_diario SET entradas = ?, saldo_final = ? WHERE data = ?",
                        (novas_entradas, novo_saldo, hoje)
                    )
                else:
                    db.execute(
                        "INSERT INTO caixa_diario (data, saldo_inicial, entradas, saidas, saldo_final) VALUES (?, 0, ?, 0, ?)",
                        (hoje, valor, valor)
                    )
                print(f"✅ Pedido {pedido_id} concluído! R$ {valor:.2f} adicionado ao caixa.")
        
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        db.commit()
        return jsonify({"status": "ok"})
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    try:
        db = get_db_gerente()
        pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if not pedido:
            return jsonify({"erro": "Pedido não encontrado"}), 404
        db.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
        db.commit()
        print(f"🗑️ Pedido {pedido_id} excluído com sucesso!")
        return jsonify({"status": "ok", "mensagem": "Pedido excluído com sucesso"})
    except Exception as e:
        print(f"❌ ERRO ao deletar pedido {pedido_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

# ============ CLIENTES ============
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

# ============ PLANOS (BASEROW) ============
@app.route("/api/gerente/planos", methods=["GET"])
@login_required
def gerente_listar_planos():
    return jsonify(listar_planos_baserow())

@app.route("/api/gerente/planos", methods=["POST"])
@login_required
def gerente_criar_plano():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    plano_id = criar_plano_baserow(dados)
    if plano_id:
        return jsonify({"status": "ok", "id": plano_id})
    return jsonify({"erro": "Erro ao criar plano"}), 500

@app.route("/api/gerente/planos/<int:plano_id>", methods=["PUT"])
@login_required
def gerente_atualizar_plano(plano_id):
    dados = request.get_json(force=True, silent=True) or {}
    if atualizar_plano_baserow(plano_id, dados):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar plano"}), 500

@app.route("/api/gerente/planos/<int:plano_id>", methods=["DELETE"])
@login_required
def gerente_deletar_plano(plano_id):
    if deletar_plano_baserow(plano_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar plano"}), 500

# ============ EQUIPE (BASEROW) ============
@app.route("/api/gerente/equipe", methods=["GET"])
@login_required
def gerente_listar_equipe():
    return jsonify(listar_equipe_baserow())

@app.route("/api/gerente/equipe", methods=["POST"])
@login_required
def gerente_criar_membro():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    membro_id = criar_membro_equipe_baserow(dados)
    if membro_id:
        return jsonify({"status": "ok", "id": membro_id})
    return jsonify({"erro": "Erro ao criar membro"}), 500

@app.route("/api/gerente/equipe/<int:membro_id>", methods=["PUT"])
@login_required
def gerente_atualizar_membro(membro_id):
    dados = request.get_json(force=True, silent=True) or {}
    if atualizar_membro_equipe_baserow(membro_id, dados):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar membro"}), 500

@app.route("/api/gerente/equipe/<int:membro_id>", methods=["DELETE"])
@login_required
def gerente_deletar_membro(membro_id):
    if deletar_membro_equipe_baserow(membro_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar membro"}), 500

# ============ PRODUTOS (BASEROW) ============
@app.route("/api/gerente/produtos", methods=["GET"])
@login_required
def gerente_listar_produtos():
    return jsonify(listar_produtos_baserow())

@app.route("/api/gerente/produtos", methods=["POST"])
@login_required
def gerente_criar_produto():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    produto_id = criar_produto_baserow(dados)
    if produto_id:
        return jsonify({"status": "ok", "id": produto_id})
    return jsonify({"erro": "Erro ao criar produto"}), 500

@app.route("/api/gerente/produtos/<int:produto_id>", methods=["PUT"])
@login_required
def gerente_atualizar_produto(produto_id):
    dados = request.get_json(force=True, silent=True) or {}
    if atualizar_produto_baserow(produto_id, dados):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar produto"}), 500

@app.route("/api/gerente/produtos/<int:produto_id>", methods=["DELETE"])
@login_required
def gerente_deletar_produto(produto_id):
    if deletar_produto_baserow(produto_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar produto"}), 500

# ============ ASSINANTES (BASEROW) ============
@app.route("/api/gerente/assinantes", methods=["GET"])
@login_required
def gerente_listar_assinantes():
    try:
        assinantes = listar_assinantes_baserow()
        return jsonify(assinantes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/assinantes", methods=["POST"])
@login_required
def gerente_criar_assinante():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    assinante_id = criar_assinante_baserow(dados)
    if assinante_id:
        return jsonify({"status": "ok", "id": assinante_id})
    return jsonify({"erro": "Erro ao criar assinante"}), 500

@app.route("/api/gerente/assinantes/<int:assinante_id>", methods=["PUT"])
@login_required
def gerente_atualizar_assinante(assinante_id):
    dados = request.get_json(force=True, silent=True) or {}
    if atualizar_assinante_baserow(assinante_id, dados):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar assinante"}), 500

@app.route("/api/gerente/assinantes/<int:assinante_id>", methods=["DELETE"])
@login_required
def gerente_deletar_assinante(assinante_id):
    if deletar_assinante_baserow(assinante_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar assinante"}), 500

# ============ VERIFICAR HORÁRIO ============
@app.route("/api/verificar_horario", methods=["POST"])
def verificar_horario():
    try:
        dados = request.get_json() or {}
        data = dados.get("data")
        hora = dados.get("hora")
        profissional = dados.get("profissional", "")
        
        print(f"🔍 Verificando: data={data}, hora={hora}, profissional={profissional}")
        
        if not data or not hora:
            return jsonify({"erro": "Data e hora são obrigatórias"}), 400
        
        db = get_db_gerente()
        
        query = """
            SELECT COUNT(*) as total 
            FROM pedidos 
            WHERE data_agendada = ? 
            AND hora_agendada = ? 
            AND status IN ('pendente', 'confirmado')
        """
        params = [data, hora]
        
        if profissional:
            query += " AND profissional = ?"
            params.append(profissional)
        
        print(f"📝 Query: {query}")
        print(f"📝 Params: {params}")
        
        row = db.execute(query, params).fetchone()
        ocupado = row[0] > 0 if row else False
        
        print(f"📊 Ocupado (mesmo profissional): {ocupado}")
        
        return jsonify({
            "disponivel": not ocupado,
            "mensagem": "Horário indisponível para este profissional" if ocupado else "Horário disponível"
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({"erro": str(e)}), 500

# ============ CAIXA - RESETAR ============
@app.route("/api/gerente/caixa/resetar", methods=["POST"])
@login_required
def resetar_caixa():
    try:
        db = get_db_gerente()
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
        
        return jsonify({"status": "ok", "mensagem": "Caixa resetado para R$ 0,00"})
        
    except Exception as e:
        print(f"❌ Erro ao resetar caixa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

# ============ SERVIÇOS (ADMIN) ============
@app.route("/api/servicos", methods=["POST"])
@login_required
def api_servicos_post():
    try:
        dados = request.get_json(force=True, silent=True)
        if not dados or not dados.get("nome"):
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
def api_servicos_put(item_id):
    try:
        dados = request.get_json(force=True, silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
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
def api_servicos_delete(item_id):
    try:
        db = get_db()
        db.execute("DELETE FROM servicos WHERE id=?", (item_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ COMANDAS ============
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

# ============ REPASSES ============
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
        pendente = db.execute("SELECT COALESCE(SUM(comissao),0) FROM repasses WHERE status='pendente'").fetchone()[0] or 0
        pago = db.execute("SELECT COALESCE(SUM(comissao),0) FROM repasses WHERE status='pago'").fetchone()[0] or 0
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

# ============ CAIXA ============
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

# ============ HORÁRIOS ============
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

# ============ PERFIL ============
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

# ============ INICIALIZAÇÃO ============
# ============ RESETAR FATURAMENTO ============
@app.route("/api/gerente/resetar_faturamento", methods=["POST"])
@login_required
def resetar_faturamento():
    try:
        db = get_db_gerente()
        db.execute("DELETE FROM caixa")
        hoje = date.today().isoformat()
        db.execute("INSERT OR REPLACE INTO caixa_diario (data, saldo_inicial, entradas, saidas, saldo_final) VALUES (?, 0, 0, 0, 0)", (hoje,))
        db.commit()
        return jsonify({"status": "ok", "mensagem": "Faturamento resetado para R$ 0,00"})
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 SQLite + Baserow")
    print("="*60)
    app.run(debug=True, host="0.0.0.0", port=5000)


