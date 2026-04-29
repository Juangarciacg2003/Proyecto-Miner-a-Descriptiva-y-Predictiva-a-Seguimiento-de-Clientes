import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Configuración de la página ─────────────────────────────────────
st.set_page_config(
    page_title = "Customer Intelligence",
    page_icon  = "📊",
    layout     = "wide"
)

# ── Cargar datos ───────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    return pd.read_csv('rfm_clientes.csv')

rfm = cargar_datos()

# ── Sidebar ────────────────────────────────────────────────────────
st.sidebar.image(
    "https://img.icons8.com/fluency/96/combo-chart.png",
    width=80
)
st.sidebar.title("Customer Intelligence")
st.sidebar.markdown("Sistema de análisis de clientes para PYMES")
st.sidebar.divider()

seccion = st.sidebar.radio(
    "Navegación",
    ["📊 Resumen General",
     "👥 Segmentos RFM",
     "🔵 Clusters",
     "⚠️ Riesgo de Churn"]
)

# ══════════════════════════════════════════════════════════════════
# SECCIÓN 1 — RESUMEN GENERAL
# ══════════════════════════════════════════════════════════════════
if seccion == "📊 Resumen General":
    st.title("📊 Resumen General")
    st.markdown("Vista general del comportamiento de clientes — Online Retail ")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total clientes",    f"{len(rfm):,}")
    col2.metric("Ingreso total",     f"£{rfm['Monetary'].sum():,.0f}")
    col3.metric("Churn rate",        f"{rfm['Churn'].mean():.1%}")
    col4.metric("Recency promedio",  f"{rfm['Recency'].mean():.0f} días")

    st.divider()

    # Gráficos lado a lado
    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.histogram(rfm, x='Recency', nbins=50,
                            title='Distribución de Recency (días)',
                            color_discrete_sequence=['#7F77DD'])
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = px.histogram(rfm, x='Frequency', nbins=50,
                            title='Distribución de Frequency (compras)',
                            color_discrete_sequence=['#5DCAA5'])
        st.plotly_chart(fig, use_container_width=True)

    # Tabla resumen por segmento
    st.subheader("Resumen por segmento RFM")
    resumen = rfm.groupby('Segmento').agg(
        Clientes  = ('CustomerID', 'count'),
        Recency   = ('Recency',    'mean'),
        Frequency = ('Frequency',  'mean'),
        Monetary  = ('Monetary',   'mean'),
        Churn     = ('Churn',      'mean')
    ).round(1).reset_index()
    resumen['Churn'] = resumen['Churn'].apply(lambda x: f"{x:.0%}")
    resumen['Monetary'] = resumen['Monetary'].apply(lambda x: f"£{x:,.0f}")
    st.dataframe(resumen, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════
# SECCIÓN 2 — SEGMENTOS RFM
# ══════════════════════════════════════════════════════════════════
elif seccion == "👥 Segmentos RFM":
    st.title("👥 Segmentos RFM")
    st.info("📌 Segmentación basada en reglas de negocio RFM definidas manualmente. "
            "Puede diferir del Cluster K-Means porque usan lógicas distintas.")

    # Filtro por segmento
    segmentos = ['Todos'] + sorted(rfm['Segmento'].unique().tolist())
    seg_sel = st.selectbox("Filtrar por segmento:", segmentos)

    df_seg = rfm if seg_sel == 'Todos' else rfm[rfm['Segmento'] == seg_sel]

    # KPIs del segmento
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes",         f"{len(df_seg):,}")
    col2.metric("Ingreso promedio", f"£{df_seg['Monetary'].mean():,.0f}")
    col3.metric("Recency promedio", f"{df_seg['Recency'].mean():.0f} días")

    st.divider()
    col_a, col_b = st.columns(2)

   with col_a:
    # Diccionario de colores fijo por segmento
    colores = {
        'Campeones':   '#2ecc71',
        'Leales':      '#3498db',
        'En riesgo':   '#e74c3c',
        'Perdidos':    '#95a5a6',
        'Potenciales': '#f39c12',
        'Nuevos':      '#9b59b6'
    }

    conteo = rfm['Segmento'].value_counts().reset_index()
    fig = px.bar(conteo, x='Segmento', y='count',
                 title='Clientes por segmento',
                 color='Segmento',
                 color_discrete_map=colores,  # ← colores fijos
                 text='count')
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    ingreso = rfm.groupby('Segmento')['Monetary'].sum().reset_index()
    fig = px.pie(ingreso, names='Segmento', values='Monetary',
                 title='Ingreso total por segmento',
                 color='Segmento',
                 color_discrete_map=colores)  # ← mismos colores
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de clientes
    st.subheader(f"Clientes — {seg_sel}")
    st.dataframe(
        df_seg[['CustomerID','Recency','Frequency',
                'Monetary','RFM_Total','Segmento']]
        .sort_values('Monetary', ascending=False),
        use_container_width=True, hide_index=True
    )

# ══════════════════════════════════════════════════════════════════
# SECCIÓN 3 — CLUSTERS
# ══════════════════════════════════════════════════════════════════
elif seccion == "🔵 Clusters":
    st.title("🔵 Clusters K-Means")
    st.info("📌 Segmentación basada en similitud matemática entre clientes. "
            "El algoritmo agrupa por Recency, Frequency y Monetary en conjunto, "
            "por eso un cliente puede ser 'Perdido' en RFM pero 'VIP' en K-Means "
            "si su Frequency o Monetary son muy altos.")

    col_a, col_b = st.columns(2)

    with col_a:
        conteo = rfm['Cluster_nombre'].value_counts().reset_index()
        fig = px.bar(conteo, x='Cluster_nombre', y='count',
                     title='Clientes por cluster',
                     color='Cluster_nombre', text='count')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        perfil = rfm.groupby('Cluster_nombre')[
            ['Recency','Frequency','Monetary']].mean().round(1).reset_index()
        fig = px.bar(perfil, x='Cluster_nombre', y='Monetary',
                     title='Ingreso promedio por cluster',
                     color='Cluster_nombre',
                     text=perfil['Monetary'].apply(lambda x: f"£{x:,.0f}"))
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(rfm, x='Recency', y='Frequency',
                      color='Cluster_nombre', size='Monetary',
                      hover_data=['CustomerID','Monetary'],
                      title='Clusters — Recency vs Frequency')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Perfil detallado por cluster")
    st.dataframe(perfil, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════
# SECCIÓN 4 — RIESGO DE CHURN
# ══════════════════════════════════════════════════════════════════
elif seccion == "⚠️ Riesgo de Churn":
    st.title("⚠️ Riesgo de Churn")

    col1, col2, col3 = st.columns(3)
    col1.metric("Churn rate global", f"{rfm['Churn'].mean():.1%}")
    col2.metric("Clientes en churn", f"{rfm['Churn'].sum():,}")
    col3.metric("Clientes activos",  f"{(rfm['Churn']==0).sum():,}")

    st.divider()

    # Filtro por probabilidad de churn
    umbral = st.slider(
        "Mostrar clientes con probabilidad de churn mayor a:",
        min_value=0.0, max_value=1.0, value=0.5, step=0.05
    )

    df_riesgo = (rfm[(rfm['Churn'] == 0) &
                     (rfm['Churn_prob'] >= umbral)]
                 [['CustomerID','Recency','Frequency',
                   'Monetary','Cluster_nombre','Churn_prob']]
                 .sort_values('Churn_prob', ascending=False))

    st.markdown(f"**{len(df_riesgo):,} clientes activos** con probabilidad de churn ≥ {umbral:.0%}")
    st.dataframe(df_riesgo, use_container_width=True, hide_index=True)

    # Churn por segmento
    churn_seg = rfm.groupby('Segmento')['Churn'].mean().reset_index()
    churn_seg.columns = ['Segmento', 'Churn_rate']
    fig = px.bar(churn_seg.sort_values('Churn_rate', ascending=False),
                 x='Segmento', y='Churn_rate',
                 title='Tasa de Churn por segmento RFM',
                 color='Segmento',
                 text=churn_seg.sort_values('Churn_rate', ascending=False)
                 ['Churn_rate'].apply(lambda x: f"{x:.0%}"))
    fig.update_traces(textposition='outside')
    fig.update_yaxes(tickformat='.0%')
    st.plotly_chart(fig, use_container_width=True)
