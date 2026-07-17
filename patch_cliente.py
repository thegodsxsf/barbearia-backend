"""
Aplica no cliente.html as duas pequenas alterações necessárias para que
os pedidos/agendamentos feitos pelo cliente cheguem até o painel do
gerente (além de continuarem indo pelo WhatsApp, como já funcionava).

Uso: python3 patch_cliente.py
(precisa ser executado na mesma pasta onde está o cliente.html)
"""
import re
import sys

ARQUIVO = "cliente.html"

# Função auxiliar que será inserida uma única vez, logo no início do <script>
HELPER = """
    // ======== ENVIA O PEDIDO/AGENDAMENTO PARA O PAINEL DO GERENTE ========
    async function salvarPedidoServidor(dados) {
      try {
        await fetch('/api/pedidos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(dados)
        });
      } catch (e) {
        console.warn('Não foi possível registrar o pedido no painel do gerente:', e);
      }
    }
"""

ANCORA_SIMPLES_ANTES = """      const mensagem = `📋 *NOVO PEDIDO!*\\n\\n` +
        `✂️ *Serviço:* ${servicoSelecionadoGlobal.nome}\\n` +
        `💰 *Valor:* R$ ${servicoSelecionadoGlobal.preco.toFixed(2)}\\n\\n` +
        `👤 *Cliente:* ${nome}\\n` +
        `💳 *Pagamento:* ${pagamentoLabels[pagamentoSelecionadoSimples]}\\n\\n` +
        `⏳ *Status:* Aguardando atendimento`;
      
      const url = `https://wa.me/${bizWhatsapp}?text=${encodeURIComponent(mensagem)}`;
      window.open(url, '_blank');"""

ANCORA_SIMPLES_DEPOIS = """      const mensagem = `📋 *NOVO PEDIDO!*\\n\\n` +
        `✂️ *Serviço:* ${servicoSelecionadoGlobal.nome}\\n` +
        `💰 *Valor:* R$ ${servicoSelecionadoGlobal.preco.toFixed(2)}\\n\\n` +
        `👤 *Cliente:* ${nome}\\n` +
        `💳 *Pagamento:* ${pagamentoLabels[pagamentoSelecionadoSimples]}\\n\\n` +
        `⏳ *Status:* Aguardando atendimento`;

      salvarPedidoServidor({
        tipo: 'pedido',
        servico_nome: servicoSelecionadoGlobal.nome,
        valor: servicoSelecionadoGlobal.preco,
        cliente_nome: nome,
        pagamento: pagamentoSelecionadoSimples
      });

      const url = `https://wa.me/${bizWhatsapp}?text=${encodeURIComponent(mensagem)}`;
      window.open(url, '_blank');"""

ANCORA_COMPLETO_ANTES = """      mensagem += `\\n💳 *Pagamento:* ${pagamentoLabels[pagamentoSelecionadoCompleto]}`;
      if (observacoes) mensagem += `\\n📝 *Observações:* ${observacoes}`;
      mensagem += `\\n\\n⏳ *Status:* Aguardando atendimento`;
      
      const url = `https://wa.me/${bizWhatsapp}?text=${encodeURIComponent(mensagem)}`;
      window.open(url, '_blank');"""

ANCORA_COMPLETO_DEPOIS = """      mensagem += `\\n💳 *Pagamento:* ${pagamentoLabels[pagamentoSelecionadoCompleto]}`;
      if (observacoes) mensagem += `\\n📝 *Observações:* ${observacoes}`;
      mensagem += `\\n\\n⏳ *Status:* Aguardando atendimento`;

      salvarPedidoServidor({
        tipo: 'agendamento',
        servico_nome: servico.nome,
        valor: servico.preco,
        cliente_nome: nome,
        cliente_telefone: telefone,
        data_agendada: data,
        hora_agendada: hora,
        corte_em_casa: corteEmCasa,
        endereco: endereco,
        complemento: complemento,
        observacoes: observacoes,
        pagamento: pagamentoSelecionadoCompleto
      });

      const url = `https://wa.me/${bizWhatsapp}?text=${encodeURIComponent(mensagem)}`;
      window.open(url, '_blank');"""


def main():
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        conteudo = f.read()

    total_patches = 0

    if "salvarPedidoServidor" not in conteudo:
        conteudo = conteudo.replace("<script>", "<script>" + HELPER, 1)
        total_patches += 1
    else:
        print("Aviso: função salvarPedidoServidor já existe, pulando esse passo.")

    if ANCORA_SIMPLES_ANTES in conteudo:
        conteudo = conteudo.replace(ANCORA_SIMPLES_ANTES, ANCORA_SIMPLES_DEPOIS, 1)
        total_patches += 1
        print("OK: fluxo 'Pedido simples' conectado ao painel do gerente.")
    else:
        print("AVISO: não encontrei o trecho do fluxo simples (confirmarSimples). "
              "Se você editou o cliente.html, talvez precise conectar manualmente.")

    if ANCORA_COMPLETO_ANTES in conteudo:
        conteudo = conteudo.replace(ANCORA_COMPLETO_ANTES, ANCORA_COMPLETO_DEPOIS, 1)
        total_patches += 1
        print("OK: fluxo 'Agendamento completo' conectado ao painel do gerente.")
    else:
        print("AVISO: não encontrei o trecho do fluxo completo (confirmarCompleto). "
              "Se você editou o cliente.html, talvez precise conectar manualmente.")

    with open(ARQUIVO, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"\nConcluído. {total_patches} alteração(ões) aplicada(s) em {ARQUIVO}.")


if __name__ == "__main__":
    main()

