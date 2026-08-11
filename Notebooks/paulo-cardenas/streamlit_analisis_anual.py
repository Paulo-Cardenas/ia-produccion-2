"""Intento de notebook interactivo con Streamlit para analizar el plan de compras por año, para el desarrollo del Analisis de Datos."""

import re
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Colores de la paleta categórica validada del proyecto (dataviz skill).
AZUL = "#2a78d6"
NARANJA = "#eb6834"
GRID = "#e1e0d9"
INK_PRIMARIO = "#0b0b0b"

MESES_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}
NOMBRES_MES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]

PATRON_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
PATRON_DMY = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
PATRON_MES_ANIO = re.compile(r"^([a-z]{3,4})\.?\s*(\d{4})$")


def _localizar_archivo(nombre_archivo: str, max_niveles: int = 5) -> Path:
    """Busca `nombre_archivo` subiendo desde el directorio de este script hasta la raíz del proyecto."""
    directorio = Path(__file__).resolve().parent
    for _ in range(max_niveles + 1):
        candidato = directorio / nombre_archivo
        if candidato.exists():
            return candidato
        directorio = directorio.parent
    raise FileNotFoundError(f"No se encontró '{nombre_archivo}' cerca de {Path(__file__)}")


def normalizar_texto(valor) -> str:
    """Minúsculas, sin tildes y sin espacios repetidos. Valores vacíos -> ''."""
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", texto)


def normalizar_fecha_individual(texto: str) -> date | None:
    """Reconoce un único valor de fecha en cualquiera de los 3 formatos del archivo."""
    texto = texto.strip()

    m = PATRON_ISO.match(texto)
    if m:
        anio, mes, dia = (int(x) for x in m.groups())
        return date(anio, mes, dia)

    m = PATRON_DMY.match(texto)
    if m:
        dia, mes, anio = (int(x) for x in m.groups())
        return date(anio, mes, dia)

    m = PATRON_MES_ANIO.match(normalizar_texto(texto))
    if m:
        mes_txt, anio = m.groups()
        mes = MESES_ES.get(mes_txt[:3])
        if mes:
            return date(int(anio), mes, 1)

    return None


def normalizar_lista_fechas(celda) -> list[date]:
    """Celda con una o varias fechas separadas por coma -> lista de `date` únicos y ordenados."""
    if pd.isna(celda):
        return []
    fechas = [normalizar_fecha_individual(p) for p in str(celda).split(",")]
    return sorted({f for f in fechas if f is not None})


def filtrar_por_anio(fechas: list[date], anio: int) -> list[date]:
    return [f for f in fechas if f.year == anio]


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    ruta_excel = _localizar_archivo("plan_de_compras_2025.xlsx")
    df = pd.read_excel(ruta_excel, sheet_name=0)

    df["Meses envío OC_norm"] = df["Meses envío OC"].apply(normalizar_lista_fechas)
    df["Meses envio OC de Arraste_norm"] = df["Meses envio OC de Arraste"].apply(normalizar_lista_fechas)

    # Todos los años que aparecen en cualquiera de las columnas de fecha del archivo,
    # para poblar el selector y los gráficos históricos.
    anios = set()
    for col in ["Meses envío OC_norm", "Meses envio OC de Arraste_norm"]:
        for lista in df[col]:
            anios.update(f.year for f in lista)
    anios.update(df["Fecha de Inicio Compra"].dropna().dt.year.tolist())
    anios.update(df["Fecha Publicación PAC 2025"].dropna().dt.year.tolist())
    df.attrs["anios_disponibles"] = sorted(anios)

    return df


