#!/bin/bash

# Adicionar as funções de produtos no JavaScript do gerente.html
sed -i '/\/\/ ============ EQUIPE (BASEROW) ============/a \
\
// ============ PRODUTOS (BASEROW) ============\
async function carregarProdutos() {\
  try {\
    const response = await fetch("/api/gerente/produtos");\
    if (!response.ok) throw new Error("Erro ao buscar produtos");\
    const lista = await response.json();\
    const el = document.getElementById("tabelaProdutos");\
    if (!el) return;\
    console.log("🧴 Produtos (Baserow):", lista.length, "registros");\
    el.innerHTML = lista.length ? lista.map(p => `<tr><td>${p.nome}</td><td>${formatarPreco(p.preco)}</td><td>${p.ativo ? "✅" : "❌"}</td><td><div class="acoes"><button class="btn-mini gray" onclick="abrirModalProduto(${JSON.stringify(p).replace(/"/g, "&quot;")})">✏️</button><button class="btn-mini red" onclick="excluirProduto(${p.id})">🗑️</button></div></td></tr>`).join("") : "<tr><td colspan=\"4\" class=\"empty-msg\">Nenhum produto cadastrado no Baserow.</td></tr>";\
  } catch(e) { console.error("Erro ao carregar produtos:", e); showToast("Erro ao carregar produtos: " + e.message); }\
}\
\
function abrirModalProduto(item=null) {\
  itemEditando = {tabela: "produtos", id: item ? item.id : null};\
  document.getElementById("modalItemTitulo").textContent = item ? "✏️ Editar Produto" : "📋 Novo Produto";\
  document.getElementById("modalItemCampos").innerHTML = `\
    <div class="form-group"><label>Nome <span class="required">*</span></label><input type="text" id="campo_nome" value="${item ? item.nome || "" : ""}"></div>\
    <div class="form-group"><label>Preço (R$) <span class="required">*</span></label><input type="number" step="0.01" id="campo_preco" value="${item ? item.preco || 0 : 0}"></div>\
    <div class="form-group"><label>Ativo</label><select id="campo_ativo"><option value="1" ${item && item.ativo ? "selected" : ""}>Sim</option><option value="0" ${item && !item.ativo ? "selected" : ""}>Não</option></select></div>\
  `;\
  document.getElementById("modalItem").classList.add("active");\
}\
\
async function salvarProduto() {\
  const {id} = itemEditando;\
  const dados = {\
    nome: document.getElementById("campo_nome").value.trim(),\
    preco: parseFloat(document.getElementById("campo_preco").value) || 0,\
    ativo: parseInt(document.getElementById("campo_ativo").value) || 1\
  };\
  if (!dados.nome) { showToast("⚠️ Nome é obrigatório."); return; }\
  try {\
    let url = "/api/gerente/produtos";\
    let method = "POST";\
    if (id) { url = `/api/gerente/produtos/${id}`; method = "PUT"; }\
    const response = await fetch(url, { method, headers: {"Content-Type": "application/json"}, body: JSON.stringify(dados) });\
    if (!response.ok) { const erro = await response.json(); throw new Error(erro.erro || "Erro ao salvar"); }\
    showToast("✅ Produto salvo no Baserow!");\
    fecharModalItem();\
    carregarProdutos();\
  } catch(e) { showToast("❌ Erro: " + e.message); console.error("Erro ao salvar:", e); }\
}\
\
async function excluirProduto(id) {\
  if (!confirm("Tem certeza que deseja excluir este produto do Baserow?")) return;\
  try {\
    const response = await fetch(`/api/gerente/produtos/${id}`, { method: "DELETE", headers: {"Content-Type": "application/json"} });\
    if (!response.ok) { const erro = await response.json(); throw new Error(erro.erro || "Erro ao excluir"); }\
    showToast("✅ Produto excluído do Baserow!");\
    carregarProdutos();\
  } catch(e) { showToast("❌ Erro: " + e.message); console.error("Erro ao excluir:", e); }\
}\
' gerente.html

# Atualizar a função carregarSecao para usar carregarProdutos
sed -i 's/else if (secao === '\''produtos'\'') carregarCatalogo('\''produtos'\'');/else if (secao === '\''produtos'\'') carregarProdutos();/g' gerente.html

echo "✅ Frontend atualizado para Produtos Baserow!"
