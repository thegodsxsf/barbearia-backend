ARQUIVO = "servidor.py"

with open(ARQUIVO, "r", encoding="utf-8") as f:
    conteudo = f.read()

old = '''def baserow_get(categoria=None):
    """Busca registros da tabela Customers. Se categoria for fornecida, filtra."""
    try:
        url = BASEROW_URL
        if categoria:
            url += f"&filter__categoria__equal={categoria}"
        response = requests.get(url, headers={"Authorization": f"Token {BASEROW_TOKEN}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        print(f"❌ Erro Baserow GET: Status {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Erro Baserow GET: {e}")
        return []'''

new = '''def baserow_get(categoria=None):
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
        return []'''

qtd = conteudo.count(old)
if qtd == 0:
    print("❌ Não encontrei a função baserow_get exatamente como esperado.")
elif qtd > 1:
    print(f"⚠️ Encontrado {qtd}x — não é único, não apliquei por segurança.")
else:
    conteudo = conteudo.replace(old, new)
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("✅ Função baserow_get corrigida com sucesso em servidor.py!")
    print("   Agora reinicie o servidor Flask (Ctrl+C e rode 'python3 servidor.py' de novo).")
