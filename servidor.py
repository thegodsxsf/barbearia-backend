"""
Servidor da Barbearia Studio Leblon - Baserow
"""
import os
import sqlite3
from datetime import date, datetime, timedelta
import getpass
import requests
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia-2024"

# ============ BASEROW CONFIG ============

BASEROW_TOKENS = {
    "pedidos": "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I",
    "clientes": "YIrPD6ZzuWYNTTj2vnYmg2EXYw4eCvKe",
    "barbeiros": "aWCJDxStBDUTlrB9sKJM1UI9TY4aqXke",
    "produtos": "3WGb3R2ZcEgemPNWrHvZeFKLGiFj6d4j"
}

BASEROW_TABLES = {
    "pedidos": "1083808",
    "clientes": "1085282",
    "barbeiros": "1085289",
    "produtos": "1085294"
}

def baserow_request(method, table, data=None, item_id=None):
    """Função genérica para Baserow"""
    token = BASEROW_TOKENS.get(table)
    table_id = BASEROW_TABLES.get(table)
    if not token or not table_id:
        return {"error": "Tabela não configurada"}
    
    url = f"https://api.baserow.io/api/database/rows/table/{table_id}/?user_field_names=true"
    if item_id:
        url = f"https://api.baserow.io/api/database/rows/table/{table_id}/{item_id}/?user_field_names=true"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return {"error": "Método inválido"}
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ Erro Baserow: {response.status_code} - {response.text}")
            return {"error": f"Erro {response.status_code}"}
    except Exception as e:
        print(f"❌ Erro: {e}")
        return {"error": str(e)}

def listar_baserow(table):
    return baserow_request("GET", table)

def criar_baserow(table, data):
    return baserow_request("POST", table, data)

def atualizar_baserow(table, item_id, data):
    return baserow_request("PUT", table, data, item_id)

def deletar_baserow(table, item_id):
    return baserow_request("DELETE", table, item_id=item_id)

# ============ BANCO SQLITE (APENAS LOGIN) ============

DB_GERENTE_PATH = os.path.join(BASE_DIR, "banco_gerente.db")

def get_db_gerente():
    if "db_gerente" not in g:
        g.db_gerente = sqlite3.connect(DB_GERENTE_PATH)
        g.db_gerente.row_factory = sqlite3.Row
    return g.db_gerente

