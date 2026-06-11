"""
GastoSmart - Interface Web via Streamlit
Identidade visual: paleta verde primária #1a6b2e com accent amarelo #f5c400.
Tema base em `.streamlit/config.toml`. Estilos finos via CSS inline abaixo.
"""

import os
from pathlib import Path

import streamlit as st

try:
    from . import services
except ImportError:
    import services

# Caminhos de assets
ASSETS = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS / "logo.svg"
FAVICON_PATH = ASSETS / "favicon.svg"

# Configuração da página
st.set_page_config(
    page_title="GastoSmart — Gerencie seus gastos",
    page_icon=str(FAVICON_PATH),
    layout="centered",
    initial_sidebar_state="expanded",
)

# CSS customizado
CUSTOM_CSS = """
<style>
  html, body, [class*="st-"] {
    font-family: "Inter", "Manrope", -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Roboto, sans-serif;
  }
  .block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 980px;
  }
  .gs-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 4px;
  }
  .gs-header .gs-logo {
    width: 52px;
    height: 52px;
    flex-shrink: 0;
  }
  .gs-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1a6b2e;
    margin: 0;
    line-height: 1.1;
    letter-spacing: -0.01em;
  }
  .gs-tagline {
    color: #6b7280;
    font-size: 0.95rem;
    margin: 4px 0 28px 66px;
  }
  [data-testid="stMetric"] {
    background: #f4f6f3;
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid #d9e7c8;
  }
  [data-testid="stMetricLabel"] {
    font-weight: 500;
    color: #4b5563;
  }
  [data-testid="stMetricValue"] {
    color: #1a6b2e;
    font-weight: 700;
  }
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
  }
  .stTabs [data-baseweb="tab"] {
    font-weight: 500;
    padding: 10px 14px;
  }
  .stButton button[kind="primary"],
  .stFormSubmitButton button {
    background: #1a6b2e;
    border-color: #1a6b2e;
    color: #fff;
    font-weight: 600;
  }
  .stButton button[kind="primary"]:hover,
  .stFormSubmitButton button:hover {
    background: #155a26;
    border-color: #155a26;
  }
  [data-testid="stSidebar"] {
    background: #f7f8f5;
    border-right: 1px solid #e5e7eb;
  }
  [data-testid="stSidebar"] [data-testid="stMetric"] {
    background: #ffffff;
    border-color: #e5e7eb;
  }
  [data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
  }
  .gs-footer {
    text-align: center;
    color: #9ca3af;
    font-size: 0.82rem;
    margin-top: 44px;
    padding-top: 14px;
    border-top: 1px solid #e5e7eb;
  }
  .gs-footer a {
    color: #1a6b2e;
    text-decoration: none;
  }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header com logo
logo_svg = LOGO_PATH.read_text(encoding="utf-8") if LOGO_PATH.exists() else ""

st.markdown(
    f"""
    <div class="gs-header">
        <div class="gs-logo">{logo_svg}</div>
        <h1>GastoSmart</h1>
    </div>
    <div class="gs-tagline">Gerenciador de gastos pessoais com integração Supabase</div>
    """,
    unsafe_allow_html=True,
)

# Sidebar: clima opcional
api_key = os.getenv("OPENWEATHER_API_KEY", "")
cidade = os.getenv("OPENWEATHER_CIDADE", "Brasilia")

with st.sidebar:
    st.markdown("### Clima")
    if api_key:
        clima = services.buscar_clima(cidade, api_key)
        if clima:
            st.metric(
                label=f"📍 {clima['cidade']}",
                value=f"{clima['temperatura']}°C",
                delta=clima["descricao"],
                delta_color="off",
            )
        else:
            st.warning("⚠️ Não foi possível obter o clima no momento.")
    else:
        st.caption("Configure `OPENWEATHER_API_KEY` para ver o clima da sua cidade.")

# Abas principais
tab_resumo, tab_listar, tab_adicionar, tab_remover = st.tabs([
    "📊 Resumo",
    "📋 Listar",
    "📝 Adicionar",
    "🗑️ Remover",
])

# TAB 1: RESUMO
with tab_resumo:
    st.subheader("Resumo financeiro")
    resumo = services.resumo_gastos()

    st.metric(label="Total geral", value=f"R$ {resumo['total']:.2f}")

    if resumo["por_categoria"]:
        st.markdown("#### Por categoria")
        sorted_categories = sorted(
            resumo["por_categoria"].items(), key=lambda x: -x[1]
        )

        col1, col2 = st.columns([1, 1.2])
        with col1:
            for cat, valor in sorted_categories:
                st.write(f"**{cat}:** R$ {valor:.2f}")
        with col2:
            st.bar_chart(resumo["por_categoria"], height=240)
    else:
        st.info("Nenhum gasto registrado ainda. Use a aba **Adicionar** para começar.")

# TAB 2: LISTAR
with tab_listar:
    st.subheader("Seus gastos")
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
                "valor": st.column_config.NumberColumn(
                    "Valor", format="R$ %.2f"
                ),
                "criado_em": None,
            },
            hide_index=True,
            width="stretch",
        )

# TAB 3: ADICIONAR
with tab_adicionar:
    st.subheader("Novo gasto")

    with st.form("form_adicionar", clear_on_submit=True):
        descricao = st.text_input("Descrição", placeholder="Ex.: Almoço no restaurante")
        valor = st.number_input(
            "Valor (R$)", min_value=0.01, step=0.50, format="%.2f"
        )
        categoria = st.selectbox("Categoria", services.CATEGORIAS)

        submitted = st.form_submit_button("Salvar gasto", type="primary")

        if submitted:
            try:
                gasto = services.adicionar_gasto(descricao, valor, categoria)
                st.success(
                    f"✅ Gasto adicionado! ID #{gasto['id']} — {gasto['descricao']}"
                )
                st.rerun()
            except ValueError as e:
                st.error(f"❌ Erro: {e}")

# TAB 4: REMOVER
with tab_remover:
    st.subheader("Remover gasto")
    st.caption("Confira o ID na aba **Listar** antes de remover.")

    gasto_id = st.number_input(
        "ID do gasto a remover", min_value=1, step=1
    )
    if st.button("Remover", type="primary"):
        if services.remover_gasto(int(gasto_id)):
            st.success(f"✅ Gasto #{gasto_id} removido com sucesso.")
            st.rerun()
        else:
            st.error(f"❌ Gasto #{gasto_id} não encontrado.")

# Footer
st.markdown(
    """
    <div class="gs-footer">
        GastoSmart · Entrega Final Bootcamp II · CEUB ·
        <a href="https://github.com/erickcmendes/gastosmart" target="_blank">Repositório no GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
