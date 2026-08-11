from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Resumen de compras", page_icon="📊", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[2]
EXCEL_PATH = BASE_DIR / "plan_de_compras_2025.xlsx"

st.title("📊 Resumen del proyecto de compras")
st.caption("Dashboard generado con Streamlit a partir de la planilla del proyecto")

if not EXCEL_PATH.exists():
    st.error(f"No se encontró el archivo de datos: {EXCEL_PATH}")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [col.strip() for col in df.columns]

    for col in ["Monto Total Ítem Año 2025", "Monto Unitario Ítem", "Cantidad Productos", "Cantidad de Ítems"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Estado Proyecto"] = df["Estado Proyecto"].fillna("Sin dato")
    df["Tipo Proyecto"] = df["Tipo Proyecto"].fillna("Sin dato")
    return df


df = load_data(EXCEL_PATH)

st.sidebar.header("Filtros")
selected_states = st.sidebar.multiselect(
    "Estado del proyecto",
    options=sorted(df["Estado Proyecto"].dropna().unique()),
    default=sorted(df["Estado Proyecto"].dropna().unique()),
)
selected_types = st.sidebar.multiselect(
    "Tipo de proyecto",
    options=sorted(df["Tipo Proyecto"].dropna().unique()),
    default=sorted(df["Tipo Proyecto"].dropna().unique()),
)

filtered_df = df.copy()
if selected_states:
    filtered_df = filtered_df[filtered_df["Estado Proyecto"].isin(selected_states)]
if selected_types:
    filtered_df = filtered_df[filtered_df["Tipo Proyecto"].isin(selected_types)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Proyectos", int(filtered_df["ID Proyecto"].nunique()))
col2.metric("Monto total", f"${filtered_df['Monto Total Ítem Año 2025'].sum():,.0f}")
col3.metric("Ítems", int(filtered_df["Cantidad de Ítems"].sum()))
col4.metric("Publicados", int(filtered_df[filtered_df["Estado Proyecto"].str.lower() == "publicado"]["ID Proyecto"].nunique()))

st.subheader("1. Proyectos por estado")
state_summary = (
    filtered_df.groupby("Estado Proyecto")["ID Proyecto"].nunique().sort_values(ascending=False)
)
st.bar_chart(state_summary)

st.subheader("2. Monto por tipo de proyecto")
type_summary = (
    filtered_df.groupby("Tipo Proyecto")["Monto Total Ítem Año 2025"].sum().sort_values(ascending=False)
)
st.bar_chart(type_summary)

st.subheader("3. Top 10 proyectos por monto")
top_projects = (
    filtered_df.groupby("Nombre Proyecto", as_index=False)
    .agg(
        Proyectos=("ID Proyecto", "nunique"),
        Monto_total=("Monto Total Ítem Año 2025", "sum"),
        Items=("Cantidad de Ítems", "sum"),
    )
    .sort_values("Monto_total", ascending=False)
    .head(10)
)
st.dataframe(top_projects, use_container_width=True)

st.caption("Archivos usados: plan_de_compras_2025.xlsx")
