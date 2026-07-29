import streamlit as st
import pandas as pd
import logging
from io import StringIO
import datetime
#hello
# 1. Configurar el sistema de logs para capturar eventos en un buffer de texto
log_buffer = StringIO()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(log_buffer)]
)

st.set_page_config(page_title="Planilla de Compras 2025", layout="wide")
st.title("📊 Procesamiento de Planilla de Compras 2025")

# 2. Generar datos ficticios de compras
@st.cache_data
def cargar_datos_ficticios():
    logging.info("Iniciando la generación de datos ficticios para el año 2025.")
    datos = {
        "Fecha": [
            datetime.date(2025, 1, 15), datetime.date(2025, 2, 20), 
            datetime.date(2025, 3, 5), datetime.date(2025, 4, 12),
            datetime.date(2025, 5, 18), datetime.date(2025, 6, 22)
        ],
        "Proveedor": ["TechCorp", "OfficeSupplies", "BuildIt Co.", "TechCorp", "CleanGreen", "OfficeSupplies"],
        "Categoría": ["Tecnología", "Oficina", "Infraestructura", "Tecnología", "Mantenimiento", "Oficina"],
        "Cantidad": [2, 10, 1, 5, 20, 50],
        "Precio_Unitario": [800.0, 15.5, 1500.0, 120.0, 30.0, 5.0]
    }
    df = pd.DataFrame(datos)
    logging.info(f"DataFrame generado exitosamente con {len(df)} registros de compras.")
    return df

# 3. Procesar y calcular totales
def calcular_planilla(df):
    logging.info("Iniciando el cálculo de los montos totales de la planilla.")
    
    # Calcular el total por fila
    df["Total_Item"] = df["Cantidad"] * df["Precio_Unitario"]
    logging.info("Cálculo de 'Total_Item' completado exitosamente para cada registro.")
    
    # Calcular métricas globales
    gasto_total = df["Total_Item"].sum()
    items_totales = df["Cantidad"].sum()
    logging.info(f"Cálculo finalizado. Gasto Total: ${gasto_total:,.2f}, Items Totales: {items_totales}.")
    
    return df, gasto_total, items_totales

# Ejecución del pipeline de datos
df_original = cargar_datos_ficticios()
df_procesado, total_gasto, total_items = calcular_planilla(df_original.copy())

# 4. Interfaz de Streamlit (Visualización)
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Gasto Total Acumulado 2025", value=f"${total_gasto:,.2f}")
with col2:
    st.metric(label="Total de Productos Comprados", value=int(total_items))

st.subheader("📋 Detalle de la Planilla Procesada")
st.dataframe(df_procesado, use_container_width=True)

# 5. Mostrar los Logs del sistema en la UI
st.subheader("🪵 Logs del Proceso de Información")
st.text_area(
    label="Historial de eventos de la aplicación",
    value=log_buffer.getvalue(),
    height=200,
    disabled=True
)
