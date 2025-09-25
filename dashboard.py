import streamlit as st
import pandas as pd
import plotly.express as px
from query import conexao  # sua função já existente

st.set_page_config(page_title="Dashboard • tb_registros", layout="wide")

# -----------------------------
# Carga de dados
# -----------------------------
QUERY = "SELECT * FROM tb_registros_teste"

@st.cache_data(show_spinner=False, ttl=300)
def carregar_dados():
    df = conexao(QUERY)
    # Garantir tipos corretos
    df = df.copy()
    df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")
    # Ordena por tempo e remove linhas sem tempo
    df = df.dropna(subset=["data_registro"]).sort_values("data_registro")
    # Garantir floats
    cols_float = [
        "co2_ppm","poeira1_mg_m3","poeira2_mg_m3","altitude_m",
        "umidade_ur","temperatura_c","pressao_pa"
    ]
    for c in cols_float:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Normaliza status para string (evita NaN no filtro)
    if "status_registro" in df.columns:
        df["status_registro"] = df["status_registro"].fillna("False").astype(str)
    return df

st.title("📈 Monitoramento de Sensores — tb_registros")

# Botão atualizar (ignora cache)
col_atualizar, col_download = st.columns([1, 3])
with col_atualizar:
    if st.button("🔄 ATUALIZAR DADOS"):
        st.cache_data.clear()

df = carregar_dados()

if df.empty:
    st.warning("Não há dados para exibir.")
    st.stop()

# -----------------------------
# Filtros laterais
# -----------------------------
st.sidebar.header("Filtros")

# Intervalo temporal padrão: últimos 7 dias (ou todo o range, se curto)
min_dt = df["data_registro"].min()
max_dt = df["data_registro"].max()
default_start = max(min_dt, max_dt - pd.Timedelta(days=7)) if pd.notna(min_dt) else min_dt

intervalo = st.sidebar.date_input(
    "Intervalo de datas",
    value=(default_start.date(), max_dt.date()),
    min_value=min_dt.date(),
    max_value=max_dt.date()
)

