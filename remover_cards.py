ARQUIVO = "gerente.html"

with open(ARQUIVO, "r", encoding="utf-8") as f:
    conteudo = f.read()

cards_remover = [
    '<div class="stat-card"><div class="label">💰 Saldo Inicial do Dia</div><div class="valor gold" id="statSaldoInicial">R$ 0,00</div></div>',
    '<div class="stat-card"><div class="label">📈 Entradas Hoje</div><div class="valor green" id="statEntradasHoje">R$ 0,00</div></div>',
    '<div class="stat-card"><div class="label">💰 Faturamento Total</div><div class="valor green" id="statFaturamento">R$ 0,00</div></div>',
    '<div class="stat-card"><div class="label">👥 Clientes Atendidos</div><div class="valor" id="statClientes">0</div></div>',
    '<div class="stat-card"><div class="label">📋 Comandas Abertas</div><div class="valor blue" id="statComandas">0</div></div>',
    '<div class="stat-card"><div class="label">💰 Repasses Pendentes</div><div class="valor red" id="statRepasses">0</div></div>',
]

removidos = 0
for card in cards_remover:
    qtd = conteudo.count(card)
    if qtd == 1:
        conteudo = conteudo.replace(card, '')
        removidos += 1
        print(f"✅ Removido: {card[:60]}...")
    elif qtd == 0:
        print(f"❌ Não encontrado: {card[:60]}...")
    else:
        print(f"⚠️ Encontrado {qtd}x, pulei por segurança: {card[:60]}...")

with open(ARQUIVO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"\n🎉 {removidos}/6 cards removidos do HTML.")
print("   Recarregue a página do painel (F5) para ver a mudança.")
