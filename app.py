"""
Dashboard interactivo — Análisis de Ventas E-commerce (Online Retail)
Ejecutar con: streamlit run app.py
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# --------------------------------------------------------------------------
# RUTA AL ARCHIVO DE DATOS
# --------------------------------------------------------------------------
# BASE_DIR = carpeta donde vive este mismo app.py (sin importar desde dónde
# se ejecute el comando `streamlit run`).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 👉 Cambia "data" por el nombre real de tu subcarpeta donde está el Excel.
DATA_PATH = os.path.join(BASE_DIR, "data/raw", "Online Retail.xlsx")

# --------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Ventas | Online Retail",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = {
    "brass": "#96702F",
    "brass_l": "#B08A45",
    "ink": "#1E2C3A",
    "forest": "#3E5C42",
    "stamp": "#A13A2E",
    "slate": "#6B7F8C",
}
SEG_COLORS = {
    "Campeones": "#3E5C42",
    "Clientes Leales": "#B08A45",
    "Potenciales": "#6B7F8C",
    "En Riesgo": "#C99A4A",
    "Perdidos / Bajo Valor": "#A13A2E",
}

st.markdown("""
<style>
    .stMetric { background: #F3F0E5; border: 1px solid rgba(30,44,58,0.15); padding: 12px 16px; border-radius: 4px; }
    div[data-testid="stMetricLabel"] { font-size: 13px; color: #4A5A68; }
    div[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; color: #1E2C3A; }
    h1, h2, h3 { color: #1E2C3A; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# CARGA Y LIMPIEZA DE DATOS
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando y limpiando datos...")
def load_data(path=DATA_PATH):
    df = pd.read_excel(path)
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["EsCancelacion"] = df["InvoiceNo"].str.startswith("C")

    df_ventas = df[(~df["EsCancelacion"]) & (df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    df_ventas["ImporteTotal"] = df_ventas["Quantity"] * df_ventas["UnitPrice"]
    df_ventas["Fecha"] = df_ventas["InvoiceDate"].dt.date
    df_ventas["AnioMes"] = df_ventas["InvoiceDate"].dt.to_period("M").astype(str)
    df_ventas["DiaSemana"] = df_ventas["InvoiceDate"].dt.day_name()
    df_ventas["Hora"] = df_ventas["InvoiceDate"].dt.hour

    df_cancel = df[df["EsCancelacion"]].copy()
    df_cancel["ImporteTotal"] = df_cancel["Quantity"] * df_cancel["UnitPrice"]

    return df, df_ventas, df_cancel


@st.cache_data(show_spinner=False)
def compute_rfm(df_ventas):
    base = df_ventas.dropna(subset=["CustomerID"]).copy()
    fecha_ref = base["InvoiceDate"].max() + timedelta(days=1)

    rfm = base.groupby("CustomerID").agg(
        Recencia=("InvoiceDate", lambda x: (fecha_ref - x.max()).days),
        Frecuencia=("InvoiceNo", "nunique"),
        Monetario=("ImporteTotal", "sum"),
    ).reset_index()

    rfm["R_Score"] = pd.qcut(rfm["Recencia"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frecuencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetario"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    def segmentar(row):
        if row["RFM_Score"] >= 13:
            return "Campeones"
        elif row["RFM_Score"] >= 10:
            return "Clientes Leales"
        elif row["RFM_Score"] >= 7:
            return "Potenciales"
        elif row["RFM_Score"] >= 5:
            return "En Riesgo"
        else:
            return "Perdidos / Bajo Valor"

    rfm["Segmento"] = rfm.apply(segmentar, axis=1)
    return rfm


try:
    df_raw, df_ventas_full, df_cancel_full = load_data()
except FileNotFoundError:
    st.error(
        f"No se encontró el archivo en la ruta esperada:\n\n`{DATA_PATH}`\n\n"
        "Verifica que el nombre de la subcarpeta en `DATA_PATH` (dentro de `app.py`) "
        "coincida con el nombre real de tu subcarpeta, y que el Excel se llame "
        "exactamente `Online_Retail.xlsx`."
    )
    st.stop()

rfm_full = compute_rfm(df_ventas_full)

# --------------------------------------------------------------------------
# SIDEBAR — FILTROS INTERACTIVOS
# --------------------------------------------------------------------------
st.sidebar.title("📊 Filtros")

fecha_min = df_ventas_full["InvoiceDate"].min().date()
fecha_max = df_ventas_full["InvoiceDate"].max().date()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max,
)
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_ini, fecha_fin = rango_fechas
else:
    fecha_ini, fecha_fin = fecha_min, fecha_max

paises_disponibles = sorted(df_ventas_full["Country"].unique().tolist())
paises_sel = st.sidebar.multiselect(
    "País",
    options=paises_disponibles,
    default=[],
    help="Vacío = todos los países",
)

segmentos_disponibles = ["Campeones", "Clientes Leales", "Potenciales", "En Riesgo", "Perdidos / Bajo Valor"]
segmentos_sel = st.sidebar.multiselect(
    "Segmento de cliente (RFM)",
    options=segmentos_disponibles,
    default=[],
    help="Vacío = todos los segmentos. Filtra pedidos de clientes en estos segmentos.",
)

incluir_devoluciones = st.sidebar.checkbox("Incluir vista de devoluciones/cancelaciones", value=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Fuente: [UCI ML Repository — Online Retail Dataset]"
    "(https://archive.ics.uci.edu/dataset/352/online+retail) · Datos abiertos"
)

# --------------------------------------------------------------------------
# APLICAR FILTROS
# --------------------------------------------------------------------------
mask = (
    (df_ventas_full["Fecha"] >= fecha_ini) &
    (df_ventas_full["Fecha"] <= fecha_fin)
)
if paises_sel:
    mask &= df_ventas_full["Country"].isin(paises_sel)

df_ventas = df_ventas_full[mask].copy()

if segmentos_sel:
    clientes_validos = rfm_full[rfm_full["Segmento"].isin(segmentos_sel)]["CustomerID"]
    df_ventas = df_ventas[df_ventas["CustomerID"].isin(clientes_validos)]

rfm = rfm_full[rfm_full["CustomerID"].isin(df_ventas["CustomerID"].dropna().unique())].copy()
if segmentos_sel:
    rfm = rfm[rfm["Segmento"].isin(segmentos_sel)]

if df_ventas.empty:
    st.warning("No hay datos para la combinación de filtros seleccionada. Ajusta los filtros en la barra lateral.")
    st.stop()

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
st.title("📊 Dashboard de Ventas — E-commerce (Online Retail)")
st.caption(
    f"Mostrando datos del **{fecha_ini}** al **{fecha_fin}**"
    + (f" · Países: {', '.join(paises_sel)}" if paises_sel else " · Todos los países")
    + (f" · Segmentos: {', '.join(segmentos_sel)}" if segmentos_sel else "")
)

# --------------------------------------------------------------------------
# KPIs
# --------------------------------------------------------------------------
ingresos_totales = df_ventas["ImporteTotal"].sum()
num_pedidos = df_ventas["InvoiceNo"].nunique()
num_clientes = df_ventas["CustomerID"].nunique()
ticket_promedio = ingresos_totales / num_pedidos if num_pedidos else 0
unidades = df_ventas["Quantity"].sum()
num_paises = df_ventas["Country"].nunique()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Ingresos totales", f"£{ingresos_totales:,.0f}")
col2.metric("Pedidos", f"{num_pedidos:,}")
col3.metric("Ticket promedio", f"£{ticket_promedio:,.2f}")
col4.metric("Clientes únicos", f"{num_clientes:,}")
col5.metric("Unidades vendidas", f"{unidades:,}")
col6.metric("Países", f"{num_paises}")

st.markdown("---")

# --------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------
tab_tendencia, tab_productos, tab_geografia, tab_clientes, tab_devoluciones = st.tabs(
    ["📈 Tendencia", "📦 Productos", "🌍 Geografía", "👥 Clientes (RFM)", "↩️ Devoluciones"]
)

CHART_TEMPLATE = "plotly_white"

# ---------------- TAB TENDENCIA ----------------
with tab_tendencia:
    st.subheader("Evolución mensual de ingresos y pedidos")

    ventas_mensuales = df_ventas.groupby("AnioMes").agg(
        Ingresos=("ImporteTotal", "sum"),
        Pedidos=("InvoiceNo", "nunique"),
    ).reset_index()

    fig = go.Figure()
    fig.add_bar(x=ventas_mensuales["AnioMes"], y=ventas_mensuales["Ingresos"],
                name="Ingresos (£)", marker_color=PALETTE["brass_l"])
    fig.add_trace(go.Scatter(x=ventas_mensuales["AnioMes"], y=ventas_mensuales["Pedidos"],
                              name="Pedidos", yaxis="y2", mode="lines+markers",
                              line=dict(color=PALETTE["ink"], width=2)))
    fig.update_layout(
        template=CHART_TEMPLATE,
        yaxis=dict(title="Ingresos (£)"),
        yaxis2=dict(title="Nº Pedidos", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        height=420,
        margin=dict(t=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ingresos por día de la semana")
        orden_dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        ventas_dia = df_ventas.groupby("DiaSemana")["ImporteTotal"].sum().reindex(orden_dias).fillna(0)
        fig2 = px.bar(x=nombres_dias, y=ventas_dia.values, template=CHART_TEMPLATE,
                      color_discrete_sequence=[PALETTE["forest"]], labels={"x": "", "y": "Ingresos (£)"})
        fig2.update_layout(height=350, margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        st.subheader("Ingresos por hora del día")
        ventas_hora = df_ventas.groupby("Hora")["ImporteTotal"].sum()
        fig3 = px.area(x=ventas_hora.index, y=ventas_hora.values, template=CHART_TEMPLATE,
                       color_discrete_sequence=[PALETTE["stamp"]], labels={"x": "Hora", "y": "Ingresos (£)"})
        fig3.update_layout(height=350, margin=dict(t=10))
        st.plotly_chart(fig3, use_container_width=True)

# ---------------- TAB PRODUCTOS ----------------
with tab_productos:
    n_top = st.slider("Número de productos a mostrar (Top N)", 5, 25, 10, key="n_prod")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Top {n_top} productos por ingresos")
        top_ing = df_ventas.groupby("Description")["ImporteTotal"].sum().sort_values(ascending=False).head(n_top)
        fig = px.bar(x=top_ing.values, y=top_ing.index, orientation="h", template=CHART_TEMPLATE,
                    color_discrete_sequence=[PALETTE["brass_l"]], labels={"x": "Ingresos (£)", "y": ""})
        fig.update_layout(height=max(350, n_top * 28), yaxis=dict(autorange="reversed"), margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader(f"Top {n_top} productos por unidades")
        top_unid = df_ventas.groupby("Description")["Quantity"].sum().sort_values(ascending=False).head(n_top)
        fig = px.bar(x=top_unid.values, y=top_unid.index, orientation="h", template=CHART_TEMPLATE,
                    color_discrete_sequence=[PALETTE["slate"]], labels={"x": "Unidades", "y": ""})
        fig.update_layout(height=max(350, n_top * 28), yaxis=dict(autorange="reversed"), margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Buscar un producto específico")
    busqueda = st.text_input("Escribe parte del nombre del producto", "")
    if busqueda:
        resultado = (
            df_ventas[df_ventas["Description"].str.contains(busqueda, case=False, na=False)]
            .groupby("Description")
            .agg(Ingresos=("ImporteTotal", "sum"), Unidades=("Quantity", "sum"), Pedidos=("InvoiceNo", "nunique"))
            .sort_values("Ingresos", ascending=False)
        )
        st.dataframe(resultado.style.format({"Ingresos": "£{:,.2f}", "Unidades": "{:,}", "Pedidos": "{:,}"}),
                     use_container_width=True)

# ---------------- TAB GEOGRAFIA ----------------
with tab_geografia:
    ventas_pais = df_ventas.groupby("Country").agg(
        Ingresos=("ImporteTotal", "sum"),
        Pedidos=("InvoiceNo", "nunique"),
        Clientes=("CustomerID", "nunique"),
    ).sort_values("Ingresos", ascending=False)

    incluir_uk = st.checkbox("Incluir Reino Unido en el gráfico", value=False,
                              help="UK suele dominar el eje y opacar al resto de los países")

    tabla_paises = ventas_pais if incluir_uk else ventas_pais.drop("United Kingdom", errors="ignore")
    top_n_pais = st.slider("Número de países a mostrar", 5, min(30, len(tabla_paises)), 10, key="n_pais")
    tabla_paises = tabla_paises.head(top_n_pais)

    fig = px.bar(tabla_paises, x="Ingresos", y=tabla_paises.index, orientation="h",
                template=CHART_TEMPLATE, color_discrete_sequence=[PALETTE["ink"]])
    fig.update_layout(height=max(350, top_n_pais * 32), yaxis=dict(autorange="reversed"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    if "United Kingdom" in ventas_pais.index:
        uk_pct = ventas_pais.loc["United Kingdom", "Ingresos"] / ventas_pais["Ingresos"].sum() * 100
        st.info(f"🇬🇧 Reino Unido representa el **{uk_pct:.1f}%** de los ingresos en la selección actual.")

    st.subheader("Tabla completa por país")
    st.dataframe(
        ventas_pais.style.format({"Ingresos": "£{:,.2f}", "Pedidos": "{:,}", "Clientes": "{:,}"}),
        use_container_width=True,
    )

# ---------------- TAB CLIENTES / RFM ----------------
with tab_clientes:
    if rfm.empty:
        st.warning("No hay clientes con CustomerID en la selección actual de filtros.")
    else:
        resumen_seg = rfm.groupby("Segmento").agg(
            Clientes=("CustomerID", "count"),
            IngresoTotal=("Monetario", "sum"),
        ).reindex(segmentos_disponibles).dropna()
        resumen_seg["PctIngreso"] = resumen_seg["IngresoTotal"] / resumen_seg["IngresoTotal"].sum() * 100

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Clientes por segmento")
            fig = px.pie(resumen_seg, values="Clientes", names=resumen_seg.index, hole=0.55,
                        color=resumen_seg.index, color_discrete_map=SEG_COLORS, template=CHART_TEMPLATE)
            fig.update_layout(height=380, margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("Ingresos por segmento (%)")
            fig = px.bar(resumen_seg, x="PctIngreso", y=resumen_seg.index, orientation="h",
                        color=resumen_seg.index, color_discrete_map=SEG_COLORS, template=CHART_TEMPLATE,
                        labels={"PctIngreso": "% del ingreso total", "y": ""})
            fig.update_layout(height=380, showlegend=False, margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Curva de Pareto — concentración de ingresos por cliente")
        rfm_sorted = rfm.sort_values("Monetario", ascending=False).reset_index(drop=True)
        rfm_sorted["CumIngreso"] = rfm_sorted["Monetario"].cumsum() / rfm_sorted["Monetario"].sum() * 100
        rfm_sorted["CumClientes"] = (rfm_sorted.index + 1) / len(rfm_sorted) * 100
        clientes_80 = (rfm_sorted["CumIngreso"] <= 80).sum()
        pct_80 = clientes_80 / len(rfm_sorted) * 100

        fig = px.area(rfm_sorted, x="CumClientes", y="CumIngreso", template=CHART_TEMPLATE,
                     color_discrete_sequence=[PALETTE["brass"]],
                     labels={"CumClientes": "% acumulado de clientes", "CumIngreso": "% acumulado de ingresos"})
        fig.add_hline(y=80, line_dash="dash", line_color=PALETTE["stamp"])
        fig.add_vline(x=pct_80, line_dash="dash", line_color=PALETTE["stamp"])
        fig.update_layout(height=380, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"El **{pct_80:.1f}%** de los clientes de la selección actual genera el 80% de los ingresos.")

        st.subheader("Top clientes por valor")
        n_clientes = st.slider("Número de clientes a mostrar", 5, 50, 10, key="n_clientes")
        top_clientes = rfm.sort_values("Monetario", ascending=False).head(n_clientes)[
            ["CustomerID", "Monetario", "Frecuencia", "Recencia", "Segmento"]
        ].rename(columns={
            "CustomerID": "ID Cliente", "Monetario": "Gasto total (£)",
            "Frecuencia": "Nº Pedidos", "Recencia": "Días desde última compra",
        })
        st.dataframe(
            top_clientes.style.format({"Gasto total (£)": "£{:,.2f}"}),
            use_container_width=True, hide_index=True,
        )

        csv = top_clientes.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar tabla de clientes (CSV)", csv, "top_clientes.csv", "text/csv")

# ---------------- TAB DEVOLUCIONES ----------------
with tab_devoluciones:
    if not incluir_devoluciones:
        st.info("Activa la casilla 'Incluir vista de devoluciones/cancelaciones' en la barra lateral para ver esta sección.")
    else:
        df_cancel = df_cancel_full[
            (df_cancel_full["InvoiceDate"].dt.date >= fecha_ini) &
            (df_cancel_full["InvoiceDate"].dt.date <= fecha_fin)
        ].copy()
        if paises_sel:
            df_cancel = df_cancel[df_cancel["Country"].isin(paises_sel)]

        valor_cancel = abs(df_cancel["ImporteTotal"].sum())
        pedidos_totales_periodo = df_raw[
            (df_raw["InvoiceDate"].dt.date >= fecha_ini) & (df_raw["InvoiceDate"].dt.date <= fecha_fin)
        ]["InvoiceNo"].nunique()
        tasa_cancel = df_cancel["InvoiceNo"].nunique() / pedidos_totales_periodo * 100 if pedidos_totales_periodo else 0

        c1, c2 = st.columns(2)
        c1.metric("Valor devuelto/cancelado", f"£{valor_cancel:,.2f}")
        c2.metric("Tasa de cancelación", f"{tasa_cancel:.2f}%")

        if not df_cancel.empty:
            n_devol = st.slider("Número de productos a mostrar", 5, 25, 10, key="n_devol")
            top_devol = df_cancel.groupby("Description")["Quantity"].sum().sort_values().head(n_devol).abs()
            fig = px.bar(x=top_devol.values, y=top_devol.index, orientation="h", template=CHART_TEMPLATE,
                        color_discrete_sequence=[PALETTE["stamp"]], labels={"x": "Unidades devueltas", "y": ""})
            fig.update_layout(height=max(350, n_devol * 28), yaxis=dict(autorange="reversed"), margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No hay devoluciones/cancelaciones registradas para la selección actual de filtros.")

st.markdown("---")
st.caption(
    "Dashboard generado a partir del dataset "
    "[Online Retail — UCI ML Repository](https://archive.ics.uci.edu/dataset/352/online+retail) (datos abiertos). "
    "Se excluyen pedidos cancelados y líneas con cantidad o precio ≤ 0 del cálculo de ingresos, salvo en la sección de Devoluciones."
)
