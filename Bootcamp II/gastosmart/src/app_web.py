"""
GastoSmart - Interface Web via Streamlit
Identidade visual: paleta verde primaria #1a6b2e com accent amarelo #f5c400.
Tema base em `.streamlit/config.toml` (apenas primaryColor; resto adapta a light/dark).
Estilos finos via CSS inline abaixo - usando variaveis do Streamlit para
nao quebrar o tema do usuario nem a fonte de icones (Material Symbols).
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

# Configuracao da pagina
st.set_page_config(
    page_title="GastoSmart - Gerencie seus gastos",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "💸",
    layout="centered",
    initial_sidebar_state="expanded",
)

# CSS customizado - conservador, sem mexer em font-family global
# nem em backgrounds hardcoded (preserva tema claro/escuro do usuario)
CUSTOM_CSS = """
<style>
  /* Container principal */
  .block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 980px;
  }

  /* Header do app */
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
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .gs-header .gs-logo svg {
    width: 100%;
    height: 100%;
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
    opacity: 0.7;
    font-size: 0.95rem;
    margin: 4px 0 28px 66px;
  }

  /* Tabs - so ajusta espacamento, mantem cores do tema */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
  }
  .stTabs [data-baseweb="tab"] {
    font-weight: 500;
    padding: 10px 14px;
  }

  /* Tabela com bordas arredondadas */
  [data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
  }

  /* Footer adaptativo */
  .gs-footer {
    text-align: center;
    opacity: 0.6;
    font-size: 0.82rem;
    margin-top: 44px;
    padding-top: 14px;
    border-top: 1px solid rgba(128, 128, 128, 0.25);
  }
  .gs-footer a {
    color: #1a6b2e;
    text-decoration: none;
    font-weight: 500;
  }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header com logo SVG inline
logo_svg = LOGO_PATH.read_text(encoding="utf-8") if LOGO_PATH.exists() else ""

st.markdown(
    f"""
    <div class="gs-header">
        <div class="gs-logo">{logo_svg}</div>
        <h1>GastoSmart</h1>
    </div>
    <div class="gs-tagline">Gerenciador de gastos pessoais com integracao Supabase</div>
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
                    f"✅ Gasto adicionado! ID #{gasto['id']} - {gasto['descricao']}"
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
        GastoSmart · Entrega Final Bootcamp II · CEUB · <a href="https://github.com/erickcmendes/gastosmart" target="_blank">Repositório no GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
