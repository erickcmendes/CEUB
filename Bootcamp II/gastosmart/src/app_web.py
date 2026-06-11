"""
GastoSmart - Interface Web via Streamlit
"""

import os
import streamlit as st

try:
    from . import services
except ImportError:
    import services

# Configuração da página
st.set_page_config(page_title="GastoSmart", page_icon="💸", layout="centered")

st.title("💸 GastoSmart")
st.write("Gerenciador de Gastos Pessoais com integração Supabase")

# Sidebar com informações do clima (se a chave API estiver configurada)
api_key = os.getenv("OPENWEATHER_API_KEY", "")
cidade = os.getenv("OPENWEATHER_CIDADE", "Brasilia")

if api_key:
    clima = services.buscar_clima(cidade, api_key)
    if clima:
        st.sidebar.metric(
            label=f"📍 Clima em {clima['cidade']}", 
            value=f"{clima['temperatura']}°C", 
            delta=clima['descricao'],
            delta_color="off"
        )
    else:
        st.sidebar.warning("⚠️ Não foi possível obter o clima no momento.")

# Cria as abas para as diferentes funcionalidades
tab_resumo, tab_listar, tab_adicionar, tab_remover = st.tabs([
    "📊 Ver Resumo", 
    "📋 Listar Gastos", 
    "📝 Adicionar Gasto", 
    "🗑️ Remover Gasto"
])

# ─── TAB 1: VER RESUMO ────────────────────────────────────────────────────────
with tab_resumo:
    st.header("Resumo Financeiro")
    resumo = services.resumo_gastos()
    
    st.metric(label="Total Geral", value=f"R$ {resumo['total']:.2f}")
    
    if resumo["por_categoria"]:
        st.subheader("Por Categoria")
        # Displaying as a neat bar chart and data list
        sorted_categories = sorted(resumo["por_categoria"].items(), key=lambda x: -x[1])
        
        col1, col2 = st.columns(2)
        with col1:
            for cat, valor in sorted_categories:
                st.write(f"**{cat}:** R$ {valor:.2f}")
        with col2:
            st.bar_chart(resumo["por_categoria"])
    else:
        st.info("Nenhum gasto registrado ainda.")

# ─── TAB 2: LISTAR GASTOS ─────────────────────────────────────────────────────
with tab_listar:
    st.header("Lista de Gastos")
    gastos = services.listar_gastos()
    
    if not gastos:
        st.info("Nenhum gasto cadastrado ainda.")
    else:
        st.dataframe(
            gastos, 
            column_config={
                "id": "ID",
                "data": "Data",
                "categoria": "Categoria",
                "descricao": "Descrição",
                "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "criado_em": None  # Oculta timestamps do banco
            },
            hide_index=True,
            width="stretch"  
        )

# ─── TAB 3: ADICIONAR GASTO ───────────────────────────────────────────────────
with tab_adicionar:
    st.header("Novo Gasto")
    
    with st.form("form_adicionar", clear_on_submit=True):
        descricao = st.text_input("Descrição:")
        valor = st.number_input("Valor (R$):", min_value=0.01, step=0.50, format="%.2f")
        categoria = st.selectbox("Categoria:", services.CATEGORIAS)
        
        submitted = st.form_submit_button("Salvar Gasto")
        
        if submitted:
            try:
                gasto = services.adicionar_gasto(descricao, valor, categoria)
                st.success(f"✅ Gasto adicionado! ID #{gasto['id']} — {gasto['descricao']}")
                st.rerun()  # Força atualização para mostrar o novo gasto na lista e resumo
            except ValueError as e:
                st.error(f"❌ Erro: {e}")

# ─── TAB 4: REMOVER GASTO ─────────────────────────────────────────────────────
with tab_remover:
    st.header("Remover Gasto")
    
    gasto_id = st.number_input("Digite o ID do gasto a remover:", min_value=1, step=1)
    if st.button("Remover", type="primary"):
        if services.remover_gasto(int(gasto_id)):
            st.success(f"✅ Gasto #{gasto_id} removido com sucesso.")
            st.rerun()
        else:
            st.error(f"❌ Gasto #{gasto_id} não encontrado.")