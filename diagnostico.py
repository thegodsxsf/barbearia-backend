import requests

BASE = "http://127.0.0.1:5000"
s = requests.Session()

usuario = input("Usuário do gerente: ")
senha = input("Senha do gerente: ")

r = s.post(f"{BASE}/api/gerente/login", json={"usuario": usuario, "senha": senha})
print("\nLogin:", r.status_code, r.json())

print("\n--- DASHBOARD ---")
print(s.get(f"{BASE}/api/gerente/dashboard").json())

print("\n--- CAIXA (lista completa) ---")
print(s.get(f"{BASE}/api/gerente/caixa").json())

print("\n--- DIAGNÓSTICO CAIXA (pedidos faltando) ---")
print(s.get(f"{BASE}/api/gerente/caixa/diagnostico").json())
