import streamlit as st
import streamlit.components.v1 as components
#from ydata_profiling import ProfileReport
# accesorios
from streamlit_extras.metric_cards import style_metric_cards
from millify import millify

import pandas as pd
import plotly.express as px
import io

st.set_page_config(
    page_title="Plan de Compras",
    layout="wide"
)

# ESTILOS
with open('style/estilos.css') as f:
    css = f.read()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


st.title("📊 Análisis de Plan de Compras")

##############################################################
# SIDEBAR
##############################################################

st.sidebar.header("Configuraciones")

archivo = st.sidebar.file_uploader(
    "Seleccione archivo Excel",
    type=["xlsx", "xls"]
)

codigo_year = st.sidebar.selectbox(
    "codigo_year",
    [2025]           # modificacion codigo proceso_PC252 punto 6 JP
    # [2022, 2023, 2024, 2025],
    # index=3
)

codigo_proceso = f"PC{str(codigo_year)[-2:]}"

st.sidebar.info(f"Código proceso: {codigo_proceso}")

##############################################################
# CARGA
##############################################################

if archivo is not None:
    # barra de progreso
    progress_bar = st.progress(0)
    progress_bar.progress(10, "Cargando datos...")

    df = pd.read_excel(archivo)

    ##############################################################
    # COLUMNAS LOWERCASE
    ##############################################################

    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
    )

    ##############################################################
    # TRANSFORMACIONES
    ##############################################################
    progress_bar.progress(25, "Transformaciones...")
    codigo_proceso = "PC25"      # modificacion filtro id proyecto_PC25  punto 6 JP-
    # 1
    df = df[
        df["id proyecto"]
        .astype(str)
        .str.upper()
        .str.endswith(codigo_proceso.upper())
    ].copy()

    # 2
    df["anexo"] = (
        df["teléfono responsable"]
        .astype(str)
        .str.replace("-", "", regex=False) # ingreso numeros en columna anexo punto 4 JP-
        .str.strip()
        .str[-4:]

        # .str.split("-")
        # .str[-1]
        # .str[-4:]
    )
#----------------------------------------------------
    # 3
    df["teléfono responsable"] = (
        df["teléfono responsable"]
        .astype(str)
        .str.replace("-", "", regex=False)
        .str.replace(" ", "", regex=False)
    .str.strip()       # limpieza numeros de telefono punto 4 JP-                    
    )

    df["teléfono responsable"] = df["teléfono responsable"].str.slice(-9)
    df["teléfono responsable"] = df["teléfono responsable"].str.zfill(9)
    df["teléfono responsable"] = df["teléfono responsable"].apply(
    lambda x: "2" + x[1:] if x.startswith("0") else x
    )
