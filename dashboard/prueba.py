from pathlib import Path
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent.parent

def cargar_datos():
    ## Cargar df de incidencia municipal procesado y el shapefile municipal ##
    df = pd.read_parquet(BASE_DIR / "01_datos/processed/Municipal-Delitos.parquet")
    gdf = gpd.read_file(BASE_DIR /"01_datos/raw/mg_2025_integrado/conjunto_de_datos/00mun.shp")
    gdf = gdf.to_crs(epsg=4326)
    return df, gdf

df, gdf = cargar_datos()

print(gdf.head(10))



## Sidebar de filtros ##
subtipos = df['subtipo_de_delito'].cat.categories.tolist()
selected_subtipo = st.sidebar.selectbox("Subtipo de delito", subtipos)

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    [df['fecha'].min(), df['fecha'].max()]
)

## Filtrar datos ##

selected_subtipo = "Homicidio doloso"

# Definir rango de fechas como todo 2024
fecha_inicio = pd.to_datetime("2024-01-01")
fecha_fin   = pd.to_datetime("2024-12-31")
rango_fechas = [fecha_inicio, fecha_fin]


df_filtrado = df[
    (df["subtipo_de_delito"] == selected_subtipo) & 
    (df["fecha"] >=  pd.to_datetime(rango_fechas[0])) &
    (df["fecha"] <= pd.to_datetime(rango_fechas[1])) 
]

## Agregar totales por municipio ##
df_agrupado = df_filtrado.groupby('cve_municipio')['total'].sum().reset_index()


## Unir a geometría municipal ##
gdf = gdf.rename(columns={'CVEGEO':'cve_municipio'})
gdf_mapa = gdf.merge(df_agrupado, on = 'cve_municipio', how = 'left').fillna(0)

print(df_filtrado.head(10))

