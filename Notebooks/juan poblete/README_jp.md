
# actividades

## crear una xarpeta notebook ipynb
en una carpeta "notebooks"

### actividades
- cargar planilla de compras 2025
## 1
- realizar  EDA
## 2
- tablas de resumen
## 3
- graficos de resumen

## 4
- Limpieza de columnas de telefono   archivo juan_poblete-telefono_anexo.ipynb

Transformacion titulos columnas a minusculas y sin espacios
Filtra ID Propyecto PC25
Limpiar numeros de Telefonos 9 digitos
Tomar ultimos 4 digitos del nuemro tefonico y agregarlos a la comuna de anexo
Validar informacion


## 5
- analisis de fechas

## 6
Achivo juan_poblete_id_proyecto_pc25.ipynb
-filtrar por codigo proyecto segun año (ultimos 3 digitos es el año) PC25. filtrar solo mostrar año 25.

Validacion Nombres y cantidades de columnas (conservar o eliminar)
Transformacion titulos columnas a minusculas y sin espacios
Filtra ID Propyecto PC25



Ejecuta en terminal
```bash
streamlit run jp.py   # visualiza cambios codigo_year _codigo PC25
                      # Carga archivo plan_de_compras_2025.xlsx
                      # columna id proyecto solo muestra PC25
                      # Columna telefono responsable numeros 9 digitos
                      # Muestra en columna anexo muestra solo los ultimos 4 digitos correspondientes al anexo de cada numero de telefono