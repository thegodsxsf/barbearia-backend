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

# ============ ASSINANTES (BASEROW) ============
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
    except Exception as e:
        print(f"Erro ao listar assinantes: {e}")
        return []

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
    entradas = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='entrada'").fetchone()[0] or 0
    saidas = db.execute("SELECT COALESCE(SUM(valor),0) FROM caixa WHERE tipo='saida'").fetchone()[0] or 0
    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status='pendente'").fetchone()[0] or 0
    hoje = date.today().isoformat()
    agendamentos_hoje = db.execute("SELECT COUNT(*) FROM pedidos WHERE data_agendada = ? AND status != 'cancelado'", (hoje,)).fetchone()[0] or 0
    total_clientes = db.execute("SELECT COUNT(DISTINCT cliente_nome) FROM pedidos").fetchone()[0] or 0
    planos = listar_planos_baserow()
    equipe = listar_equipe_baserow()
    produtos = listar_produtos_baserow()
    return jsonify({
        "faturamento_total": entradas,
        "saidas_total": saidas,
        "saldo": entradas - saidas,
        "saldo_inicial": 0,
        "entradas_hoje": 0,
        "saidas_hoje": 0,
        "pedidos_pendentes": pendentes,
        "agendamentos_hoje": agendamentos_hoje,
        "total_clientes": total_clientes,
        "assinaturas_ativas": len(planos),
        "comandas_abertas": 0,
        "repasses_pendentes": 0,
        "total_equipe": len(equipe),
        "total_produtos": len(produtos)
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
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    try:
        db = get_db_gerente()
        db.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    db = get_db_gerente()
    rows = db.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/gerente/planos", methods=["GET"])
@login_required
def gerente_listar_planos():
    return jsonify(listar_planos_baserow())

@app.route("/api/gerente/equipe", methods=["GET"])
@login_required
def gerente_listar_equipe():
    return jsonify(listar_equipe_baserow())

@app.route("/api/gerente/produtos", methods=["GET"])
@login_required
def gerente_listar_produtos():
    return jsonify(listar_produtos_baserow())

# ============ ASSINANTES ROTAS ============
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
    try:
        dados = request.get_json(force=True, silent=True) or {}
        if not dados.get("nome"):
            return jsonify({"erro": "Nome é obrigatório"}), 400
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
            return jsonify({"status": "ok", "id": response.json().get('id')})
        return jsonify({"erro": f"Erro no Baserow: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/assinantes/<int:assinante_id>", methods=["PUT"])
@login_required
def gerente_atualizar_assinante(assinante_id):
    try:
        dados = request.get_json(force=True, silent=True) or {}
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
            return jsonify({"status": "ok"})
        response = requests.patch(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ASSINANTES_ID}/{assinante_id}/?user_field_names=true", json=dados_envio, headers={"Authorization": f"Token {BASEROW_TOKEN_ASSINANTES}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            return jsonify({"status": "ok"})
        return jsonify({"erro": f"Erro no Baserow: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/assinantes/<int:assinante_id>", methods=["DELETE"])
@login_required
def gerente_deletar_assinante(assinante_id):
    try:
        response = requests.delete(f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ASSINANTES_ID}/{assinante_id}/?user_field_names=true", headers={"Authorization": f"Token {BASEROW_TOKEN_ASSINANTES}"}, timeout=10)
        if response.status_code in [200, 204]:
            return jsonify({"status": "ok"})
        return jsonify({"erro": f"Erro no Baserow: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ SERVIÇOS ============
@app.route("/api/servicos", methods=["GET"])
def api_servicos():
    db = get_db()
    rows = db.execute("SELECT * FROM servicos WHERE ativo = 1 ORDER BY ordem, id").fetchall()
    return jsonify([dict(r) for r in rows])

# ============ INICIALIZAÇÃO ============
if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 SQLite + Baserow")
    print("="*60)
    app.run(debug=True, host="0.0.0.0", port=5000)
