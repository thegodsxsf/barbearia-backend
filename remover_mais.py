ARQUIVO = "gerente.html"

with open(ARQUIVO, "r", encoding="utf-8") as f:
    conteudo = f.read()

remocoes = [
    ("Botão Resetar Faturamento",
     '<button class="btn-refresh" onclick="resetarFaturamento()" style="background: #e74c3c; color:#fff; border-color:#e74c3c; font-weight:700;">💳 Resetar Faturamento</button>'),
    ("Card Agendamentos Hoje",
     '<div class="stat-card"><div class="label">📅 Agendamentos Hoje</div><div class="valor" id="statHoje">0</div></div>'),
]

removidos = 0
for nome, trecho in remocoes:
    qtd = conteudo.count(trecho)
    if qtd == 1:
        conteudo = conteudo.replace(trecho, '')
        removidos += 1
        print(f"✅ Removido: {nome}")
    elif qtd == 0:
        print(f"❌ Não encontrado: {nome}")
    else:
        print(f"⚠️ Encontrado {qtd}x, pulei por segurança: {nome}")

with open(ARQUIVO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"\n🎉 {removidos}/2 removidos.")
print("   Recarregue a página (F5) para ver a mudança.")