# Converte o resultado do date_input para timestamps de início/fim do dia
if isinstance(intervalo, tuple) and len(intervalo) == 2:
    inicio = pd.to_datetime(intervalo[0])
    fim = pd.to_datetime(intervalo[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    inicio = pd.to_datetime(intervalo)
    fim = pd.to_datetime(intervalo) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

# Status
op_status = sorted(df["status_registro"].dropna().unique().tolist())
status_sel = st.sidebar.multiselect(
    "Status do registro",
    options=op_status,
    default=op_status
)

# Frequência de reamostragem (para suavizar séries)
freq_map = {
    "Sem reamostragem (original)": None,
    "1 min": "T",
    "5 min": "5T",
    "15 min": "15T",
    "1 hora": "H",
    "6 horas": "6H",
    "1 dia": "D"
}
freq_label = st.sidebar.selectbox("Reamostragem", list(freq_map.keys()), index=3)
freq = freq_map[freq_label]

# Aplica filtros
mask = (
    (df["data_registro"] >= inicio) &
    (df["data_registro"] <= fim) &
    (df["status_registro"].isin(status_sel))
)
df_sel = df.loc[mask].copy()

# Reamostragem opcional
def reamostrar_por_freq(dfs, freq):
    if not freq:
        return dfs
    dfs = dfs.set_index("data_registro").sort_index()
    # Usa média por janela de tempo
    dfs = dfs.resample(freq).mean(numeric_only=True)
    # Mantém status como nulo na reamostragem; reconstitui coluna tempo
    dfs = dfs.reset_index()
    return dfs

df_plot = reamostrar_por_freq(df_sel, freq)

# -----------------------------
# Cards (métricas)
# -----------------------------
st.subheader("Visão geral")

if df_sel.empty:
    st.warning("Nenhum dado com os filtros atuais.")
else:
    # Último registro no intervalo filtrado (antes da reamostragem)
    ultimo = df_sel.sort_values("data_registro").tail(1).squeeze()

    # Métricas principais
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.info("CO₂ (ppm) — último", icon="🌫️")
        st.metric(label=str(ultimo["data_registro"]), value=f"{ultimo['co2_ppm']:.0f}" if pd.notna(ultimo["co2_ppm"]) else "—")
    with c2:
        st.info("Temp (°C) — último", icon="🌡️")
        st.metric(label=str(ultimo["data_registro"]), value=f"{ultimo['temperatura_c']:.1f}" if pd.notna(ultimo["temperatura_c"]) else "—")
    with c3:
        st.info("Umidade (%UR) — último", icon="💧")
        st.metric(label=str(ultimo["data_registro"]), value=f"{ultimo['umidade_ur']:.1f}" if pd.notna(ultimo["umidade_ur"]) else "—")
    with c4:
        st.info("Pressão (Pa) — último", icon="⚙️")
        st.metric(label=str(ultimo["data_registro"]), value=f"{ultimo['pressao_pa']:.0f}" if pd.notna(ultimo["pressao_pa"]) else "—")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.caption("Média CO₂ (ppm)")
        st.metric(label="Período filtrado", value=f"{df_sel['co2_ppm'].mean():.0f}")
    with c6:
        st.caption("Média Temp (°C)")
        st.metric(label="Período filtrado", value=f"{df_sel['temperatura_c'].mean():.1f}")
    with c7:
        st.caption("Média Umidade (%UR)")
        st.metric(label="Período filtrado", value=f"{df_sel['umidade_ur'].mean():.1f}")
    with c8:
        st.caption("Média Pressão (Pa)")
        st.metric(label="Período filtrado", value=f"{df_sel['pressao_pa'].mean():.0f}")

st.markdown("---")

# -----------------------------
# Gráficos
# -----------------------------
if df_plot.empty:
    st.warning("Sem pontos para plotar com os filtros/reamostragem atuais.")
    st.stop()

tabs = st.tabs(["📊 Séries temporais", "📈 Comparações", "🔍 Dispersões (correlações)"])

with tabs[0]:
    st.write("Séries temporais ao longo de *data_registro*")

    # Linha: CO2
    fig_co2 = px.line(
        df_plot, x="data_registro", y="co2_ppm",
        title=f"CO₂ (ppm) — {freq_label.lower()}",
        markers=False
    )
    st.plotly_chart(fig_co2, use_container_width=True)

    # Linha: poeira 1 e 2
    cols = st.columns(2)
    with cols[0]:
        fig_p1 = px.line(df_plot, x="data_registro", y="poeira1_mg_m3", title=f"Poeira 1 (mg/m³) — {freq_label.lower()}", markers=False)
        st.plotly_chart(fig_p1, use_container_width=True)
    with cols[1]:
        fig_p2 = px.line(df_plot, x="data_registro", y="poeira2_mg_m3", title=f"Poeira 2 (mg/m³) — {freq_label.lower()}", markers=False)
        st.plotly_chart(fig_p2, use_container_width=True)

    # Linha: temperatura e umidade
    cols = st.columns(2)
    with cols[0]:
        fig_t = px.line(df_plot, x="data_registro", y="temperatura_c", title=f"Temperatura (°C) — {freq_label.lower()}", markers=False)
        st.plotly_chart(fig_t, use_container_width=True)
    with cols[1]:
        fig_u = px.line(df_plot, x="data_registro", y="umidade_ur", title=f"Umidade (%UR) — {freq_label.lower()}", markers=False)
        st.plotly_chart(fig_u, use_container_width=True)

    # Linha: pressão e altitude
    cols = st.columns(2)
    with cols[0]:
        fig_p = px.line(df_plot, x="data_registro", y="pressao_pa", title=f"Pressão (Pa) — {freq_label.lower()}", markers=False)
        st.plotly_chart(fig_p, use_container_width=True)
    with cols[1]:
        fig_alt = px.line(df_plot, x="data_registro", y="altitude_m", title=f"Altitude (m) — {freq_label.lower()}", markers=False)
        st.plotly_chart(fig_alt, use_container_width=True)

with tabs[1]:
    st.write("Comparações lado a lado")
    # Média por janela de tempo (ou original) — barras
    # Exemplo: médias de poeira por período
    agrup = df_plot.copy()
    agrup["periodo"] = agrup["data_registro"].dt.strftime("%Y-%m-%d %H:%M") if freq else agrup["data_registro"].dt.strftime("%Y-%m-%d %H:%M:%S")
    fig_bar = px.bar(
        agrup, x="periodo", y=["poeira1_mg_m3", "poeira2_mg_m3"],
        barmode="group", title="Média por período — Poeira (mg/m³)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Boxplots para distribuição no período filtrado
    cols = st.columns(3)
    with cols[0]:
        st.caption("Distribuição CO₂ (ppm)")
        st.plotly_chart(px.box(df_sel, y="co2_ppm", points="outliers", title="CO₂"), use_container_width=True)
    with cols[1]:
        st.caption("Distribuição Temperatura (°C)")
        st.plotly_chart(px.box(df_sel, y="temperatura_c", points="outliers", title="Temperatura"), use_container_width=True)
    with cols[2]:
        st.caption("Distribuição Umidade (%UR)")
        st.plotly_chart(px.box(df_sel, y="umidade_ur", points="outliers", title="Umidade"), use_container_width=True)

with tabs[2]:
    st.write("Relações entre variáveis (útil para detectar correlações)")
    # Dispersões com cor pelo horário (para contexto temporal)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            px.scatter(df_sel, x="temperatura_c", y="umidade_ur", color="data_registro",
                       title="Temperatura vs Umidade", trendline="ols"),
            use_container_width=True
        ) # pip install statsmodels
    with c2:
        st.plotly_chart(
            px.scatter(df_sel, x="co2_ppm", y="poeira1_mg_m3", color="data_registro",
                       title="CO₂ vs Poeira 1", trendline="ols"),
            use_container_width=True
        )

# -----------------------------
# Tabela/Exportação
# -----------------------------
with col_download:
    st.download_button(
        "⬇️ Baixar CSV (filtro aplicado)",
        data=df_sel.to_csv(index=False).encode("utf-8"),
        file_name="tb_registros_filtrado.csv",
        mime="text/csv"
    )

with st.expander("Ver dados filtrados (amostra)"):
    st.dataframe(df_sel.tail(500), use_container_width=True)