def preparar_tabla_por_anio(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    """
    Filtra `df` a las filas que tienen alguna fecha de envío de OC en `anio`, y
    reemplaza las columnas de fechas por UNA sola fecha "aaaa-mm-dd" de ese año
    (nunca la mezcla original de varios años en una misma celda).
    """
    envio_anio = df["Meses envío OC_norm"].apply(lambda fechas: filtrar_por_anio(fechas, anio))
    arraste_anio = df["Meses envio OC de Arraste_norm"].apply(lambda fechas: filtrar_por_anio(fechas, anio))

    mascara = (envio_anio.apply(len) > 0) | (arraste_anio.apply(len) > 0)
    resultado = df.loc[mascara].copy()
    resultado["Mes envío OC"] = envio_anio.loc[mascara].apply(
        lambda fechas: ", ".join(f.strftime("%Y-%m-%d") for f in fechas)
    )
    resultado["Mes envío OC arrastre"] = arraste_anio.loc[mascara].apply(
        lambda fechas: ", ".join(f.strftime("%Y-%m-%d") for f in fechas)
    )
    resultado["_orden"] = envio_anio.loc[mascara].apply(lambda fechas: min(fechas) if fechas else date(anio, 12, 31))
    return resultado.sort_values("_orden").drop(columns="_orden")


st.set_page_config(page_title="Plan de Compras por Año", layout="wide")

st.title("📅 Analisis de Fechas — vista por año")
st.caption(
    "Datos normalizados de `plan_de_compras_2025.xlsx`"

)

df = cargar_datos()
anios_disponibles = df.attrs["anios_disponibles"]

st.sidebar.header("Filtro")
anio = st.sidebar.selectbox(
    "Año",
    anios_disponibles,
    index=len(anios_disponibles) - 1,
)

tabla = preparar_tabla_por_anio(df, anio)

# --- KPIs -------------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Proyectos con OC en el año", f"{len(tabla):,}".replace(",", "."))
col2.metric("Unidades de compra distintas", tabla["Unidad de Compra"].nunique())
col3.metric("Tipos de proyecto", tabla["Tipo Proyecto"].nunique())

# --- Tabla --------------------------------------------------------------
st.subheader(f"Proyectos con envío de OC en {anio}")
columnas_tabla = [
    "ID Proyecto", "Unidad de Compra", "Nombre Proyecto", "Tipo Proyecto",
    "Estado Proyecto", "Mes envío OC", "Mes envío OC arrastre",
    "Cantidad OC", "Monto Total Ítem Año 2025",
]
st.dataframe(tabla[columnas_tabla], use_container_width=True, hide_index=True)

# --- Gráfico 1: envíos de OC por mes dentro del año seleccionado -------
st.subheader(f"Envíos de OC por mes en {anio}")
meses_del_anio = [
    f.month
    for lista in df["Meses envío OC_norm"]
    for f in filtrar_por_anio(lista, anio)
]
conteo_mensual = (
    pd.Series(meses_del_anio, name="mes")
    .value_counts()
    .reindex(range(1, 13), fill_value=0)
    .sort_index()
)
fig_mensual = px.bar(
    x=NOMBRES_MES,
    y=conteo_mensual.values,
    labels={"x": "Mes", "y": "Envíos de OC"},
    color_discrete_sequence=[AZUL],
)
fig_mensual.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font_color=INK_PRIMARIO,
    xaxis=dict(gridcolor=GRID, tickfont_color=INK_PRIMARIO, title_font_color=INK_PRIMARIO),
    yaxis=dict(gridcolor=GRID, tickfont_color=INK_PRIMARIO, title_font_color=INK_PRIMARIO),
)
st.plotly_chart(fig_mensual, use_container_width=True, theme=None)

# --- Gráfico 2: top unidades de compra en el año ------------------------
st.subheader(f"Unidades de Compra con más proyectos en {anio}")
top_unidades = tabla["Unidad de Compra"].value_counts().head(10).sort_values()
fig_unidades = px.bar(
    x=top_unidades.values,
    y=top_unidades.index,
    orientation="h",
    labels={"x": "Cantidad de proyectos", "y": ""},
    color_discrete_sequence=[AZUL],
)
fig_unidades.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font_color=INK_PRIMARIO,
    xaxis=dict(gridcolor=GRID, tickfont_color=INK_PRIMARIO, title_font_color=INK_PRIMARIO),
    yaxis=dict(gridcolor=GRID, tickfont_color=INK_PRIMARIO, title_font_color=INK_PRIMARIO),
)
st.plotly_chart(fig_unidades, use_container_width=True, theme=None)

# --- Gráfico 3: evolución histórica (todos los años) ---------------------
st.subheader("Evolución histórica de proyectos con envío de OC")
conteo_por_anio = pd.Series(
    {a: sum(1 for lista in df["Meses envío OC_norm"] if filtrar_por_anio(lista, a)) for a in anios_disponibles}
)
colores_punto = [NARANJA if a == anio else AZUL for a in conteo_por_anio.index]
fig_historico = px.line(
    x=conteo_por_anio.index,
    y=conteo_por_anio.values,
    markers=True,
    labels={"x": "Año", "y": "Proyectos con OC"},
)
fig_historico.update_traces(line_color=AZUL, marker=dict(color=colores_punto, size=10))
fig_historico.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font_color=INK_PRIMARIO,
    xaxis=dict(
        gridcolor=GRID, tickfont_color=INK_PRIMARIO, title_font_color=INK_PRIMARIO,
        tickmode="linear", dtick=1,
    ),
    yaxis=dict(gridcolor=GRID, tickfont_color=INK_PRIMARIO, title_font_color=INK_PRIMARIO),
)
st.plotly_chart(fig_historico, use_container_width=True, theme=None)
st.caption(f"El punto naranjo marca el año seleccionado ({anio}).")
