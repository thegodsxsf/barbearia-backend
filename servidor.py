"""
Servidor da Barbearia Studio Leblon
------------------------------------
Usando Baserow como banco de dados principal
Apenas o login do gerente fica no SQLite local
"""

import os
import sqlite3
from datetime import date, datetime, timedelta
import getpass
import requests
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ BANCO SQLITE (APENAS PARA LOGIN) ============
DB_GERENTE_PATH = os.path.join(BASE_DIR, "banco_gerente.db")

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao-leblon-2026")

# ============ BASEROW CONFIGURATIONS ============

# 1. PEDIDOS
BASEROW_PEDIDOS_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_PEDIDOS_TABLE = "1083808"
BASEROW_PEDIDOS_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_PEDIDOS_TABLE}/?user_field_names=true"

# 2. CLIENTES
BASEROW_CLIENTES_TOKEN = "YIrPD6ZzuWYNTTj2vnYmg2EXYw4eCvKe"
BASEROW_CLIENTES_TABLE = "1085282"
BASEROW_CLIENTES_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_CLIENTES_TABLE}/?user_field_names=true"

# 3. BARBEIROS
BASEROW_BARBEIROS_TOKEN = "aWCJDxStBDUTlrB9sKJM1UI9TY4aqXke"
BASEROW_BARBEIROS_TABLE = "1085289"
BASEROW_BARBEIROS_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_BARBEIROS_TABLE}/?user_field_names=true"

# 4. PRODUTOS/SERVIÇOS
BASEROW_PRODUTOS_TOKEN = "3WGb3R2ZcEgemPNWrHvZeFKLGiFj6d4j"
BASEROW_PRODUTOS_TABLE = "1085294"
BASEROW_PRODUTOS_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_PRODUTOS_TABLE}/?user_field_names=true"

# 5. ASSINATURAS (criar tabela no Baserow com: nome, preco, descricao, beneficios)
BASEROW_ASSINATURAS_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_ASSINATURAS_TABLE = "SEU_TABLE_ID_AQUI"  # Substitua pelo ID da tabela
BASEROW_ASSINATURAS_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_ASSINATURAS_TABLE}/?user_field_names=true"

# 6. COMANDAS (criar tabela no Baserow com: ticket, cliente, profissional, servicos, valor, status, pagamento)
BASEROW_COMANDAS_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_COMANDAS_TABLE = "SEU_TABLE_ID_AQUI"  # Substitua pelo ID da tabela
BASEROW_COMANDAS_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_COMANDAS_TABLE}/?user_field_names=true"

# 7. REPASSES (criar tabela no Baserow com: profissional, servico, valor, comissao, status)
BASEROW_REPASSES_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_REPASSES_TABLE = "SEU_TABLE_ID_AQUI"  # Substitua pelo ID da tabela
BASEROW_REPASSES_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_REPASSES_TABLE}/?user_field_names=true"

# 8. CAIXA (criar tabela no Baserow com: tipo, valor, descricao, pagamento)
BASEROW_CAIXA_TOKEN = "jivqqHBFnvvVWwmgGPPtqTZLPHcaT38I"
BASEROW_CAIXA_TABLE = "SEU_TABLE_ID_AQUI"  # Substitua pelo ID da tabela
BASEROW_CAIXA_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_CAIXA_TABLE}/?user_field_names=true"


# ============ FUNÇÕES BASEROW ============

def baserow_request(method, url, data=None, token=None):
    """Função genérica para requisições ao Baserow"""
    if not token:
        return {"error": "Token não configurado"}
    try:
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return {"error": "Método não suportado"}
        
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            print(f"❌ Erro Baserow: {response.status_code} - {response.text}")
            return {"error": f"Erro {response.status_code}"}
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {"error": str(e)}

def listar_do_baserow(url, token):
    """Lista registros do Baserow"""
    return baserow_request("GET", url, token=token)

def criar_do_baserow(url, token, data):
    """Cria registro no Baserow"""
    return baserow_request("POST", url, data=data, token=token)

def atualizar_do_baserow(url, token, data):
    """Atualiza registro no Baserow"""
    return baserow_request("PUT", url, data=data, token=token)

def deletar_do_baserow(url, token):
    """Deleta registro no Baserow"""
    return baserow_request("DELETE", url, token=token)


# ============ BANCO SQLITE (APENAS LOGIN) ============

