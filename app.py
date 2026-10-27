# ============================================================
# OBSERVATORIO ECONOMICO Y SOCIAL DE NARINO
# Version enriquecida - Streamlit
# Datos 100% reales - CERO sinteticos
# Fuentes: datos.gov.co (SODA), MinDefensa, DNP
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import unicodedata
import warnings
from io import StringIO

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Observatorio Económico y Social | Nariño",
    page_icon="🇨🇴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos
st.markdown("""
<style>
    .main-title { font-size: 2.1rem; font-weight: 800; color: #1a365d; margin-bottom: 0.1rem; }
    .sub-title { font-size: 1.05rem; color: #4a5568; margin-bottom: 1.2rem; }
    .diag-box { background: #ebf8ff; border-left: 5px solid #3182ce; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
    .stMetric { background: #f7fafc; padding: 10px 14px; border-radius: 10px; border: 1px solid #e2e8f0; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# NORMALIZACIÓN
# ------------------------------------------------------------
def quitar_tildes(texto):
    if pd.isna(texto) or texto is None:
        return ""
    t = str(texto).strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return t.replace(",", "").replace(".", " ").replace("  ", " ").strip()

DEPARTAMENTOS_CANONICOS = {
    "amazonas": "Amazonas", "antioquia": "Antioquia", "arauca": "Arauca",
    "atlantico": "Atlántico", "bogota": "Bogotá D.C.", "bogota d c": "Bogotá D.C.",
    "bogota dc": "Bogotá D.C.", "bolivar": "Bolívar", "boyaca": "Boyacá",
    "caldas": "Caldas", "caqueta": "Caquetá", "casanare": "Casanare",
    "cauca": "Cauca", "cesar": "Cesar", "choco": "Chocó", "cordoba": "Córdoba",
    "cundinamarca": "Cundinamarca", "guainia": "Guainía", "guaviare": "Guaviare",
    "huila": "Huila", "la guajira": "La Guajira", "magdalena": "Magdalena",
    "meta": "Meta", "narino": "Nariño", "norte de santander": "Norte de Santander",
    "putumayo": "Putumayo", "quindio": "Quindío", "risaralda": "Risaralda",
    "san andres": "San Andrés y Providencia", "san andres y providencia": "San Andrés y Providencia",
    "archipielago de san andres": "San Andrés y Providencia", "santander": "Santander",
    "sucre": "Sucre", "tolima": "Tolima", "valle": "Valle del Cauca",
    "valle del cauca": "Valle del Cauca", "vaupes": "Vaupés", "vichada": "Vichada",
}

def normalizar_departamento(nombre):
    clave = quitar_tildes(nombre)
    return DEPARTAMENTOS_CANONICOS.get(clave, str(nombre).strip().title() if nombre else None)

# ------------------------------------------------------------
# CARGA DE DATOS
# ------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Descargando PIB departamental...")
def cargar_pib():
    try:
        url = "https://www.datos.gov.co/resource/kgyi-qc7j.json?$limit=50000&$order=a_o DESC"
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["anio"] = pd.to_numeric(df["a_o"], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor_miles_de_millones_de"], errors="coerce")
        df["departamento"] = df["departamento"].apply(normalizar_departamento)
        df = df[df["tipo_de_precios"].str.contains("constantes", case=False, na=False)]
        agg = df.groupby(["departamento", "anio"], as_index=False)["valor"].sum().dropna()
        agg["indicador"] = "PIB (miles de millones, constantes 2015)"
        agg["categoria"] = "Crecimiento / PIB"
        agg["fuente"] = "datos.gov.co/kgyi-qc7j (DANE)"
        return agg
    except Exception as e:
        st.sidebar.warning(f"PIB no disponible: {str(e)[:60]}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner="Descargando homicidios...")
def cargar_homicidios():
    try:
        url = "https://www.datos.gov.co/resource/m8fd-ahd9.json?$limit=150000"
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["fecha"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
        df["anio"] = df["fecha"].dt.year
        df["departamento"] = df["departamento"].apply(normalizar_departamento)
        df["cantidad"] = pd.to_numeric(df.get("cantidad"), errors="coerce").fillna(1)
        agg = df.groupby(["departamento", "anio"], as_index=False)["cantidad"].sum().rename(columns={"cantidad": "valor"}).dropna()
        agg = agg[(agg["anio"] >= 2010) & (agg["anio"] <= 2026)]
        agg["indicador"] = "Homicidios (víctimas)"
        agg["categoria"] = "Seguridad ciudadana"
        agg["fuente"] = "MinDefensa/m8fd-ahd9"
        return agg
    except Exception as e:
        st.sidebar.warning(f"Homicidios no disponible: {str(e)[:60]}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner="Descargando violencia intrafamiliar...")
def cargar_violencia_intrafamiliar():
    try:
        url = "https://www.datos.gov.co/resource/gepp-dxcs.json?$limit=150000"
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["fecha"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
        df["anio"] = df["fecha"].dt.year
        df["departamento"] = df["departamento"].apply(normalizar_departamento)
        df["cantidad"] = pd.to_numeric(df.get("cantidad"), errors="coerce").fillna(1)
        agg = df.groupby(["departamento", "anio"], as_index=False)["cantidad"].sum().rename(columns={"cantidad": "valor"}).dropna()
        agg = agg[(agg["anio"] >= 2010) & (agg["anio"] <= 2026)]
        agg["indicador"] = "Violencia intrafamiliar (víctimas)"
        agg["categoria"] = "Seguridad ciudadana"
        agg["fuente"] = "MinDefensa/gepp-dxcs"
        return agg
    except Exception as e:
        st.sidebar.warning(f"Violencia intrafamiliar no disponible: {str(e)[:60]}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner="Descargando recursos DNP...")
def cargar_dnp():
    try:
        url = "https://www.datos.gov.co/resource/wc86-9j4a.json?$limit=80000"
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["departamento"] = df["departamento"].apply(normalizar_departamento)
        df["anio"] = pd.to_numeric(df.get("vigencia"), errors="coerce")
        valor_col = next((c for c in ["valorpagado", "valorobligado", "valorcomprometido"] if c in df.columns), None)
        if not valor_col:
            return pd.DataFrame()
        df["valor"] = pd.to_numeric(df[valor_col], errors="coerce")
        agg = df.groupby(["departamento", "anio"], as_index=False)["valor"].sum().dropna()
        agg = agg[(agg["anio"] >= 2010) & (agg["anio"] <= 2026)]
        agg["indicador"] = "Recursos públicos DNP (COP)"
        agg["categoria"] = "Finanzas públicas"
        agg["fuente"] = "DNP/wc86-9j4a"
        return agg
    except Exception as e:
        st.sidebar.warning(f"DNP no disponible: {str(e)[:60]}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def construir_maestro():
    partes = []
    for fn in [cargar_pib, cargar_homicidios, cargar_violencia_intrafamiliar, cargar_dnp]:
        d = fn()
        if not d.empty:
            partes.append(d)
    if not partes:
        return pd.DataFrame(columns=["departamento", "anio", "valor", "indicador", "categoria", "fuente"])
    maestro = pd.concat(partes, ignore_index=True)
    maestro["anio"] = maestro["anio"].astype(int)
    return maestro.sort_values(["indicador", "departamento", "anio"]).reset_index(drop=True)

# ------------------------------------------------------------
# ANÁLISIS
# ------------------------------------------------------------
def filtrar(df, deptos, indicador, anio_min, anio_max):
    d = df.copy()
    if deptos and "Todos" not in deptos:
        d = d[d["departamento"].isin(deptos)]
    if indicador and indicador != "Todos":
        d = d[d["indicador"] == indicador]
    return d[(d["anio"] >= anio_min) & (d["anio"] <= anio_max)]

def calcular_crecimiento(serie):
    if len(serie) < 2:
        return None
    ant, act = serie.iloc[-2], serie.iloc[-1]
    return ((act - ant) / ant * 100) if ant != 0 else None

def obtener_kpis_narino(df):
    resultados = []
    if df.empty or "Nariño" not in df["departamento"].values:
        return resultados
    for ind in df["indicador"].unique():
        d = df[df["indicador"] == ind]
        ultimo = d["anio"].max()
        d_ult = d[d["anio"] == ultimo]
        nar = d_ult[d_ult["departamento"] == "Nariño"]
        if nar.empty:
            continue
        valor_nar = float(nar["valor"].iloc[0])
        promedio = float(d_ult["valor"].mean())
        ranking = int((d_ult["valor"] > valor_nar).sum() + 1)
        total = int(d_ult["departamento"].nunique())
        serie_nar = d[d["departamento"] == "Nariño"].sort_values("anio")["valor"]
        crec = calcular_crecimiento(serie_nar)
        resultados.append({
            "indicador": ind, "anio": ultimo, "valor_narino": valor_nar,
            "promedio_nacional": promedio, "ranking": ranking, "total_deptos": total,
            "crecimiento_pct": crec,
            "diferencia_vs_promedio_pct": ((valor_nar - promedio) / promedio * 100) if promedio else None
        })
    return resultados

def generar_diagnostico(kpis):
    if not kpis:
        return "No hay suficientes datos de Nariño para generar un diagnóstico automático."
    lineas = ["**Diagnóstico automático de Nariño** (basado en el último año disponible):\n"]
    for k in kpis:
        nombre = k["indicador"].split("(")[0].strip()
        pos = f"posición {k['ranking']} de {k['total_deptos']}"
        crec = f"{k['crecimiento_pct']:+.1f}% respecto al año anterior" if k["crecimiento_pct"] is not None else "sin dato de variación"
        diff = k["diferencia_vs_promedio_pct"]
        if diff is not None:
            if diff > 10:
                comparacion = f"está **por encima** del promedio nacional (+{diff:.1f}%)"
            elif diff < -10:
                comparacion = f"está **por debajo** del promedio nacional ({diff:.1f}%)"
            else:
                comparacion = f"se encuentra **cerca** del promedio nacional ({diff:+.1f}%)"
        else:
            comparacion = "sin comparación disponible"
        lineas.append(f"- **{nombre}**: {pos}. {comparacion}. Variación: {crec}.")
    lineas.append("\n*Este texto se genera automáticamente a partir de los datos oficiales cargados.*")
    return "\n".join(lineas)

# ------------------------------------------------------------
# INTERFAZ
# ------------------------------------------------------------
st.markdown('<p class="main-title">🇨🇴 Observatorio Económico y Social de Nariño</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Prototipo comparativo - Datos oficiales en tiempo real - Cero datos sintéticos</p>', unsafe_allow_html=True)

with st.spinner("Cargando datos oficiales desde portales del Estado colombiano..."):
    DF = construir_maestro()

if DF.empty:
    st.error("⚠️ No se pudieron cargar datos de ninguna fuente oficial. Las APIs pueden estar temporalmente no disponibles. Intenta más tarde.")
    st.stop()

lista_deptos = sorted(DF["departamento"].dropna().unique().tolist())
lista_inds = ["Todos"] + sorted(DF["indicador"].unique().tolist())
amin, amax = int(DF["anio"].min()), int(DF["anio"].max())

# SIDEBAR
with st.sidebar:
    st.header("🔍 Filtros")
    st.markdown("---")
    default_deptos = ["Nariño"] if "Nariño" in lista_deptos else lista_deptos[:1]
    deptos_sel = st.multiselect("Departamento(s)", ["Todos"] + lista_deptos, default=default_deptos)
    ind_sel = st.selectbox("Indicador", lista_inds, index=1 if len(lista_inds) > 1 else 0)
    st.markdown("**Rango de años**")
    c1, c2 = st.columns(2)
    with c1:
        anio_min = st.number_input("Desde", amin, amax, max(amin, amax-10), 1)
    with c2:
        anio_max = st.number_input("Hasta", amin, amax, amax, 1)
    anio_barras = st.slider("Año ranking", amin, amax, amax, 1)
    st.markdown("---")
    st.markdown("**Fuentes activas**")
    for ind, g in DF.groupby("indicador"):
        st.caption(f"• {ind.split('(')[0].strip()}: {g['anio'].min()}-{g['anio'].max()}")
    st.markdown("---")
    st.success("📌 Regla antialucinación activa\nSolo datos reales de datos.gov.co, MinDefensa y DNP.")

df_filtrado = filtrar(DF, deptos_sel, ind_sel, anio_min, anio_max)

# NARIÑO EN CIFRAS
st.subheader("📍 Nariño en cifras (último año disponible)")
kpis_nar = obtener_kpis_narino(DF)

if kpis_nar:
    cols = st.columns(min(4, len(kpis_nar)))
    for i, k in enumerate(kpis_nar):
        with cols[i % 4]:
            delta = f"{k['crecimiento_pct']:+.1f}% vs año ant." if k["crecimiento_pct"] is not None else None
            st.metric(
                label=f"{k['indicador'].split('(')[0].strip()} ({k['anio']})",
                value=f"{k['valor_narino']:,.0f}" if k['valor_narino'] >= 100 else f"{k['valor_narino']:,.2f}",
                delta=delta,
                help=f"Ranking: {k['ranking']}/{k['total_deptos']} | Promedio nac.: {k['promedio_nacional']:,.0f}"
            )
else:
    st.warning("No se encontraron datos de Nariño.")

# DIAGNÓSTICO AUTOMÁTICO
if kpis_nar:
    st.markdown(f'<div class="diag-box">{generar_diagnostico(kpis_nar)}</div>', unsafe_allow_html=True)

st.markdown("---")

# PESTAÑAS
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Tendencias", "📊 Ranking nacional", "🔬 Estadística", "📁 Datos y CSV", "ℹ️ Fuentes"
])

with tab1:
    st.subheader("Evolución temporal")
    if df_filtrado.empty:
        st.warning("Sin datos para los filtros actuales.")
    else:
        if ind_sel == "Todos":
            for ind in sorted(df_filtrado["indicador"].unique()):
                d_ind = df_filtrado[df_filtrado["indicador"] == ind]
                fig = px.line(d_ind, x="anio", y="valor", color="departamento", markers=True,
                              title=f"Tendencia - {ind}", template="plotly_white")
                fig.update_layout(hovermode="x unified", height=400, legend=dict(orientation="h", y=-0.25))
                st.plotly_chart(fig, use_container_width=True)
        else:
            fig = px.line(df_filtrado, x="anio", y="valor", color="departamento", markers=True,
                          title=f"Tendencia - {ind_sel}", template="plotly_white")
            fig.update_layout(hovermode="x unified", height=480, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"Ranking nacional - {anio_barras}")
    ind_b = ind_sel if ind_sel != "Todos" else (lista_inds[1] if len(lista_inds) > 1 else ind_sel)
    d_bar = DF[(DF["indicador"] == ind_b) & (DF["anio"] == anio_barras)].copy()
    if d_bar.empty:
        st.warning("Sin datos para este año/indicador.")
    else:
        d_bar = d_bar.nlargest(18, "valor").sort_values("valor", ascending=True)
        colors = ["#e53e3e" if d == "Nariño" else "#2b6cb0" for d in d_bar["departamento"]]
        fig = go.Figure(go.Bar(
            x=d_bar["valor"], y=d_bar["departamento"], orientation="h",
            marker_color=colors, text=[f"{v:,.0f}" for v in d_bar["valor"]], textposition="outside"
        ))
        fig.update_layout(title=f"Top departamentos - {ind_b} ({anio_barras})",
                          template="plotly_white", height=520, xaxis_title="Valor", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔴 Nariño  -  🔵 Resto de departamentos")

with tab3:
    st.subheader("Estadística descriptiva")
    if df_filtrado.empty:
        st.warning("Sin datos.")
    else:
        res = (df_filtrado.groupby("indicador")["valor"]
               .agg(n="count", media="mean", mediana="median", std="std",
                    min="min", max="max", p25=lambda x: x.quantile(0.25), p75=lambda x: x.quantile(0.75))
               .round(2).reset_index())
        st.dataframe(res, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Visor de datos")
    st.markdown(f"**{len(df_filtrado):,}** registros filtrados (máx. 1.000 visibles)")
    st.dataframe(df_filtrado.head(1000), use_container_width=True, hide_index=True)
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV filtrado", csv,
                       f"observatorio_narino_{anio_min}_{anio_max}.csv", "text/csv")

with tab5:
    st.subheader("Fuentes oficiales y metodología")
    st.markdown("""
**Regla antialucinación:** Este observatorio no usa datos sintéticos ni `np.random`.  
Toda la información se obtiene de portales oficiales del Estado.

| Indicador | Categoría | Fuente | ID SODA |
|-----------|-----------|--------|---------|
| PIB (constantes 2015) | Crecimiento / PIB | DANE | kgyi-qc7j |
| Homicidios | Seguridad ciudadana | MinDefensa | m8fd-ahd9 |
| Violencia intrafamiliar | Seguridad ciudadana | MinDefensa | gepp-dxcs |
| Recursos públicos DNP | Finanzas públicas | DNP | wc86-9j4a |

**Procesamiento:** normalización de departamentos, agregación anual, filtrado de precios constantes, manejo de valores faltantes.
""")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#718096;font-size:0.85rem;'><b>Observatorio Económico y Social de Nariño</b><br>Datos oficiales - datos.gov.co - MinDefensa - DNP - DANE<br>Prototipo académico - Cero datos sintéticos</div>", unsafe_allow_html=True)
