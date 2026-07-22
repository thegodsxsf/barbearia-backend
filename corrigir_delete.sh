#!/bin/bash

# Corrigir a função excluirProduto no gerente.html
sed -i '/async function excluirProduto(id) {/,/}/c\
async function excluirProduto(id) {\
  if (!confirm("Tem certeza que deseja excluir este produto do Baserow?")) return;\
  try {\
    const response = await fetch(`/api/gerente/produtos/${id}`, { method: "DELETE", headers: {"Content-Type": "application/json"} });\
    if (!response.ok) { const erro = await response.json(); throw new Error(erro.erro || "Erro ao excluir"); }\
    showToast("✅ Produto excluído do Baserow!");\
    carregarProdutos();\
  } catch(e) { showToast("❌ Erro: " + e.message); console.error("Erro ao excluir:", e); }\
}' gerente.html

# Corrigir a função excluirItemCatalogo para produtos
sed -i '/async function excluirItemCatalogo(tabela, id) {/,/}/c\
async function excluirItemCatalogo(tabela, id) {\
  if (tabela === "produtos") {\
    await excluirProduto(id);\
    return;\
  }\
  if (tabela === "equipe") {\
    await excluirMembroEquipe(id);\
    return;\
  }\
  if (tabela === "planos") {\
    await excluirPlano(id);\
    return;\
  }\
  if (!confirm(`Tem certeza que deseja excluir este item?`)) return;\
  try {\
    const response = await fetch(`/api/${tabela}/${id}`, { method: "DELETE", headers: {"Content-Type": "application/json"} });\
    if (!response.ok) { const erro = await response.json(); throw new Error(erro.erro || "Erro ao excluir"); }\
    showToast("✅ Item excluído!");\
    if (tabela === "servicos") carregarServicos();\
  } catch(e) { showToast("❌ Erro: " + e.message); console.error("Erro ao excluir:", e); }\
}' gerente.html

echo "✅ Correção aplicada!"