def get_db_gerente():
    if "db_gerente" not in g:
        os.makedirs(os.path.dirname(DB_GERENTE_PATH) or ".", exist_ok=True)
        g.db_gerente = sqlite3.connect(DB_GERENTE_PATH)
        g.db_gerente.row_factory = sqlite3.Row
    return g.db_gerente

def init_db_gerente():
    if os.path.exists(DB_GERENTE_PATH):
        print("📁 Banco do gerente já existe.")
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
    """)
    conn.commit()
    print("✅ Banco do gerente criado!")
    conn.close()

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db_gerente", None)
    if db is not None:
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

@app.route("/api/gerente/alterar_nome", methods=["POST"])
@login_required
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
@login_required
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


# ============ ROTAS PRINCIPAIS ============

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


# ============ ROTAS DE CATÁLOGO (BASEROW) ============

@app.route("/api/servicos", methods=["GET"])
def api_servicos():
    result = listar_do_baserow(BASEROW_PRODUTOS_URL, BASEROW_PRODUTOS_TOKEN)
    if "error" in result:
        return jsonify([])
    # Adaptar os dados para o formato esperado pelo frontend
    servicos = []
    for item in result.get("results", []):
        servicos.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "preco": float(item.get("valor", "0").replace("R$", "").replace(",", ".").strip() or 0),
            "duracao_min": 30,
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(servicos)

@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    result = listar_do_baserow(BASEROW_PRODUTOS_URL, BASEROW_PRODUTOS_TOKEN)
    if "error" in result:
        return jsonify([])
    produtos = []
    for item in result.get("results", []):
        produtos.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "preco": float(item.get("valor", "0").replace("R$", "").replace(",", ".").strip() or 0),
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(produtos)

@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    result = listar_do_baserow(BASEROW_BARBEIROS_URL, BASEROW_BARBEIROS_TOKEN)
    if "error" in result:
        return jsonify([])
    profissionais = []
    for item in result.get("results", []):
        profissionais.append({
            "id": item.get("id"),
            "nome": item.get("profissional", ""),
            "especialidade": item.get("descrição", ""),
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(profissionais)

@app.route("/api/assinaturas", methods=["GET"])
def api_assinaturas():
    result = listar_do_baserow(BASEROW_ASSINATURAS_URL, BASEROW_ASSINATURAS_TOKEN)
    if "error" in result:
        return jsonify([])
    assinaturas = []
    for item in result.get("results", []):
        assinaturas.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "preco": float(item.get("preco", "0").replace("R$", "").replace(",", ".").strip() or 0),
            "descricao": item.get("descricao", ""),
            "beneficios": item.get("beneficios", ""),
            "ativo": 1,
            "ordem": 0
        })
    return jsonify(assinaturas)


# ============ ROTAS DE CLIENTES (BASEROW) ============

@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    result = listar_do_baserow(BASEROW_CLIENTES_URL, BASEROW_CLIENTES_TOKEN)
    if "error" in result:
        return jsonify([])
    clientes = []
    for item in result.get("results", []):
        clientes.append({
            "id": item.get("id"),
            "nome": item.get("nome", ""),
            "telefone": item.get("contato", ""),
            "cpf": item.get("cpf", ""),
            "endereco": item.get("endereço", ""),
            "data_cadastro": datetime.now().isoformat()
        })
    return jsonify(clientes)

@app.route("/api/gerente/clientes", methods=["POST"])
@login_required
def gerente_criar_cliente():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    data = {
        "nome": dados.get("nome", ""),
        "contato": dados.get("telefone", ""),
        "cpf": dados.get("cpf", ""),
        "endereço": dados.get("endereco", "")
    }
    result = criar_do_baserow(BASEROW_CLIENTES_URL, BASEROW_CLIENTES_TOKEN, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["PUT"])
@login_required
def gerente_editar_cliente(cliente_id):
    dados = request.get_json(force=True, silent=True) or {}
    url = f"{BASEROW_CLIENTES_URL}{cliente_id}/"
    data = {}
    if "nome" in dados:
        data["nome"] = dados["nome"]
    if "telefone" in dados:
        data["contato"] = dados["telefone"]
    if "cpf" in dados:
        data["cpf"] = dados["cpf"]
    if "endereco" in dados:
        data["endereço"] = dados["endereco"]
    result = atualizar_do_baserow(url, BASEROW_CLIENTES_TOKEN, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["DELETE"])
@login_required
def gerente_deletar_cliente(cliente_id):
    url = f"{BASEROW_CLIENTES_URL}{cliente_id}/"
    result = deletar_do_baserow(url, BASEROW_CLIENTES_TOKEN)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})


# ============ ROTAS DE PEDIDOS (BASEROW) ============

@app.route("/api/pedidos", methods=["POST"])
def api_criar_pedido():
    dados = request.get_json(force=True, silent=True) or {}
    campos_obrigatorios = ["tipo", "servico_nome", "cliente_nome"]
    if any(not dados.get(c) for c in campos_obrigatorios):
        return jsonify({"erro": "Dados incompletos"}), 400
    
    data = {
        "Cliente": dados.get("cliente_nome", ""),
        "Serviço": dados.get("servico_nome", ""),
        "Data/Hora": dados.get("data_agendada", "") + " " + (dados.get("hora_agendada", "") or ""),
        "valor": f"R$ {float(dados.get('valor', 0)):.2f}",
        "Status": "pendente",
        "Profissional": dados.get("profissional", ""),
        "Pagamento": dados.get("pagamento", ""),
        "Telefone": dados.get("cliente_telefone", ""),
        "CPF": dados.get("cliente_cpf", "")
    }
    result = criar_do_baserow(BASEROW_PEDIDOS_URL, BASEROW_PEDIDOS_TOKEN, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok", "id": result.get("id")})

@app.route("/api/gerente/pedidos", methods=["GET"])
@login_required
def gerente_listar_pedidos():
    result = listar_do_baserow(BASEROW_PEDIDOS_URL, BASEROW_PEDIDOS_TOKEN)
    if "error" in result:
        return jsonify([])
    pedidos = []
    for item in result.get("results", []):
        pedidos.append({
            "id": item.get("id"),
            "cliente_nome": item.get("Cliente", ""),
            "servico_nome": item.get("Serviço", ""),
            "data_agendada": item.get("Data/Hora", "").split(" ")[0] if item.get("Data/Hora") else "",
            "hora_agendada": item.get("Data/Hora", "").split(" ")[1] if len(item.get("Data/Hora", "").split(" ")) > 1 else "",
            "valor": float(item.get("valor", "0").replace("R$", "").replace(",", ".").strip() or 0),
            "status": item.get("Status", "pendente"),
            "profissional": item.get("Profissional", ""),
            "pagamento": item.get("Pagamento", ""),
            "cliente_telefone": item.get("Telefone", ""),
            "cliente_cpf": item.get("CPF", ""),
            "criado_em": datetime.now().isoformat()
        })
    return jsonify(pedidos)

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["PUT"])
@login_required
def gerente_atualizar_pedido(pedido_id):
    dados = request.get_json(force=True, silent=True) or {}
    novo_status = dados.get("status")
    if novo_status not in ("pendente", "confirmado", "concluido", "cancelado"):
        return jsonify({"erro": "Status inválido"}), 400
    url = f"{BASEROW_PEDIDOS_URL}{pedido_id}/"
    data = {"Status": novo_status}
    result = atualizar_do_baserow(url, BASEROW_PEDIDOS_TOKEN, data)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    url = f"{BASEROW_PEDIDOS_URL}{pedido_id}/"
    result = deletar_do_baserow(url, BASEROW_PEDIDOS_TOKEN)
    if "error" in result:
        return jsonify({"erro": result["error"]}), 500
    return jsonify({"status": "ok"})


# ============ DASHBOARD ============

@app.route("/api/gerente/dashboard")
@login_required
def gerente_dashboard():
    pedidos = listar_do_baserow(BASEROW_PEDIDOS_URL, BASEROW_PEDIDOS_TOKEN)
    pedidos_list = pedidos.get("results", []) if "error" not in pedidos else []
    
    faturamento_total = 0
    pendentes = 0
    for p in pedidos_list:
        valor_str = p.get("valor", "0").replace("R$", "").replace(",", ".").strip()
        try:
            valor = float(valor_str)
            faturamento_total += valor
        except:
            pass
        if p.get("Status") == "pendente":
            pendentes += 1
    
    return jsonify({
        "faturamento_total": faturamento_total,
        "saidas_total": 0,
        "saldo": faturamento_total,
        "pedidos_pendentes": pendentes,
        "agendamentos_hoje": 0,
        "total_clientes": 0,
        "assinaturas_ativas": 0,
        "comandas_abertas": 0,
        "repasses_pendentes": 0
    })


# ============ ROTAS DE CONFIGURAÇÕES ============

@app.route("/api/gerente/configuracoes", methods=["GET"])
@login_required
def gerente_get_configuracoes():
    return jsonify({
        "nome": "Barbearia Studio Leblon",
        "endereco": "Rua Maganel, nº 1477, Curado, Recife, PE",
        "whatsapp": "5581995654683",
        "logo": "/static/logo.jpeg",
        "cor_primaria": "#3ddc84",
        "cor_fundo": "#0a0a0e",
        "cor_texto": "#eeeeef"
    })

@app.route("/api/gerente/configuracoes", methods=["PUT"])
@login_required
def gerente_update_configuracoes():
    return jsonify({"status": "ok"})


# ============ ROTAS DE HORÁRIOS ============

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


# ============ ROTAS DE VERIFICAÇÃO ============

@app.route("/api/verificar-horario", methods=["POST"])
def verificar_horario():
    return jsonify({"disponivel": True, "mensagem": "✅ Horário disponível!"})

@app.route("/api/horarios-ocupados", methods=["POST"])
def horarios_ocupados():
    return jsonify({"data": "", "horarios_ocupados": [], "total": 0})


# ============ ROTAS DE RELATÓRIOS ============

@app.route("/api/gerente/relatorio/pdf")
@login_required
def gerente_relatorio_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from io import BytesIO
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "RELATÓRIO - Barbearia Studio Leblon")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar PDF: {str(e)}"}), 500


# ============ ROTAS DE COMANDAS, REPASSES, CAIXA ============

@app.route("/api/gerente/comandas", methods=["GET"])
@login_required
def gerente_listar_comandas():
    return jsonify([])

@app.route("/api/gerente/comandas", methods=["POST"])
@login_required
def gerente_criar_comanda():
    return jsonify({"status": "ok", "id": 1, "ticket": "TICKET-0001"})

@app.route("/api/gerente/comandas/<int:comanda_id>", methods=["PUT"])
@login_required
def gerente_atualizar_comanda(comanda_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/comandas/<int:comanda_id>", methods=["DELETE"])
@login_required
def gerente_deletar_comanda(comanda_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/repasses", methods=["GET"])
@login_required
def gerente_listar_repasses():
    return jsonify([])

@app.route("/api/gerente/repasses", methods=["POST"])
@login_required
def gerente_criar_repasse():
    return jsonify({"status": "ok", "id": 1})

@app.route("/api/gerente/repasses/<int:repasse_id>", methods=["PUT"])
@login_required
def gerente_atualizar_repasse(repasse_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/repasses/<int:repasse_id>", methods=["DELETE"])
@login_required
def gerente_deletar_repasse(repasse_id):
    return jsonify({"status": "ok"})

@app.route("/api/gerente/repasses/resumo")
@login_required
def gerente_resumo_repasses():
    return jsonify({"total_pendente": 0, "total_pago": 0, "profissionais": []})

@app.route("/api/gerente/caixa", methods=["GET"])
@login_required
def gerente_listar_caixa():
    return jsonify([])

@app.route("/api/gerente/caixa", methods=["POST"])
@login_required
def gerente_criar_caixa():
    return jsonify({"status": "ok"})

@app.route("/api/gerente/caixa/<int:caixa_id>", methods=["DELETE"])
@login_required
def gerente_deletar_caixa(caixa_id):
    return jsonify({"status": "ok"})


# ============ CONFIG.JS ============

@app.route("/config.js")
def serve_config():
    return send_from_directory(BASE_DIR, "config.js")


# ============ INICIAR ============

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🚀 INICIANDO SERVIDOR - Barbearia Studio Leblon")
    print("="*60 + "\n")
    print("📋 Usando Baserow como banco de dados principal")
    print("   Apenas login do gerente fica no SQLite")
    print("")
    
    init_db_gerente()
    
    print("\n" + "="*60)
    print("  ✅ SERVIDOR PRONTO!")
    print("="*60)
    print("  🌐 Site do cliente:    http://localhost:5000/")
    print("  🔐 Painel do gerente:  http://localhost:5000/gerente/login")
    print("="*60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