def init_db_gerente():
    if os.path.exists(DB_GERENTE_PATH):
        return
    conn = sqlite3.connect(DB_GERENTE_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS gerentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            nome TEXT DEFAULT 'Gerente'
        );
    """)
    # Criar usuário padrão
    conn.execute("INSERT OR IGNORE INTO gerentes (usuario, senha_hash, nome) VALUES ('barbe', 'barbe', 'Gerente')")
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db_gerente", None)
    if db:
        db.close()

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
    dados = request.get_json(force=True, silent=True) or {}
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

# ============ CATÁLOGO ============

@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    result = listar_baserow("barbeiros")
    if "error" in result:
        return jsonify([])
    items = []
    for item in result.get("results", []):
        items.append({
            "id": item.get("id"),
            "nome": item.get("profissional", ""),
            "especialidade": item.get("descrição", ""),
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(items)

@app.route("/api/servicos", methods=["GET"])
def api_servicos():
    result = listar_baserow("produtos")
    if "error" in result:
        return jsonify([])
    items = []
    for item in result.get("results", []):
        preco = 0
        try:
            preco = float(str(item.get("valor", "0")).replace("R$", "").replace(",", ".").strip())
        except:
            pass
        items.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "preco": preco,
            "duracao_min": 30,
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(items)

@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    return api_servicos()

# ============ GERENTE - PROFISSIONAIS ============

@app.route("/api/gerente/profissionais", methods=["POST"])
@login_required
def gerente_criar_profissional():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "profissional": dados.get("nome"),
        "descrição": dados.get("especialidade", "")
    }
    result = criar_baserow("barbeiros", data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/profissionais/<int:item_id>", methods=["PUT"])
@login_required
def gerente_editar_profissional(item_id):
    dados = request.get_json(force=True, silent=True) or {}
    data = {}
    if "nome" in dados:
        data["profissional"] = dados["nome"]
    if "especialidade" in dados:
        data["descrição"] = dados["especialidade"]
    result = atualizar_baserow("barbeiros", item_id, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

@app.route("/api/gerente/profissionais/<int:item_id>", methods=["DELETE"])
@login_required
def gerente_deletar_profissional(item_id):
    result = deletar_baserow("barbeiros", item_id)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

# ============ GERENTE - SERVIÇOS ============

@app.route("/api/gerente/servicos", methods=["POST"])
@login_required
def gerente_criar_servico():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "nome": dados.get("nome"),
        "valor": str(dados.get("preco", 0)),
        "tempo": str(dados.get("duracao_min", 30)) + " min"
    }
    result = criar_baserow("produtos", data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/servicos/<int:item_id>", methods=["PUT"])
@login_required
def gerente_editar_servico(item_id):
    dados = request.get_json(force=True, silent=True) or {}
    data = {}
    if "nome" in dados:
        data["nome"] = dados["nome"]
    if "preco" in dados:
        data["valor"] = str(dados["preco"])
    if "duracao_min" in dados:
        data["tempo"] = str(dados["duracao_min"]) + " min"
    result = atualizar_baserow("produtos", item_id, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

@app.route("/api/gerente/servicos/<int:item_id>", methods=["DELETE"])
@login_required
def gerente_deletar_servico(item_id):
    result = deletar_baserow("produtos", item_id)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

# ============ GERENTE - CLIENTES ============

@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    result = listar_baserow("clientes")
    if "error" in result:
        return jsonify([])
    items = []
    for item in result.get("results", []):
        items.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "telefone": item.get("contato", ""),
            "cpf": item.get("cpf", ""),
            "endereco": item.get("endereço", ""),
            "data_cadastro": datetime.now().isoformat()
        })
    return jsonify(items)

@app.route("/api/gerente/clientes", methods=["POST"])
@login_required
def gerente_criar_cliente():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "nome": dados.get("nome"),
        "contato": dados.get("telefone", ""),
        "cpf": dados.get("cpf", ""),
        "endereço": dados.get("endereco", "")
    }
    result = criar_baserow("clientes", data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/clientes/<int:item_id>", methods=["PUT"])
@login_required
def gerente_editar_cliente(item_id):
    dados = request.get_json(force=True, silent=True) or {}
    data = {}
    if "nome" in dados:
        data["nome"] = dados["nome"]
    if "telefone" in dados:
        data["contato"] = dados["telefone"]
    if "cpf" in dados:
        data["cpf"] = dados["cpf"]
    if "endereco" in dados:
        data["endereço"] = dados["endereco"]
    result = atualizar_baserow("clientes", item_id, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes/<int:item_id>", methods=["DELETE"])
@login_required
def gerente_deletar_cliente(item_id):
    result = deletar_baserow("clientes", item_id)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

# ============ GERENTE - PEDIDOS ============

@app.route("/api/gerente/pedidos", methods=["GET"])
@login_required
def gerente_listar_pedidos():
    result = listar_baserow("pedidos")
    if "error" in result:
        return jsonify([])
    items = []
    for item in result.get("results", []):
        valor = 0
        try:
            valor = float(str(item.get("valor", "0")).replace("R$", "").replace(",", ".").strip())
        except:
            pass
        items.append({
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
    return jsonify(items)

@app.route("/api/gerente/pedidos/<int:item_id>", methods=["PUT"])
@login_required
def gerente_atualizar_pedido(item_id):
    dados = request.get_json(force=True, silent=True) or {}
    novo_status = dados.get("status")
    if novo_status not in ["pendente", "confirmado", "concluido", "cancelado"]:
        return jsonify({"erro": "Status inválido"}), 400
    data = {"Status": novo_status}
    result = atualizar_baserow("pedidos", item_id, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:item_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(item_id):
    result = deletar_baserow("pedidos", item_id)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

# ============ GERENTE - DASHBOARD ============

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

# ============ OUTRAS ROTAS ============

@app.route("/api/horarios", methods=["GET"])
def api_horarios():
    horarios = [
        {"id": 1, "dia_semana": 0, "abertura": "09:00", "fechamento": "12:00", "pausa_inicio": None, "pausa_fim": None, "ativo": 0},
        {"id": 2, "dia_semana": 1, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"id": 3, "dia_semana": 2, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"id": 4, "dia_semana": 3, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"id": 5, "dia_semana": 4, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"id": 6, "dia_semana": 5, "abertura": "09:00", "fechamento": "19:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
        {"id": 7, "dia_semana": 6, "abertura": "09:00", "fechamento": "18:00", "pausa_inicio": "13:00", "pausa_fim": "14:00", "ativo": 1},
    ]
    return jsonify(horarios)

@app.route("/api/horarios", methods=["PUT"])
def api_update_horarios():
    return jsonify({"status": "ok"})

@app.route("/api/verificar-horario", methods=["POST"])
def verificar_horario():
    return jsonify({"disponivel": True, "mensagem": "✅ Horário disponível!"})

@app.route("/api/horarios-ocupados", methods=["POST"])
def horarios_ocupados():
    return jsonify({"data": "", "horarios_ocupados": [], "total": 0})

@app.route("/api/gerente/configuracoes", methods=["GET"])
@login_required
def gerente_get_configuracoes():
    return jsonify({
        "nome": "Barbearia Studio Leblon",
        "endereco": "Rua Maganel, nº 1477, Curado, Recife, PE",
        "whatsapp": "5581995654683",
        "logo": "/static/logo.jpeg",
        "cor_primaria": "#3ddc84",
        "cor_fundo": "#0a0a0e"
    })

@app.route("/api/gerente/configuracoes", methods=["PUT"])
@login_required
def gerente_update_configuracoes():
    return jsonify({"status": "ok"})

@app.route("/config.js")
def serve_config():
    return send_from_directory(BASE_DIR, "config.js")

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
    print("  🚀 Barbearia Studio Leblon - Baserow")
    print("="*60)
    init_db_gerente()
    print("✅ Servidor pronto!")
    print("🔗 http://localhost:5000")
    print("🔐 /gerente/login (barbe/barbe)")
    app.run(debug=True, host="0.0.0.0", port=5000)