#--------------------------------------------------

    # mostrar barra de progreso con un mensaje y luego desaparecer
    progress_bar.progress(60, "Modificando nombre de proyecto...")


    # -------------------------------------------------------------
    # modificar el nombre del proyecto segun el nombre de la planilla 
    # # codigos_unicos
    # ---------------------------------------------
    # transformacion de nombre de proyecto basado en codigos unicos
    codigos = pd.read_excel('codigos_unicos.xlsx')
    # Asegurar que las columnas de cruce tengan formato string sin espacios extra
    df['código presupuestario'] = df['código presupuestario'].astype(str).str.strip()
    codigos['Codigo'] = codigos['Codigo'].astype(str).str.strip()

    # Realizar el Join entre df y codigos
    df_merged = df.merge(
        codigos[['Codigo', 'Nombre']], 
        left_on='código presupuestario', 
        right_on='Codigo', 
        how='left'
    )
    # Reemplazar los valores en 'Nombre Proyecto' con el nuevo 'Nombre' obtenido del join
    # Se mantiene el valor original en caso de que no haya coincidencia
    df['nombre proyecto'] = df_merged['Nombre'].fillna(df['nombre proyecto'])

    ##############################################################
    # HEADER TARJETAS
    ##############################################################

    total_registros = len(df)

    monto_total = df["monto total ítem año 2025"].sum()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total registros",
        f"{total_registros:,}",
        delta="30",
    )

    c2.metric(
        "Monto Total",
       millify(monto_total, precision=2),
       delta=millify(monto_total - 1000000, precision=2)
    )

    c3.metric(
        "Monto promedio",
        millify(df["monto total ítem año 2025"].mean(), precision=2),
        delta="-50"
    )
    c4.metric(
        "Valor máximo",
        millify(df["monto total ítem año 2025"].max(), precision=2)
    )

    style_metric_cards()

    st.divider()

    ##############################################################
    # ANALISIS EXPLORATORIO
    ##############################################################
    progress_bar.progress(80, "Análisis Exploratorio...")

    st.header("Análisis Exploratorio")

    # walker = pyg.walk(df) # exploración de datos esilo Tableau

    st.dataframe(df.head(500), use_container_width=True)

    nulos = pd.DataFrame({

        "Columna": df.columns,

        "Nulos": df.isnull().sum().values,

        "Porcentaje": (
            df.isnull().mean()*100
        ).round(2)

    })

    st.dataframe(nulos, use_container_width=True)


    columna_eliminar = (
        nulos
        .sort_values("Nulos", ascending=False)
        .iloc[0]["Columna"]
    )

    st.warning(
        f"Se propone eliminar la columna **{columna_eliminar}** "
        "por ser la que posee más valores nulos."
    )

    eliminar = st.radio(
        "¿Desea eliminarla?",
        ["NO", "SI"],
        horizontal=True
    )

    if eliminar == "SI":
        df = df.drop(columns=[columna_eliminar])
        st.success("Columna eliminada.")

    ##############################################################
    # TABLAS RESUMEN
    ##############################################################
    progress_bar.progress(90, "Generando resúmenes...")
    
    st.header("Resúmenes")

    resumen1 = (
        df.groupby("nombre responsable", as_index=False)
        ["monto total ítem año 2025"]
        .sum()
        .sort_values(
            "monto total ítem año 2025",
            ascending=False
        ).head(10)
    )

    resumen2 = (
        df[
            [
                "nombre ítem",
                "nombre responsable",
                "monto unitario ítem"
            ]
        ]
        .sort_values(
            "monto unitario ítem",
            ascending=False
        )
        .head(6)
    )

    resumen3 = (
        df
        .groupby("nombre ítem", as_index=False)
        .agg({
            "monto unitario ítem":"sum"
        })
        .sort_values(
            "monto unitario ítem",
            ascending=True
        ).head(10)
    )

    st.subheader("Monto por Responsable")
    st.dataframe(resumen1, use_container_width=True)

    st.subheader("10 Ítems más caros")
    st.dataframe(resumen2, use_container_width=True)

    st.subheader("Ítems más comprados")
    st.dataframe(resumen3, use_container_width=True)

    ##############################################################
    # GRAFICOS
    ##############################################################

    st.header("Gráficos")

    fig1 = px.bar(
        resumen1,
        x="nombre responsable",
        y="monto total ítem año 2025",
        title="Monto Total por Responsable"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    fig2 = px.bar(
        resumen2,
        x="nombre ítem",
        y="monto unitario ítem",
        color="nombre responsable",
        title="10 Ítems más caros"
    )
    fig2.update_layout(height=600)
    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    fig3 = px.bar(
        resumen3,
        x="monto unitario ítem",
        y="nombre ítem",
        title="Ítems más comprados",
        orientation="h",
        color="monto unitario ítem",
    )
    fig3.update_layout(height=600)
    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    progress_bar.empty()

    ##############################################################
    # DESCARGA ARCHIV
    ##############################################################
    output_bytes = io.BytesIO()
    with pd.ExcelWriter(output_bytes, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="Descargar Excel procesado",
        data=output_bytes.getvalue(),
        file_name="plan_de_compras_2025_procesado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("Por favor, suba un archivo Excel para comenzar el análisis.")