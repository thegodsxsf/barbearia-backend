#!/bin/bash

# Substituir a chamada de carregarCatalogo('assinaturas') por carregarPlanos()
sed -i 's/carregarCatalogo('\''assinaturas'\'')/carregarPlanos()/g' gerente.html

# Adicionar a função carregarPlanos() no JavaScript
sed -i '/\/\/ ============ CATÁLOGO ============/a \
\
// ============ PLANOS (BASEROW) ============\
async function carregarPlanos() {\
  try {\
    const response = await fetch("/api/gerente/planos");\
    if (!response.ok) throw new Error("Erro ao buscar planos");\
    const lista = await response.json();\
    const el = document.getElementById("tabelaAssinaturas");\
    if (!el) return;\
    console.log("📋 Planos (Baserow):", lista.length, "registros");\
    el.innerHTML = lista.length ? lista.map(p => `<tr><td>${p.icone || "⭐"} ${p.nome}</td><td>${formatarPreco(p.preco)}</td><td>${p.destaque ? "⭐" : "-"}</td><td>${p.ativo ? "✅" : "❌"}</td><td><div class="acoes"><button class="btn-mini gray" onclick="abrirModalPlano(${JSON.stringify(p).replace(/"/g, "&quot;")})">✏️</button><button class="btn-mini red" onclick="excluirPlano(${p.id})">🗑️</button></div></td></tr>`).join("") : "<tr><td colspan="5" class=\"empty-msg\">Nenhum plano cadastrado no Baserow.</td></tr>";\
  } catch(e) { console.error("Erro ao carregar planos:", e); showToast("Erro ao carregar planos: " + e.message); }\
}\
\
function abrirModalPlano(item=null) {\
  itemEditando = {tabela: "planos", id: item ? item.id : null};\
  document.getElementById("modalItemTitulo").textContent = item ? "✏️ Editar Plano" : "📋 Novo Plano";\
  document.getElementById("modalItemCampos").innerHTML = `\
    <div class="form-group"><label>Nome <span class="required">*</span></label><input type="text" id="campo_nome" value="${item ? item.nome || "" : ""}"></div>\
    <div class="form-group"><label>Preço (R$) <span class="required">*</span></label><input type="number" step="0.01" id="campo_preco" value="${item ? item.preco || 0 : 0}"></div>\
    <div class="form-group"><label>Descrição</label><textarea id="campo_descricao" rows="2">${item ? item.descricao || "" : ""}</textarea></div>\
    <div class="form-group"><label>Ativo</label><select id="campo_ativo"><option value="1" ${item && item.ativo ? "selected" : ""}>Sim</option><option value="0" ${item && !item.ativo ? "selected" : ""}>Não</option></select></div>\
  `;\
  document.getElementById("modalItem").classList.add("active");\
}\
\
async function salvarPlano() {\
  const {id} = itemEditando;\
  const dados = {\
    nome: document.getElementById("campo_nome").value.trim(),\
    preco: parseFloat(document.getElementById("campo_preco").value) || 0,\
    descricao: document.getElementById("campo_descricao").value.trim(),\
    ativo: parseInt(document.getElementById("campo_ativo").value) || 1\
  };\
  if (!dados.nome) { showToast("⚠️ Nome é obrigatório."); return; }\
  try {\
    let url = "/api/gerente/planos";\
    let method = "POST";\
    if (id) { url = `/api/gerente/planos/${id}`; method = "PUT"; }\
    const response = await fetch(url, { method, headers: {"Content-Type": "application/json"}, body: JSON.stringify(dados) });\
    if (!response.ok) { const erro = await response.json(); throw new Error(erro.erro || "Erro ao salvar"); }\
    showToast("✅ Plano salvo no Baserow!");\
    fecharModalItem();\
    carregarPlanos();\
  } catch(e) { showToast("❌ Erro: " + e.message); console.error("Erro ao salvar:", e); }\
}\
\
async function excluirPlano(id) {\
  if (!confirm("Tem certeza que deseja excluir este plano do Baserow?")) return;\
  try {\
    const response = await fetch(`/api/gerente/planos/${id}`, { method: "DELETE", headers: {"Content-Type": "application/json"} });\
    if (!response.ok) { const erro = await response.json(); throw new Error(erro.erro || "Erro ao excluir"); }\
    showToast("✅ Plano excluído do Baserow!");\
    carregarPlanos();\
  } catch(e) { showToast("❌ Erro: " + e.message); console.error("Erro ao excluir:", e); }\
}\
' gerente.html

# Substituir o onclick do botão "Novo Plano"
sed -i 's/abrirModalItem('\''assinaturas'\'')/abrirModalPlano()/g' gerente.html

echo "✅ Frontend atualizado!"
