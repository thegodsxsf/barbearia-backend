import requests
import getpass

BASE = "http://127.0.0.1:5000"
s = requests.Session()

usuario = input("Usuário do gerente: ")
senha = getpass.getpass("Senha do gerente: ")

r = s.post(f"{BASE}/api/gerente/login", json={"usuario": usuario, "senha": senha})
if r.status_code != 200:
    print("❌ Login falhou:", r.json())
    exit()

print("✅ Login ok\n")

print("⏳ Forçando sincronização caixa <-> pedidos concluídos...")
r = s.post(f"{BASE}/api/gerente/caixa/forcar_sincronizacao")
print(r.json())

print("\n📊 Dashboard atualizado:")
print(s.get(f"{BASE}/api/gerente/dashboard").json())
