ARQUIVO = "gerente.html"

with open(ARQUIVO, "r", encoding="utf-8") as f:
    conteudo = f.read()

# 1) Remove o card "Saldo em Caixa" do HTML
old_html = '<div class="stat-card"><div class="label">💵 Saldo em Caixa</div><div class="valor blue" id="statSaldo">R$ 0,00</div></div>'
qtd_html = conteudo.count(old_html)
if qtd_html == 1:
    conteudo = conteudo.replace(old_html, '')
    print("✅ Card 'Saldo em Caixa' removido do HTML")
elif qtd_html == 0:
    print("❌ Card 'Saldo em Caixa' não encontrado no HTML (talvez já removido)")
else:
    print(f"⚠️ Encontrado {qtd_html}x no HTML, pulei por segurança")

# 2) Reescreve a função carregarInicio para só usar o que ainda existe (statPendentes)
old_js = '''async function carregarInicio(){
  try{
    const stats = await api('/api/gerente/dashboard');
    document.getElementById('statFaturamento').textContent = formatarPreco(stats.faturamento_total);
    document.getElementById('statSaldo').textContent = formatarPreco(stats.saldo);
    document.getElementById('statPendentes').textContent = stats.pedidos_pendentes;
    document.getElementById('statHoje').textContent = stats.agendamentos_hoje;
    document.getElementById('statClientes').textContent = stats.total_clientes;
    document.getElementById('statComandas').textContent = stats.comandas_abertas || 0;
    document.getElementById('statRepasses').textContent = stats.repasses_pendentes || 0;
    const pedidos = await api('/api/gerente/pedidos');
    const ultimos = pedidos.slice(0, 8);
    document.getElementById('tabelaInicioPedidos').innerHTML = ultimos.length ? ultimos.map(p => `<tr><td>${p.cliente_nome}</td><td>${p.servico_nome}</td><td>${p.profissional && p.profissional !== '' ? '👤 ' + p.profissional : '-'}</td><td>${formatarPreco(p.valor)}</td><td><span class="status-pill status-${p.status}">${p.status}</span></td><td>${formatarData(p.criado_em)}</td></tr>`).join('') : '<tr><td colspan="6" class="empty-msg">Nenhum pedido ainda.</td></tr>';
  } catch(e){ showToast('Erro: ' + e.message); }
}'''

new_js = '''async function carregarInicio(){
  try{
    const stats = await api('/api/gerente/dashboard');
    const elPendentes = document.getElementById('statPendentes');
    if (elPendentes) elPendentes.textContent = stats.pedidos_pendentes;
    const pedidos = await api('/api/gerente/pedidos');
    const ultimos = pedidos.slice(0, 8);
    document.getElementById('tabelaInicioPedidos').innerHTML = ultimos.length ? ultimos.map(p => `<tr><td>${p.cliente_nome}</td><td>${p.servico_nome}</td><td>${p.profissional && p.profissional !== '' ? '👤 ' + p.profissional : '-'}</td><td>${formatarPreco(p.valor)}</td><td><span class="status-pill status-${p.status}">${p.status}</span></td><td>${formatarData(p.criado_em)}</td></tr>`).join('') : '<tr><td colspan="6" class="empty-msg">Nenhum pedido ainda.</td></tr>';
  } catch(e){ showToast('Erro: ' + e.message); }
}'''

qtd_js = conteudo.count(old_js)
if qtd_js == 1:
    conteudo = conteudo.replace(old_js, new_js)
    print("✅ Função carregarInicio() corrigida")
elif qtd_js == 0:
    print("❌ Função carregarInicio() não bateu exatamente (pode já ter sido alterada)")
else:
    print(f"⚠️ Encontrado {qtd_js}x, pulei por segurança")

with open(ARQUIVO, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("\n🎉 Pronto! Recarregue a página (F5).")
