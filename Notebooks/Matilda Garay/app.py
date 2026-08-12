# --- Importaciones ---
from pathlib import Path
import io

# Librerías de datos y UI
import pandas as pd
import streamlit as st

# --- Configuración de Streamlit ---
st.set_page_config(page_title="Resumen de compras", page_icon="📊", layout="wide")

# --- Rutas y constantes ---
BASE_DIR = Path(__file__).resolve().parents[2]
EXCEL_PATH = BASE_DIR / "plan_de_compras_2025.xlsx"

st.title("📊 Resumen del proyecto de compras")
st.caption("Dashboard generado con Streamlit a partir de la planilla del proyecto")


@st.cache_data(show_spinner=False)
def load_data(path_or_buffer) -> pd.DataFrame:
    # --- Carga y limpieza de datos ---
    df = pd.read_excel(path_or_buffer)
    df.columns = [col.strip() for col in df.columns]

    # Ensure numeric columns exist and are numeric
    numeric_cols = [
        "Monto Total Ítem Año 2025",
        "Monto Unitario Ítem",
        "Cantidad Productos",
        "Cantidad de Ítems",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    # Ensure categorical columns exist
    for col in ["Estado Proyecto", "Tipo Proyecto", "Nombre Proyecto"]:
        if col not in df.columns:
            df[col] = "Sin dato"
        else:
            df[col] = df[col].fillna("Sin dato")

    # ID Proyecto should exist for counts
    if "ID Proyecto" not in df.columns:
        df["ID Proyecto"] = df.index

    return df


def get_dataframe() -> pd.DataFrame:
    # --- Obtención del dataframe (local o subida) ---
    # Prefer local file, but allow upload as fallback
    if EXCEL_PATH.exists():
        try:
            return load_data(EXCEL_PATH)
        except Exception as e:
            st.warning(f"Error leyendo {EXCEL_PATH}: {e}")

    uploaded = st.sidebar.file_uploader("Sube el archivo Excel (si no existe local)", type=["xlsx", "xls"])
    if uploaded is None:
        st.error(f"No se encontró el archivo de datos: {EXCEL_PATH}. Sube el archivo en la barra lateral.")
        st.stop()

    # pd.read_excel accepts file-like objects
    return load_data(io.BytesIO(uploaded.read()))


df = get_dataframe()

# --- Filtros ---
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
# --- Métricas principales ---
try:
    proyectos_count = int(filtered_df["ID Proyecto"].nunique())
except Exception:
    proyectos_count = int(filtered_df.shape[0])

monto_total = float(filtered_df["Monto Total Ítem Año 2025"].sum())
items_total = int(filtered_df["Cantidad de Ítems"].sum())
publicados_count = int(
    filtered_df[filtered_df["Estado Proyecto"].str.lower().fillna("") == "publicado"]["ID Proyecto"].nunique()
)

col1.metric("Proyectos", proyectos_count)
col2.metric("Monto total", f"${monto_total:,.0f}")
col3.metric("Ítems", items_total)
col4.metric("Publicados", publicados_count)

st.subheader("1. Proyectos por estado")
# --- Visualización: proyectos por estado ---
state_summary = (
    filtered_df.groupby("Estado Proyecto")["ID Proyecto"].nunique().sort_values(ascending=False)
)
st.bar_chart(state_summary)

st.subheader("2. Monto por tipo de proyecto")
# --- Visualización: monto por tipo ---
type_summary = (
    filtered_df.groupby("Tipo Proyecto")["Monto Total Ítem Año 2025"].sum().sort_values(ascending=False)
)
st.bar_chart(type_summary)

st.subheader("3. Top 10 proyectos por monto")
# --- Tabla: top proyectos ---
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

# --- Exportar datos filtrados ---
# Descargar CSV de los datos filtrados
csv = filtered_df.to_csv(index=False, encoding="utf-8")
st.sidebar.download_button("Descargar CSV filtrado", data=csv, file_name="plan_de_compras_filtrado.csv", mime="text/csv")

# --- Mostrar datos crudos (opcional) ---
if st.checkbox("Mostrar datos crudos"):
    st.dataframe(filtered_df, use_container_width=True)

# --- Pie / Fuente ---
st.caption(f"Fuente: {EXCEL_PATH.name} (local o subido)")
