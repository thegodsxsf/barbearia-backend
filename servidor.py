"""
Servidor Barbearia - Baserow
"""
import os
import sqlite3
from datetime import datetime
import requests
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, send_file
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia"
CORS(app)

# ============ BASEROW ============
BASEROW_CONFIG = {
    "pedidos": {"token": "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I", "table": "1083808"},
    "clientes": {"token": "YIrPD6ZzuWYNTTj2vnYmg2EXYw4eCvKe", "table": "1085282"},
    "barbeiros": {"token": "aWCJDxStBDUTlrB9sKJM1UI9TY4aqXke", "table": "1085289"},
    "produtos": {"token": "3WGb3R2ZcEgemPNWrHvZeFKLGiFj6d4j", "table": "1085294"}
}

def baserow_get(table):
    config = BASEROW_CONFIG.get(table)
    if not config:
        return []
    url = f"https://api.baserow.io/api/database/rows/table/{config['table']}/?user_field_names=true"
    headers = {"Authorization": f"Token {config['token']}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    except Exception as e:
        print(f"Erro Baserow GET: {e}")
        return []

def baserow_post(table, data):
    config = BASEROW_CONFIG.get(table)
    if not config:
        return None
    url = f"https://api.baserow.io/api/database/rows/table/{config['table']}/?user_field_names=true"
    headers = {"Authorization": f"Token {config['token']}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=10)
        if r.status_code in [200, 201]:
            return r.json()
        return None
    except Exception as e:
        print(f"Erro Baserow POST: {e}")
        return None

# ============ LOGIN ============
DB_GERENTE = os.path.join(BASE_DIR, "banco_gerente.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_GERENTE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()

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
    dados = baserow_get("produtos")
    if not dados:
        return jsonify([])
    resultados = []
    for item in dados:
        try:
            preco = float(str(item.get("valor", "0")).replace("R$", "").replace(",", ".").strip() or 0)
        except:
            preco = 0
        resultados.append({
            "id": item.get("id"),
            "nome": item.get("nome", "Sem nome"),
            "preco": preco,
            "duracao_min": 30,
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(resultados)

@app.route("/api/assinaturas", methods=["GET"])
def api_assinaturas():
    return jsonify([])

@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    dados = baserow_get("barbeiros")
    if not dados:
        return jsonify([])
    resultados = []
    for item in dados:
        resultados.append({
            "id": item.get("id"),
            "nome": item.get("profissional", "Sem nome"),
            "especialidade": item.get("descrição", ""),
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(resultados)

@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    return jsonify([])

@app.route("/api/horarios", methods=["GET"])
def api_horarios():
    return jsonify([
        {"dia_semana": 0, "abertura": "09:00", "fechamento": "12:00", "ativo": 0},
        {"dia_semana": 1, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"dia_semana": 2, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"dia_semana": 3, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"dia_semana": 4, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"dia_semana": 5, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"dia_semana": 6, "abertura": "09:00", "fechamento": "18:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
    ])

@app.route("/api/verificar-horario", methods=["POST"])
def verificar_horario():
    return jsonify({"disponivel": True})

@app.route("/api/horarios-ocupados", methods=["POST"])
def horarios_ocupados():
    return jsonify({"horarios_ocupados": [], "total": 0})

@app.route("/api/barbearia", methods=["GET"])
def api_barbearia():
    return jsonify({
        "nome": "Barbearia Studio Leblon",
        "endereco": "Av. Liberdade, 1477 - Totó, Recife - PE",
        "whatsapp": "5581995654683"
    })

@app.route("/api/imagens", methods=["GET"])
def api_imagens():
    return jsonify([])

# ============ API GERENTE ============

@app.route("/api/gerente/login", methods=["POST"])
def gerente_login():
    dados = request.get_json() or {}
    usuario = dados.get("usuario", "").strip()
    senha = dados.get("senha", "")
    db = get_db()
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
    return jsonify({
        "faturamento_total": 0,
        "saidas_total": 0,
        "saldo": 0,
        "pedidos_pendentes": 0,
        "agendamentos_hoje": 0,
        "total_clientes": 0,
        "assinaturas_ativas": 0,
        "comandas_abertas": 0,
        "repasses_pendentes": 0
    })

@app.route("/api/gerente/pedidos", methods=["GET"])
@login_required
def gerente_listar_pedidos():
    dados = baserow_get("pedidos")
    if not dados:
        return jsonify([])
    resultados = []
    for item in dados:
        try:
            valor = float(str(item.get("valor", "0")).replace("R$", "").replace(",", ".").strip() or 0)
        except:
            valor = 0
        resultados.append({
            "id": item.get("id"),
            "cliente_nome": item.get("Cliente", ""),
            "servico_nome": item.get("Serviço", ""),
            "data_agendada": item.get("Data/Hora", "").split(" ")[0] if item.get("Data/Hora") else "",
            "hora_agendada": item.get("Data/Hora", "").split(" ")[1] if " " in item.get("Data/Hora", "") else "",
            "valor": valor,
            "status": item.get("Status", "pendente"),
            "profissional": item.get("Profissional", ""),
            "pagamento": item.get("Pagamento", ""),
            "cliente_telefone": item.get("Telefone", ""),
            "cliente_cpf": item.get("CPF", ""),
            "criado_em": datetime.now().isoformat()
        })
    return jsonify(resultados)

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["PUT"])
@login_required
def gerente_atualizar_pedido(pedido_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    dados = baserow_get("clientes")
    if not dados:
        return jsonify([])
    resultados = []
    for item in dados:
        resultados.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "telefone": item.get("contato", ""),
            "cpf": item.get("cpf", ""),
            "endereco": item.get("endereço", ""),
            "data_cadastro": datetime.now().isoformat()
        })
    return jsonify(resultados)

@app.route("/api/gerente/clientes", methods=["POST"])
@login_required
def gerente_criar_cliente():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "nome": dados.get("nome", ""),
        "contato": dados.get("telefone", ""),
        "cpf": dados.get("cpf", ""),
        "endereço": dados.get("endereco", "")
    }
    result = baserow_post("clientes", data)
    if not result:
        return jsonify({"erro": "Erro ao criar cliente"}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["PUT"])
@login_required
def gerente_editar_cliente(cliente_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["DELETE"])
@login_required
def gerente_deletar_cliente(cliente_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/profissionais", methods=["POST"])
@login_required
def gerente_criar_profissional():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "profissional": dados.get("nome", ""),
        "descrição": dados.get("especialidade", "")
    }
    result = baserow_post("barbeiros", data)
    if not result:
        return jsonify({"erro": "Erro ao criar profissional"}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/profissionais/<int:item_id>", methods=["PUT"])
@login_required
def gerente_editar_profissional(item_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/profissionais/<int:item_id>", methods=["DELETE"])
@login_required
def gerente_deletar_profissional(item_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/servicos", methods=["POST"])
@login_required
def gerente_criar_servico():
    dados = request.get_json() or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "nome": dados.get("nome", ""),
        "valor": str(dados.get("preco", 0)),
        "tempo": str(dados.get("duracao_min", 30)) + " min"
    }
    result = baserow_post("produtos", data)
    if not result:
        return jsonify({"erro": "Erro ao criar serviço"}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/configuracoes", methods=["GET"])
@login_required
def gerente_get_configuracoes():
    return jsonify({
        "nome": "Barbearia Studio Leblon",
        "endereco": "Av. Liberdade, 1477 - Totó, Recife - PE",
        "whatsapp": "5581995654683",
        "logo": "/static/logo.jpeg",
        "cor_primaria": "#3ddc84",
        "cor_fundo": "#0a0a0e"
    })

@app.route("/api/gerente/configuracoes", methods=["PUT"])
@login_required
def gerente_update_configuracoes():
    return jsonify({"status": "ok"})

@app.route("/api/gerente/comandas", methods=["GET"])
@login_required
def gerente_listar_comandas():
    return jsonify([])

@app.route("/api/gerente/comandas", methods=["POST"])
@login_required
def gerente_criar_comanda():
    return jsonify({"status": "ok", "id": 1, "ticket": "TICKET-0001"})

@app.route("/api/gerente/repasses", methods=["GET"])
@login_required
def gerente_listar_repasses():
    return jsonify([])

@app.route("/api/gerente/repasses", methods=["POST"])
@login_required
def gerente_criar_repasse():
    return jsonify({"status": "ok", "id": 1})

@app.route("/api/gerente/caixa", methods=["GET"])
@login_required
def gerente_listar_caixa():
    return jsonify([])

@app.route("/api/gerente/caixa", methods=["POST"])
@login_required
def gerente_criar_caixa():
    return jsonify({"status": "ok"})

# ============ INICIAR ============

if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 Usando Baserow como banco de dados")
    print("="*60)
    app.run(debug=True, host="0.0.0.0", port=5000)
