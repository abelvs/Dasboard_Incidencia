import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit.components.v1 import html
from pathlib import Path
import branca.colormap as cm


BASE_DIR = Path(__file__).resolve().parent.parent
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

def cargar_datos():
    ## Cargar df de incidencia municipal procesado y el shapefile municipal ##
    df = pd.read_parquet(BASE_DIR / "01_datos/processed/Municipal-Delitos.parquet")
    gdf = gpd.read_file(BASE_DIR /"01_datos/processed/00mun_simplificado.geojson")
    gdf = gdf.rename(columns={'CVEGEO':'cve_municipio'})
    return df, gdf

df, gdf = cargar_datos()

@st.cache_resource
def crear_mapa(subtipo, fecha_inicio, fecha_fin):
    ## Filtrar datos ##
    df_filtrado = df[
        (df["subtipo_de_delito"] == subtipo) & 
        (df["fecha"] >= pd.to_datetime(fecha_inicio)) &
        (df["fecha"] <= pd.to_datetime(fecha_fin)) 
    ]
    
    ## Agregar totales por municipio ##
    df_agrupado = df_filtrado.groupby('cve_municipio', observed=False)['total'].sum().reset_index()
    
    ## Unir a geometría municipal ##
    gdf_mapa = gdf.merge(df_agrupado, on='cve_municipio', how='left').fillna(0)
    
    ## Paleta dinámica de color ##
    vmin = gdf_mapa["total"].min()
    vmax = gdf_mapa["total"].max()
    indices = [vmin, vmax*0.2, vmax*0.4, vmax*0.6, vmax*0.8, vmax]
    colores = ["#000000", "#330000", "#660000", "#990000", "#cc0000", "#ff0000"]
    
    colormap = cm.LinearColormap(
        colors=colores,
        index=indices,
        vmin=vmin,
        vmax=vmax
    )
    colormap.caption = "Total"
    
    ## Mapa interactivo ##
    gdf_proj = gdf_mapa.to_crs("EPSG:3857")
    centro = [gdf_mapa.geometry.centroid.y.mean(), gdf_mapa.geometry.centroid.x.mean()]
    m = folium.Map(
        location=centro, 
        zoom_start=5.4, 
        tiles="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_nolabels/{z}/{x}/{y}.png",
        attr="&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors &copy; <a href=\"https://carto.com/attributions\">CARTO</a>"
    )
    
    folium.GeoJson(
        gdf_mapa,
        style_function=lambda x: {
            "fillColor": colormap(x['properties']['total']),
            "color": "grey50",
            "weight": 0.3,
            # Menos opacos los medios, solo los más bajos muy opacos
            "fillOpacity": (
                0.2 if x['properties']['total'] <= vmax*0.2 else
                0.45 if x['properties']['total'] <= vmax*0.4 else
                0.6 if x['properties']['total'] <= vmax*0.6 else
                0.75 if x['properties']['total'] <= vmax*0.8 else
                0.85
            ),
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NOMGEO","total"],
            aliases=["Municipio:","Total delitos:"]
        )
    ).add_to(m)
    
    return m, len(df_filtrado)

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

# --- Crear y renderizar mapa ---
m, num_registros = crear_mapa(selected_subtipo, rango_fechas[0], rango_fechas[1])

html(
    f"""
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
        }}
    </style>
    <div style="position: fixed; top: 0; left: 0; width: 110%; height: 100vh; z-index: 1;">
        {m._repr_html_()}
    </div>
    """,
    height=800
)

st.markdown(f"Mostrando {num_registros} registros filtrados.")


