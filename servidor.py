import os
import requests
import re
from datetime import date, datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, g, session, redirect, Response
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder="static")
app.secret_key = "chave-secreta-barbearia"

# ============ BASEROW CONFIGS ============
BASEROW_TOKEN = "4tKiir8cwC5MvMu0Cgj9X5ewrzQn8jNR"
BASEROW_TABLE_ID = "1094351"
BASEROW_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"

# ============ FUNÇÕES BASEROW ============
def baserow_get(categoria=None):
    """Busca TODOS os registros da tabela (com paginação) e filtra localmente por categoria.
    Isso evita depender do filtro remoto do Baserow, que falha quando 'categoria' é
    um campo de selecao (single select) em vez de texto simples."""
    try:
        todos = []
        url = BASEROW_URL + "&size=200"
        while url:
            response = requests.get(url, headers={"Authorization": f"Token {BASEROW_TOKEN}"}, timeout=10)
            if response.status_code != 200:
                print(f"❌ Erro Baserow GET: Status {response.status_code}")
                break
            data = response.json()
            todos.extend(data.get('results', []))
            url = data.get('next')
        if categoria:
            alvo = categoria.strip().lower()
            todos = [r for r in todos if str(r.get('categoria', '')).strip().lower() == alvo]
        return todos
    except Exception as e:
        print(f"❌ Erro Baserow GET: {e}")
        return []

