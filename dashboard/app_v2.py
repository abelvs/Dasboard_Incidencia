import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit.components.v1 import html
from pathlib import Path
import branca.colormap as cm


BASE_DIR = Path(__file__).resolve().parent.parent

def cargar_datos():
    ## Cargar df de incidencia municipal procesado y el shapefile municipal ##
    df = pd.read_parquet(BASE_DIR / "01_datos/processed/Municipal-Delitos.parquet")
    gdf = gpd.read_file(BASE_DIR /"01_datos/raw/mg_2025_integrado/conjunto_de_datos/00mun.shp")
    gdf = gdf.to_crs(epsg=4326)
    gdf = gdf.rename(columns={'CVEGEO':'cve_municipio'})
    return df, gdf

df, gdf = cargar_datos()

gdf["geometry"] = gdf.geometry.simplify(tolerance=0.005, preserve_topology=True)


## Sidebar de filtros ##
subtipos = df['subtipo_de_delito'].cat.categories.tolist()
selected_subtipo = st.sidebar.selectbox(
    "Subtipo de delito", 
    subtipos,
    index=subtipos.index("Homicidio doloso"))

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    [pd.to_datetime("2024-01-01"), pd.to_datetime("2024-12-31")]
)

## Filtrar datos ##

df_filtrado = df[
    (df["subtipo_de_delito"] == selected_subtipo) & 
    (df["fecha"] >= pd.to_datetime(rango_fechas[0])) &
    (df["fecha"] <= pd.to_datetime(rango_fechas[1])) 
]

## Agregar totales por municipio ##
df_agrupado = df_filtrado.groupby('cve_municipio')['total'].sum().reset_index()


## Unir a geometría municipal ##
gdf_mapa = gdf.merge(df_agrupado, on = 'cve_municipio', how = 'left').fillna(0)


## Paleta dinámica de color ##
colormap = cm.LinearColormap(
    colors=["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
    vmin=gdf_mapa["total"].min(),
    vmax=gdf_mapa["total"].max()
)
colormap.caption = "Total delitos"

## Mapa interactivo ##
centro = [gdf_mapa.geometry.centroid.y.mean(), gdf_mapa.geometry.centroid.x.mean()]
m = folium.Map(location=centro, zoom_start=6, tiles="cartodbdark_matter")

folium.GeoJson(
    gdf_mapa,
    style_function=lambda x: {
        "fillColor": colormap(x['properties']['total']),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["NOMGEO","total"],
        aliases=["Municipio:","Total delitos:"]
    )
).add_to(m)

# --- Renderizar en Streamlit ---
html(m._repr_html_(), width=2500, height=2200)

st.markdown(f"Mostrando {len(df_filtrado)} registros filtrados.")


