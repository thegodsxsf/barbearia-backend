ARQUIVO = "gerente.html"

with open(ARQUIVO, "r", encoding="utf-8") as f:
    conteudo = f.read()

old = '''    showToast(`✅ Status alterado para: ${statusMap[status] || status}`);
    carregarPedidos();
    carregarInicio();
  } catch(e){ 
    showToast('❌ Erro: ' + e.message);
    console.error('Erro ao atualizar status:', e);
  }
}'''

new = '''    showToast(`✅ Status alterado para: ${statusMap[status] || status}`);
    carregarPedidos();
    carregarInicio();
    carregarCaixa();
  } catch(e){ 
    showToast('❌ Erro: ' + e.message);
    console.error('Erro ao atualizar status:', e);
  }
}'''

qtd = conteudo.count(old)
if qtd == 0:
    print("❌ Trecho não encontrado — o arquivo já pode ter sido alterado antes. Verifique manualmente.")
elif qtd > 1:
    print(f"⚠️ Encontrado {qtd}x, não é único — não apliquei por segurança.")
else:
    conteudo = conteudo.replace(old, new)
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("✅ Pronto! Agora o saldo do Caixa atualiza assim que um pedido é concluído.")