def baserow_post(dados):
    """Cria um novo registro na tabela Customers."""
    try:
        print(f"📤 Enviando para Baserow: {dados}")
        response = requests.post(BASEROW_URL, json=dados, headers={"Authorization": f"Token {BASEROW_TOKEN}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            print(f"✅ Registro criado: ID {response.json().get('id')}")
            return response.json().get('id')
        print(f"❌ Erro Baserow POST: Status {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"❌ Erro Baserow POST: {e}")
        return None

def baserow_patch(item_id, dados):
    """Atualiza um registro existente na tabela Customers."""
    try:
        url = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/{item_id}/?user_field_names=true"
        response = requests.patch(url, json=dados, headers={"Authorization": f"Token {BASEROW_TOKEN}", "Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            print(f"✅ Registro {item_id} atualizado")
            return True
        print(f"❌ Erro Baserow PATCH: Status {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Erro Baserow PATCH: {e}")
        return False

def baserow_delete(item_id):
    """Deleta um registro da tabela Customers."""
    try:
        url = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/{item_id}/?user_field_names=true"
        response = requests.delete(url, headers={"Authorization": f"Token {BASEROW_TOKEN}"}, timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Erro Baserow DELETE: {e}")
        return False

# ============ LOGIN ============
def login_required(f):
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

# ============ GERENTE LOGIN ============
@app.route("/api/gerente/login", methods=["POST"])
def gerente_login():
    dados = request.get_json() or {}
    usuario = dados.get("usuario", "").strip()
    senha = dados.get("senha", "")
    
    gerentes = baserow_get("gerente")
    for g in gerentes:
        if g.get('nome') == usuario and g.get('senha') == senha:
            session["gerente_id"] = g.get('id')
            session["gerente_nome"] = g.get('nome')
            return jsonify({"status": "ok", "nome": g.get('nome')})
    
    return jsonify({"erro": "Usuário ou senha inválidos"}), 401

@app.route("/api/gerente/logout", methods=["POST"])
def gerente_logout():
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/api/gerente/me")
def gerente_me():
    if not session.get("gerente_id"):
        return jsonify({"erro": "Não autenticado"}), 401
    return jsonify({"nome": session.get("gerente_nome")})

# ============ DASHBOARD ============
@app.route("/api/gerente/dashboard")
@login_required
def gerente_dashboard():
    pedidos = baserow_get("pedido")
    pendentes = len([p for p in pedidos if p.get('status') == 'pendente'])
    
    planos = baserow_get("plano")
    equipe = baserow_get("equipe")
    produtos = baserow_get("produto")
    
    hoje = date.today().isoformat()
    agendamentos_hoje = len([p for p in pedidos if p.get('data_agendada') == hoje and p.get('status') != 'cancelado'])
    
    # Busca dados do caixa
    caixa = baserow_get("caixa")
    entradas_caixa = sum(float(c.get('preço', 0)) for c in caixa if c.get('tipo') == 'entrada')
    saidas_caixa = sum(float(c.get('preço', 0)) for c in caixa if c.get('tipo') == 'saida')
    saldo_caixa = entradas_caixa - saidas_caixa
    
    # Busca comandas abertas
    comandas = baserow_get("comanda")
    comandas_abertas = len([c for c in comandas if c.get('status') == 'aberta'])
    
    # Busca repasses pendentes
    repasses = baserow_get("repasse")
    repasses_pendentes = len([r for r in repasses if r.get('status') == 'pendente'])
    
    return jsonify({
        "faturamento_total": entradas_caixa,
        "saidas_total": saidas_caixa,
        "saldo": saldo_caixa,
        "saldo_inicial": 0,
        "entradas_hoje": entradas_caixa,
        "saidas_hoje": saidas_caixa,
        "pedidos_pendentes": pendentes,
        "agendamentos_hoje": agendamentos_hoje,
        "total_clientes": len(baserow_get("cliente")),
        "assinaturas_ativas": len(planos),
        "comandas_abertas": comandas_abertas,
        "repasses_pendentes": repasses_pendentes,
        "total_equipe": len(equipe),
        "total_produtos": len(produtos)
    })

# ============ SERVIÇOS ============
@app.route("/api/servicos", methods=["GET"])
def api_servicos_get():
    items = baserow_get("servico")
    resultado = []
    for item in items:
        try:
            preco = float(item.get('preço', 0)) if item.get('preço') else 0
            duracao = int(item.get('duração', 30)) if item.get('duração') else 30
        except:
            preco = 0
            duracao = 30
        resultado.append({
            'id': item.get('id'), 
            'nome': item.get('nome', ''), 
            'preco': preco, 
            'duracao_min': duracao, 
            'ativo': 1
        })
    return jsonify(resultado)

@app.route("/api/servicos", methods=["POST"])
@login_required
def api_servicos_post():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'):
        return jsonify({"erro": "Nome é obrigatório"}), 400
    item = {
        "nome": dados.get('nome', ''), 
        "preço": str(dados.get('preco', 0)), 
        "duração": str(dados.get('duracao_min', 30)), 
        "categoria": "servico"
    }
    item_id = baserow_post(item)
    if item_id:
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar serviço"}), 500

@app.route("/api/servicos/<int:item_id>", methods=["PUT"])
@login_required
def api_servicos_put(item_id):
    dados = request.get_json(force=True, silent=True) or {}
    item = {}
    if 'nome' in dados: item['nome'] = dados['nome']
    if 'preco' in dados: item['preço'] = str(dados['preco'])
    if 'duracao_min' in dados: item['duração'] = str(dados['duracao_min'])
    if baserow_patch(item_id, item): return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar serviço"}), 500

@app.route("/api/servicos/<int:item_id>", methods=["DELETE"])
@login_required
def api_servicos_delete(item_id):
    if baserow_delete(item_id): return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar serviço"}), 500

# ============ PRODUTOS ============
@app.route("/api/produtos", methods=["GET"])
def api_produtos():
    items = baserow_get("produto")
    resultado = []
    for item in items:
        try: 
            preco = float(item.get('preço', 0)) if item.get('preço') else 0
        except: 
            preco = 0
        resultado.append({
            'id': item.get('id'), 
            'nome': item.get('nome', ''), 
            'preco': preco, 
            'ativo': 1
        })
    return jsonify(resultado)

@app.route("/api/gerente/produtos", methods=["GET"])
@login_required
def gerente_listar_produtos():
    return api_produtos()

@app.route("/api/gerente/produtos", methods=["POST"])
@login_required
def gerente_criar_produto():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'): 
        return jsonify({"erro": "Nome é obrigatório"}), 400
    item = {
        "nome": dados.get('nome', ''), 
        "preço": str(dados.get('preco', 0)), 
        "categoria": "produto"
    }
    item_id = baserow_post(item)
    if item_id: 
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar produto"}), 500

@app.route("/api/gerente/produtos/<int:produto_id>", methods=["PUT"])
@login_required
def gerente_atualizar_produto(produto_id):
    dados = request.get_json(force=True, silent=True) or {}
    item = {}
    if 'nome' in dados: item['nome'] = dados['nome']
    if 'preco' in dados: item['preço'] = str(dados['preco'])
    if baserow_patch(produto_id, item): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar produto"}), 500

@app.route("/api/gerente/produtos/<int:produto_id>", methods=["DELETE"])
@login_required
def gerente_deletar_produto(produto_id):
    if baserow_delete(produto_id): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar produto"}), 500

# ============ PLANOS ============
@app.route("/api/assinaturas", methods=["GET"])
def api_assinaturas():
    items = baserow_get("plano")
    resultado = []
    for item in items:
        try: 
            preco = float(item.get('preço', 0)) if item.get('preço') else 0
        except: 
            preco = 0
        resultado.append({
            'id': item.get('id'), 
            'nome': item.get('nome', ''), 
            'preco': preco, 
            'descricao': item.get('descrição', ''), 
            'icone': '⭐', 
            'destaque': 0, 
            'ativo': 1, 
            'cor': '#3ddc84'
        })
    return jsonify(resultado)

@app.route("/api/gerente/planos", methods=["GET"])
@login_required
def gerente_listar_planos():
    return api_assinaturas()

@app.route("/api/gerente/planos", methods=["POST"])
@login_required
def gerente_criar_plano():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'): 
        return jsonify({"erro": "Nome é obrigatório"}), 400
    item = {
        "nome": dados.get('nome', ''), 
        "preço": str(dados.get('preco', 0)), 
        "descrição": dados.get('descricao', ''), 
        "categoria": "plano"
    }
    item_id = baserow_post(item)
    if item_id: 
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar plano"}), 500

@app.route("/api/gerente/planos/<int:plano_id>", methods=["PUT"])
@login_required
def gerente_atualizar_plano(plano_id):
    dados = request.get_json(force=True, silent=True) or {}
    item = {}
    if 'nome' in dados: item['nome'] = dados['nome']
    if 'preco' in dados: item['preço'] = str(dados['preco'])
    if 'descricao' in dados: item['descrição'] = dados['descricao']
    if baserow_patch(plano_id, item): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar plano"}), 500

@app.route("/api/gerente/planos/<int:plano_id>", methods=["DELETE"])
@login_required
def gerente_deletar_plano(plano_id):
    if baserow_delete(plano_id): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar plano"}), 500

# ============ EQUIPE ============
@app.route("/api/profissionais", methods=["GET"])
def api_profissionais():
    items = baserow_get("equipe")
    resultado = []
    for item in items:
        resultado.append({
            'id': item.get('id'), 
            'nome': item.get('nome', ''), 
            'especialidade': item.get('especialidade', ''), 
            'ativo': 1
        })
    return jsonify(resultado)

@app.route("/api/gerente/equipe", methods=["GET"])
@login_required
def gerente_listar_equipe():
    return api_profissionais()

@app.route("/api/gerente/equipe", methods=["POST"])
@login_required
def gerente_criar_membro():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('nome'): 
        return jsonify({"erro": "Nome é obrigatório"}), 400
    item = {
        "nome": dados.get('nome', ''), 
        "especialidade": dados.get('especialidade', ''), 
        "categoria": "equipe"
    }
    item_id = baserow_post(item)
    if item_id: 
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar membro"}), 500

@app.route("/api/gerente/equipe/<int:membro_id>", methods=["PUT"])
@login_required
def gerente_atualizar_membro(membro_id):
    dados = request.get_json(force=True, silent=True) or {}
    item = {}
    if 'nome' in dados: item['nome'] = dados['nome']
    if 'especialidade' in dados: item['especialidade'] = dados['especialidade']
    if baserow_patch(membro_id, item): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar membro"}), 500

@app.route("/api/gerente/equipe/<int:membro_id>", methods=["DELETE"])
@login_required
def gerente_deletar_membro(membro_id):
    if baserow_delete(membro_id): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar membro"}), 500

# ============ ASSINANTES ============
@app.route("/api/gerente/assinantes", methods=["GET"])
@login_required
def gerente_listar_assinantes():
    items = baserow_get("assinante")
    resultado = []
    for item in items:
        resultado.append({
            'id': item.get('id'),
            'nome': item.get('nome', ''),
            'telefone': item.get('numero telefone', ''),
            'nascimento': item.get('nascimento', ''),
            'plano': item.get('plano', ''),
            'valor': float(item.get('preço', 0)) if item.get('preço') else 0,
            'status': item.get('status', 'ativo'),
            'criado_em': item.get('created_on', '')
        })
    return jsonify(resultado)

@app.route("/api/gerente/assinantes", methods=["POST"])
@login_required
def gerente_criar_assinante():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"): 
        return jsonify({"erro": "Nome é obrigatório"}), 400
    item = {
        "nome": dados.get('nome', ''),
        "numero telefone": dados.get('telefone', ''),
        "nascimento": dados.get('nascimento', ''),
        "plano": dados.get('plano', ''),
        "preço": str(dados.get('valor', 0)),
        "status": dados.get('status', 'ativo'),
        "categoria": "assinante"
    }
    item_id = baserow_post(item)
    if item_id: 
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar assinante"}), 500

@app.route("/api/gerente/assinantes/<int:assinante_id>", methods=["PUT"])
@login_required
def gerente_atualizar_assinante(assinante_id):
    dados = request.get_json(force=True, silent=True) or {}
    item = {}
    if 'nome' in dados: item['nome'] = dados['nome']
    if 'telefone' in dados: item['numero telefone'] = dados['telefone']
    if 'nascimento' in dados: item['nascimento'] = dados['nascimento']
    if 'plano' in dados: item['plano'] = dados['plano']
    if 'valor' in dados: item['preço'] = str(dados['valor'])
    if 'status' in dados: item['status'] = dados['status']
    if baserow_patch(assinante_id, item): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar assinante"}), 500

@app.route("/api/gerente/assinantes/<int:assinante_id>", methods=["DELETE"])
@login_required
def gerente_deletar_assinante(assinante_id):
    if baserow_delete(assinante_id): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar assinante"}), 500

# ============ CLIENTES ============
@app.route("/api/gerente/clientes", methods=["GET"])
@login_required
def gerente_listar_clientes():
    items = baserow_get("cliente")
    resultado = []
    for item in items:
        resultado.append({
            'id': item.get('id'),
            'nome': item.get('nome', ''),
            'telefone': item.get('numero telefone', ''),
            'cpf': item.get('cpf', ''),
            'endereco': item.get('endereço', ''),
            'email': item.get('Email', ''),
            'data_nascimento': item.get('nascimento', '')
        })
    return jsonify(resultado)

@app.route("/api/gerente/clientes", methods=["POST"])
@login_required
def gerente_criar_cliente():
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get("nome"): 
        return jsonify({"erro": "Nome é obrigatório"}), 400
    item = {
        "nome": dados.get('nome', ''),
        "numero telefone": dados.get('telefone', ''),
        "cpf": dados.get('cpf', ''),
        "endereço": dados.get('endereco', ''),
        "Email": dados.get('email', ''),
        "nascimento": dados.get('data_nascimento', ''),
        "categoria": "cliente"
    }
    item_id = baserow_post(item)
    if item_id: 
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar cliente"}), 500

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["PUT"])
@login_required
def gerente_atualizar_cliente(cliente_id):
    dados = request.get_json(force=True, silent=True) or {}
    item = {}
    if 'nome' in dados: item['nome'] = dados['nome']
    if 'telefone' in dados: item['numero telefone'] = dados['telefone']
    if 'cpf' in dados: item['cpf'] = dados['cpf']
    if 'endereco' in dados: item['endereço'] = dados['endereco']
    if 'email' in dados: item['Email'] = dados['email']
    if 'data_nascimento' in dados: item['nascimento'] = dados['data_nascimento']
    if baserow_patch(cliente_id, item): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao atualizar cliente"}), 500

@app.route("/api/gerente/clientes/<int:cliente_id>", methods=["DELETE"])
@login_required
def gerente_deletar_cliente(cliente_id):
    if baserow_delete(cliente_id): 
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar cliente"}), 500

# ============ PEDIDOS ============
@app.route("/api/gerente/pedidos", methods=["GET"])
@login_required
def gerente_listar_pedidos():
    items = baserow_get("pedido")
    status = request.args.get("status")
    if status:
        items = [p for p in items if p.get('status') == status]
    resultado = []
    for item in items:
        try:
            valor = float(item.get('preço', 0)) if item.get('preço') else 0
        except:
            valor = 0
        resultado.append({
            'id': item.get('id'),
            'tipo': item.get('tipo', 'pedido'),
            'servico_nome': item.get('servico', ''),
            'valor': valor,
            'cliente_nome': item.get('cliente', ''),
            'cliente_telefone': item.get('telefone', ''),
            'cliente_cpf': item.get('cpf', ''),
            'data_agendada': item.get('data_agendada', ''),
            'hora_agendada': item.get('hora_agendada', ''),
            'profissional': item.get('profissional', ''),
            'pagamento': item.get('pagamento', ''),
            'status': item.get('status', 'pendente'),
            'criado_em': item.get('created_on', '')
        })
    return jsonify(resultado)

@app.route("/api/pedidos", methods=["POST"])
def api_criar_pedido():
    dados = request.get_json() or {}
    item = {
        "tipo": dados.get('tipo', 'pedido'),
        "servico": dados.get('servico_nome', ''),
        "preço": str(dados.get('valor', 0)),
        "cliente": dados.get('cliente_nome', ''),
        "telefone": dados.get('cliente_telefone', ''),
        "cpf": dados.get('cliente_cpf', ''),
        "data_agendada": dados.get('data_agendada', ''),
        "hora_agendada": dados.get('hora_agendada', ''),
        "profissional": dados.get('profissional', ''),
        "pagamento": dados.get('pagamento', ''),
        "status": "pendente",
        "categoria": "pedido"
    }
    item_id = baserow_post(item)
    if item_id:
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar pedido"}), 500

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["PUT"])
@login_required
def gerente_atualizar_pedido(pedido_id):
    dados = request.get_json(force=True, silent=True) or {}
    novo_status = dados.get("status")
    if not novo_status:
        return jsonify({"erro": "Status não informado"}), 400
    if novo_status not in ("pendente", "confirmado", "concluido", "cancelado"):
        return jsonify({"erro": "Status inválido"}), 400
    
    # Busca o pedido atual
    pedidos = baserow_get("pedido")
    pedido_atual = None
    for p in pedidos:
        if p.get('id') == pedido_id:
            pedido_atual = p
            break
    
    if not pedido_atual:
        return jsonify({"erro": "Pedido não encontrado"}), 404
    
    # Se o pedido está sendo CONCLUÍDO
    if novo_status == "concluido" and pedido_atual.get('status') != "concluido":
        try:
            valor = float(pedido_atual.get('preço', 0))
            print(f"💰 Pedido #{pedido_id} sendo concluído. Valor: R$ {valor:.2f}")
            
            if valor > 0:
                # CRIA DIRETAMENTE NO BASEROW
                item_caixa = {
                    "tipo": "entrada",
                    "descrição": f"Pedido #{pedido_id} - {pedido_atual.get('cliente', '')} - {pedido_atual.get('servico', '')}",
                    "pagamento": pedido_atual.get('pagamento', 'manual'),
                    "preço": str(valor),
                    "categoria": "caixa"
                }
                
                # Tenta criar no Baserow
                resultado = baserow_post(item_caixa)
                if resultado:
                    print(f"✅ Pedido #{pedido_id} ADICIONADO ao caixa: R$ {valor:.2f}")
                else:
                    print(f"❌ ERRO ao adicionar pedido #{pedido_id} ao caixa")
                    # Tenta novamente com outro formato
                    item_caixa2 = {
                        "nome": f"Pedido #{pedido_id}",
                        "preço": str(valor),
                        "categoria": "caixa",
                        "descrição": f"Pedido #{pedido_id} - {pedido_atual.get('cliente', '')}",
                        "tipo": "entrada"
                    }
                    resultado2 = baserow_post(item_caixa2)
                    if resultado2:
                        print(f"✅ Pedido #{pedido_id} ADICIONADO (2ª tentativa): R$ {valor:.2f}")
        except Exception as e:
            print(f"❌ Erro ao processar conclusão: {e}")
    
    # Atualiza o status do pedido
    if not baserow_patch(pedido_id, {"status": novo_status}):
        return jsonify({"erro": "Erro ao atualizar pedido"}), 500
    
    return jsonify({"status": "ok"})

@app.route("/api/gerente/pedidos/<int:pedido_id>", methods=["DELETE"])
@login_required
def gerente_deletar_pedido(pedido_id):
    if baserow_delete(pedido_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar pedido"}), 500

# ============ CAIXA ============
@app.route("/api/gerente/caixa", methods=["GET"])
@login_required
def gerente_listar_caixa():
    """Lista todas as movimentações de caixa"""
    items = baserow_get("caixa")
    resultado = []
    for item in items:
        try:
            valor = float(item.get('preço', 0)) if item.get('preço') else 0
        except:
            valor = 0
        resultado.append({
            'id': item.get('id'),
            'tipo': item.get('tipo', 'entrada'),
            'descricao': item.get('descrição', ''),
            'pagamento': item.get('pagamento', ''),
            'valor': valor,
            'criado_em': item.get('created_on', '')
        })
    return jsonify(resultado)

@app.route("/api/gerente/caixa", methods=["POST"])
@login_required
def gerente_criar_caixa():
    """Cria uma nova movimentação de caixa"""
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('descricao'):
        return jsonify({"erro": "Descrição é obrigatória"}), 400
    
    valor = float(dados.get('valor', 0))
    if valor <= 0:
        return jsonify({"erro": "Valor deve ser maior que zero"}), 400
    
    if dados.get('tipo') == 'saida':
        movimentacoes = baserow_get("caixa")
        entradas = sum(float(m.get('preço', 0)) for m in movimentacoes if m.get('tipo') == 'entrada')
        saidas = sum(float(m.get('preço', 0)) for m in movimentacoes if m.get('tipo') == 'saida')
        saldo = entradas - saidas
        if valor > saldo:
            return jsonify({"erro": f"Saldo insuficiente. Saldo atual: R$ {saldo:.2f}"}), 400
    
    item = {
        "tipo": dados.get('tipo', 'entrada'),
        "descrição": dados.get('descricao', ''),
        "pagamento": dados.get('pagamento', 'manual'),
        "preço": str(valor),
        "categoria": "caixa"
    }
    item_id = baserow_post(item)
    if item_id:
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar movimentação"}), 500

@app.route("/api/gerente/caixa/<int:caixa_id>", methods=["DELETE"])
@login_required
def gerente_deletar_caixa(caixa_id):
    """Deleta uma movimentação de caixa"""
    if baserow_delete(caixa_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar movimentação"}), 500

@app.route("/api/gerente/caixa/resetar", methods=["POST"])
@login_required
def gerente_resetar_caixa():
    """Reseta o caixa do dia - salva o saldo atual como histórico e zera"""
    try:
        movimentacoes = baserow_get("caixa")
        
        entradas = sum(float(m.get('preço', 0)) for m in movimentacoes if m.get('tipo') == 'entrada')
        saidas = sum(float(m.get('preço', 0)) for m in movimentacoes if m.get('tipo') == 'saida')
        saldo_atual = entradas - saidas
        
        hoje = date.today().isoformat()
        item = {
            "tipo": "fechamento",
            "descrição": f"Fechamento do dia {hoje} - Saldo: R$ {saldo_atual:.2f}",
            "pagamento": "historico",
            "preço": str(saldo_atual),
            "categoria": "caixa_historico"
        }
        baserow_post(item)
        
        for m in movimentacoes:
            if m.get('categoria') == 'caixa':
                baserow_delete(m.get('id'))
        
        return jsonify({
            "status": "ok", 
            "mensagem": f"Caixa resetado! Saldo anterior: R$ {saldo_atual:.2f} salvo no histórico."
        })
        
    except Exception as e:
        print(f"❌ Erro ao resetar caixa: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/caixa/resumo", methods=["GET"])
@login_required
def gerente_resumo_caixa():
    """Retorna resumo do caixa"""
    movimentacoes = baserow_get("caixa")
    entradas = sum(float(m.get('preço', 0)) for m in movimentacoes if m.get('tipo') == 'entrada')
    saidas = sum(float(m.get('preço', 0)) for m in movimentacoes if m.get('tipo') == 'saida')
    saldo = entradas - saidas
    
    return jsonify({
        "entradas": entradas,
        "saidas": saidas,
        "saldo": saldo,
        "total_movimentacoes": len(movimentacoes)
    })

@app.route("/api/gerente/caixa/diagnostico", methods=["GET"])
@login_required
def gerente_diagnostico_caixa():
    """Rota de diagnóstico para verificar o estado do caixa"""
    try:
        # Busca todos os pedidos
        pedidos = baserow_get("pedido")
        pedidos_concluidos = [p for p in pedidos if p.get('status') == 'concluido']
        
        # Busca todas as movimentações de caixa
        caixa = baserow_get("caixa")
        entradas = [c for c in caixa if c.get('tipo') == 'entrada']
        
        # Calcula totais
        total_pedidos = sum(float(p.get('preço', 0)) for p in pedidos_concluidos)
        total_caixa = sum(float(c.get('preço', 0)) for c in entradas)
        
        # Verifica quais pedidos estão no caixa
        ids_no_caixa = []
        for c in entradas:
            desc = c.get('descrição', '')
            if 'Pedido #' in desc:
                try:
                    match = re.search(r'Pedido #(\d+)', desc)
                    if match:
                        ids_no_caixa.append(int(match.group(1)))
                except:
                    pass
        
        # Lista pedidos concluídos que NÃO estão no caixa
        faltando = []
        for p in pedidos_concluidos:
            if p.get('id') not in ids_no_caixa:
                faltando.append({
                    'id': p.get('id'),
                    'cliente': p.get('cliente', ''),
                    'servico': p.get('servico', ''),
                    'valor': float(p.get('preço', 0))
                })
        
        return jsonify({
            "total_pedidos_concluidos": len(pedidos_concluidos),
            "total_valor_pedidos": total_pedidos,
            "total_entradas_caixa": len(entradas),
            "total_valor_caixa": total_caixa,
            "ids_no_caixa": ids_no_caixa,
            "pedidos_faltando": faltando,
            "exemplos_caixa": entradas[:3],
            "exemplos_pedidos": pedidos_concluidos[:3]
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/caixa/sincronizar_pedidos", methods=["POST"])
@login_required
def gerente_sincronizar_pedidos_caixa():
    """Sincroniza todos os pedidos concluídos com o caixa"""
    try:
        pedidos = baserow_get("pedido")
        caixa_items = baserow_get("caixa")
        
        ids_no_caixa = set()
        for c in caixa_items:
            if c.get('tipo') == 'entrada' and c.get('descrição', '').startswith('Pedido #'):
                try:
                    desc = c.get('descrição', '')
                    if 'Pedido #' in desc:
                        parte = desc.split('Pedido #')[1]
                        id_str = parte.split(' ')[0] if ' ' in parte else parte
                        ids_no_caixa.add(int(id_str))
                except:
                    pass
        
        adicionados = 0
        for p in pedidos:
            if p.get('status') == 'concluido':
                pedido_id = p.get('id')
                if pedido_id not in ids_no_caixa:
                    try:
                        valor = float(p.get('preço', 0))
                        if valor > 0:
                            item_caixa = {
                                "tipo": "entrada",
                                "descrição": f"Pedido #{pedido_id} - {p.get('cliente', '')} - {p.get('servico', '')}",
                                "pagamento": p.get('pagamento', 'manual'),
                                "preço": str(valor),
                                "categoria": "caixa"
                            }
                            resultado = baserow_post(item_caixa)
                            if resultado:
                                adicionados += 1
                    except:
                        pass
        
        return jsonify({
            "status": "ok",
            "mensagem": f"{adicionados} pedidos sincronizados com o caixa"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/gerente/caixa/forcar_sincronizacao", methods=["POST"])
@login_required
def gerente_forcar_sincronizacao():
    """Força a sincronização de TODOS os pedidos concluídos com o caixa"""
    try:
        pedidos = baserow_get("pedido")
        caixa_items = baserow_get("caixa")
        
        # Remove todas as entradas de pedidos do caixa (apenas as que começam com "Pedido #")
        removidos = 0
        for c in caixa_items:
            if c.get('tipo') == 'entrada' and c.get('descrição', '').startswith('Pedido #'):
                if baserow_delete(c.get('id')):
                    removidos += 1
        
        # Adiciona todos os pedidos concluídos novamente
        adicionados = 0
        for p in pedidos:
            if p.get('status') == 'concluido':
                try:
                    valor = float(p.get('preço', 0))
                    if valor > 0:
                        item_caixa = {
                            "tipo": "entrada",
                            "descrição": f"Pedido #{p.get('id')} - {p.get('cliente', '')} - {p.get('servico', '')}",
                            "pagamento": p.get('pagamento', 'manual'),
                            "preço": str(valor),
                            "categoria": "caixa"
                        }
                        resultado = baserow_post(item_caixa)
                        if resultado:
                            adicionados += 1
                            print(f"✅ Pedido #{p.get('id')} adicionado: R$ {valor:.2f}")
                except Exception as e:
                    print(f"❌ Erro ao adicionar pedido #{p.get('id')}: {e}")
        
        # Recalcula o saldo
        caixa_atualizado = baserow_get("caixa")
        entradas = sum(float(c.get('preço', 0)) for c in caixa_atualizado if c.get('tipo') == 'entrada')
        saidas = sum(float(c.get('preço', 0)) for c in caixa_atualizado if c.get('tipo') == 'saida')
        saldo = entradas - saidas
        
        return jsonify({
            "status": "ok",
            "mensagem": f"Removidos: {removidos}, Adicionados: {adicionados}",
            "saldo_atual": saldo,
            "entradas": entradas,
            "saidas": saidas
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ COMANDAS ============
@app.route("/api/gerente/comandas", methods=["GET"])
@login_required
def gerente_listar_comandas():
    """Lista todas as comandas"""
    items = baserow_get("comanda")
    resultado = []
    for item in items:
        try:
            valor = float(item.get('preço', 0)) if item.get('preço') else 0
        except:
            valor = 0
        resultado.append({
            'id': item.get('id'),
            'ticket': item.get('ticket', f"#CM{item.get('id', '')}"),
            'cliente_nome': item.get('cliente', ''),
            'cliente_telefone': item.get('numero telefone', ''),
            'profissional': item.get('profissional', ''),
            'servicos': item.get('servico', ''),
            'valor_total': valor,
            'pagamento': item.get('pagamento', 'pendente'),
            'status': item.get('status', 'aberta'),
            'criado_em': item.get('created_on', '')
        })
    return jsonify(resultado)

@app.route("/api/gerente/comandas", methods=["POST"])
@login_required
def gerente_criar_comanda():
    """Cria uma nova comanda"""
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('cliente_nome'):
        return jsonify({"erro": "Nome do cliente é obrigatório"}), 400
    
    comandas = baserow_get("comanda")
    num_ticket = len(comandas) + 1
    
    item = {
        "ticket": f"#CM{num_ticket:04d}",
        "cliente": dados.get('cliente_nome', ''),
        "numero telefone": dados.get('cliente_telefone', ''),
        "profissional": dados.get('profissional', ''),
        "servico": dados.get('servicos', ''),
        "preço": str(dados.get('valor_total', 0)),
        "pagamento": dados.get('pagamento', 'pendente'),
        "status": dados.get('status', 'aberta'),
        "categoria": "comanda"
    }
    item_id = baserow_post(item)
    if item_id:
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar comanda"}), 500

@app.route("/api/gerente/comandas/<int:comanda_id>", methods=["DELETE"])
@login_required
def gerente_deletar_comanda(comanda_id):
    """Deleta uma comanda"""
    if baserow_delete(comanda_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar comanda"}), 500

# ============ REPASSES ============
@app.route("/api/gerente/repasses", methods=["GET"])
@login_required
def gerente_listar_repasses():
    """Lista todos os repasses"""
    items = baserow_get("repasse")
    resultado = []
    for item in items:
        try:
            valor_servico = float(item.get('preço', 0)) if item.get('preço') else 0
            comissao = valor_servico * (float(item.get('comissao', 50)) / 100)
        except:
            valor_servico = 0
            comissao = 0
        
        resultado.append({
            'id': item.get('id'),
            'profissional': item.get('profissional', ''),
            'servico_nome': item.get('servico', ''),
            'valor_servico': valor_servico,
            'comissao': comissao,
            'porcentagem': float(item.get('comissao', 50)),
            'status': item.get('status', 'pendente'),
            'criado_em': item.get('created_on', '')
        })
    return jsonify(resultado)

@app.route("/api/gerente/repasses", methods=["POST"])
@login_required
def gerente_criar_repasse():
    """Cria um novo repasse"""
    dados = request.get_json(force=True, silent=True) or {}
    if not dados.get('profissional') or not dados.get('servico_nome'):
        return jsonify({"erro": "Profissional e serviço são obrigatórios"}), 400
    
    item = {
        "profissional": dados.get('profissional', ''),
        "servico": dados.get('servico_nome', ''),
        "preço": str(dados.get('valor_servico', 0)),
        "comissao": str(dados.get('porcentagem', 50)),
        "status": dados.get('status', 'pendente'),
        "categoria": "repasse"
    }
    item_id = baserow_post(item)
    if item_id:
        return jsonify({"status": "ok", "id": item_id})
    return jsonify({"erro": "Erro ao criar repasse"}), 500

@app.route("/api/gerente/repasses/<int:repasse_id>", methods=["DELETE"])
@login_required
def gerente_deletar_repasse(repasse_id):
    """Deleta um repasse"""
    if baserow_delete(repasse_id):
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao deletar repasse"}), 500

@app.route("/api/gerente/repasses/resumo", methods=["GET"])
@login_required
def gerente_resumo_repasses():
    """Retorna resumo dos repasses"""
    repasses = baserow_get("repasse")
    total_pendente = 0
    total_pago = 0
    
    for r in repasses:
        try:
            valor = float(r.get('preço', 0))
            comissao = valor * (float(r.get('comissao', 50)) / 100)
            if r.get('status') == 'pendente':
                total_pendente += comissao
            else:
                total_pago += comissao
        except:
            pass
    
    return jsonify({
        "total_pendente": total_pendente,
        "total_pago": total_pago
    })

# ============ RELATÓRIO PDF ============
@app.route("/api/gerente/relatorio/pdf", methods=["GET"])
@login_required
def gerente_relatorio_pdf():
    """Gera um relatório PDF simples (HTML para impressão)"""
    pedidos = baserow_get("pedido")
    comandas = baserow_get("comanda")
    repasses = baserow_get("repasse")
    caixa = baserow_get("caixa")
    
    total_entradas = sum(float(c.get('preço', 0)) for c in caixa if c.get('tipo') == 'entrada')
    total_saidas = sum(float(c.get('preço', 0)) for c in caixa if c.get('tipo') == 'saida')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório - Barbearia Studio Leblon</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; }}
            h1 {{ color: #333; border-bottom: 2px solid #3ddc84; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background: #f0f0f0; text-align: left; padding: 8px; border: 1px solid #ddd; }}
            td {{ padding: 8px; border: 1px solid #ddd; }}
            .total {{ font-weight: bold; font-size: 1.2em; margin-top: 20px; }}
            .green {{ color: #2ecc71; }}
            .red {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <h1>📊 Relatório - Barbearia Studio Leblon</h1>
        <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <h2>📋 Pedidos ({len(pedidos)})</h2>
        <table>
            <tr><th>Cliente</th><th>Serviço</th><th>Profissional</th><th>Valor</th><th>Status</th></tr>
            {''.join(f"<tr><td>{p.get('cliente', '-')}</td><td>{p.get('servico', '-')}</td><td>{p.get('profissional', '-')}</td><td>R$ {float(p.get('preço', 0)):.2f}</td><td>{p.get('status', '')}</td></tr>" for p in pedidos[:20])}
            {'' if len(pedidos) <= 20 else f"<tr><td colspan='5'>... e mais {len(pedidos)-20} pedidos</td></tr>"}
        </table>
        
        <h2>💰 Resumo Financeiro</h2>
        <div class="total">
            <p>Total Entradas: <span class="green">R$ {total_entradas:.2f}</span></p>
            <p>Total Saídas: <span class="red">R$ {total_saidas:.2f}</span></p>
            <p>Saldo: <span style="color: {'#2ecc71' if total_entradas > total_saidas else '#e74c3c'}">R$ {(total_entradas - total_saidas):.2f}</span></p>
        </div>
        
        <p><em>Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M')}</em></p>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html')

# ============ VERIFICAR HORÁRIO ============
@app.route("/api/verificar_horario", methods=["POST"])
def verificar_horario():
    try:
        dados = request.get_json() or {}
        data = dados.get("data")
        hora = dados.get("hora")
        profissional = dados.get("profissional", "")
        
        if not data or not hora:
            return jsonify({"erro": "Data e hora são obrigatórias"}), 400
        
        pedidos = baserow_get("pedido")
        ocupado = False
        
        for p in pedidos:
            if p.get('data_agendada') == data and p.get('hora_agendada') == hora:
                if p.get('status') in ['pendente', 'confirmado']:
                    if profissional:
                        if p.get('profissional') == profissional:
                            ocupado = True
                            break
                    else:
                        ocupado = True
                        break
        
        return jsonify({"disponivel": not ocupado, "mensagem": "Horário indisponível" if ocupado else "Horário disponível"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============ IMAGENS ============
@app.route("/api/imagens", methods=["GET"])
def api_imagens():
    return jsonify([])

# ============ HORÁRIOS ============
@app.route("/api/horarios", methods=["GET"])
def api_horarios_get():
    return jsonify([{"dia_semana": i, "abertura": "", "fechamento": "", "ativo": 0} for i in range(7)])

@app.route("/api/horarios", methods=["PUT"])
@login_required
def api_horarios_put():
    return jsonify({"status": "ok"})

# ============ PERFIL ============
@app.route("/api/gerente/alterar_nome", methods=["POST"])
@login_required
def gerente_alterar_nome():
    dados = request.get_json() or {}
    novo_nome = dados.get("novo_nome", "").strip()
    if not novo_nome:
        return jsonify({"erro": "Nome inválido"}), 400
    
    if baserow_patch(session["gerente_id"], {"nome": novo_nome}):
        session["gerente_nome"] = novo_nome
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao alterar nome"}), 500

@app.route("/api/gerente/alterar_login", methods=["POST"])
@login_required
def gerente_alterar_login():
    dados = request.get_json() or {}
    senha_atual = dados.get("senha_atual", "")
    novo_usuario = dados.get("novo_usuario", "").strip()
    nova_senha = dados.get("nova_senha", "")
    
    if not senha_atual:
        return jsonify({"erro": "Senha atual é obrigatória"}), 400
    
    if not novo_usuario and not nova_senha:
        return jsonify({"erro": "Digite pelo menos um campo"}), 400
    
    gerentes = baserow_get("gerente")
    gerente_atual = None
    for g in gerentes:
        if g.get('id') == session["gerente_id"]:
            gerente_atual = g
            break
    
    if not gerente_atual:
        return jsonify({"erro": "Gerente não encontrado"}), 404
    
    if gerente_atual.get('senha') != senha_atual:
        return jsonify({"erro": "Senha atual incorreta"}), 401
    
    item = {}
    if novo_usuario:
        item['nome'] = novo_usuario
    if nova_senha:
        item['senha'] = nova_senha
    
    if baserow_patch(session["gerente_id"], item):
        if novo_usuario:
            session["gerente_nome"] = novo_usuario
        return jsonify({"status": "ok"})
    return jsonify({"erro": "Erro ao alterar login"}), 500

# ============ INICIALIZAÇÃO ============
if __name__ == "__main__":
    print("="*60)
    print("  🚀 Barbearia Studio Leblon")
    print("  📡 100% Baserow")
    print("="*60)
    print("📌 Token: 4tKiir8cwC5MvMu0Cgj9X5ewrzQn8jNR")
    print("📌 Tabela: 1094351 (Customers)")
    print("="*60)
    print("")
    print("🔧 Quando você clicar em CONCLUIR no pedido:")
    print("  - O valor será adicionado automaticamente ao CAIXA")
    print("  - O saldo aparecerá no dashboard e na seção Caixa")
    print("")
    print("🔧 Rotas de diagnóstico:")
    print("  GET /api/gerente/caixa/diagnostico - Verificar estado do caixa")
    print("  POST /api/gerente/caixa/sincronizar_pedidos - Sincronizar pedidos faltantes")
    print("  POST /api/gerente/caixa/forcar_sincronizacao - Forçar sincronização completa")
    print("")
    app.run(debug=True, host="0.0.0.0", port=5000)