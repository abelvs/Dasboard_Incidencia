from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

def cargar_datos():
    ## Cargar df de incidencia municipal procesado y el shapefile municipal ##
    df = pd.read_parquet(BASE_DIR / "01_datos/processed/Municipal-Delitos.parquet")
    gdf = gpd.read_file(BASE_DIR /"01_datos/processed/00mun_simplificado.geojson")
    gdf = gdf.rename(columns={'CVEGEO':'cve_municipio'})
    return df, gdf

df, gdf = cargar_datos()

print(df.head(10))

## Inicializacion de app ##
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.Div([
        ## Dropdown subtipo ##
        dcc.Dropdown(
            id='dropdown_subtipo',
            options=[{'label': s, 'value': s} for s in df['subtipo_de_delito'].cat.categories],
            value='Homicidio doloso'
        ),
        ### Selector de fecha ##
        dcc.DatePickerRange(
            id='rango_fechas',
            start_date=pd.to_datetime("2024-01-01"),
            end_date=pd.to_datetime("2024-12-31")
        ),
    ], style={'width':'20%', 'display':'inline-block', 'verticalAlign':'top', 'padding':'10px'}),
    
    html.Div([
        ## Placeholder mapa ##
        dcc.Graph(id='mapa', style={'height': '900px'})  # altura aumentada (1.5x de ~600px)
    ], style={'width':'75%', 'display':'inline-block', 'padding':'10px'}),
    
    html.Div(id='resumen', style={'padding':'10px'})
])

## Definimos los callbacks ##
@app.callback(
    Output('mapa', 'figure'),
    Output('resumen', 'children'),
    Input('dropdown_subtipo', 'value'),
    Input('rango_fechas', 'start_date'),
    Input('rango_fechas', 'end_date')
)

def actualizar_mapa_y_resumen(subtipo, start_date, end_date):

    ## Filtramos DF de incidencia ##
    df_filtrado = df[
        (df['subtipo_de_delito'] == subtipo) &
        (df['fecha'] >= pd.to_datetime(start_date)) &
        (df['fecha'] <= pd.to_datetime(end_date))
    ]

    ## Agregamos totales por municipio
    df_agrupado = (
        df_filtrado
        .groupby('cve_municipio', observed = False)['total']
        .sum()
        .reset_index()
    )

    ## Unimos a geometria ##
    gdf_mapa = gdf.merge(
        df_agrupado,
        on = 'cve_municipio',
        how="left"
    ).fillna(0)

    ## Creamos fig plotly ##
    fig = px.choropleth_mapbox(
        gdf_mapa,
        geojson=gdf_mapa.set_index('cve_municipio').__geo_interface__,  # <-- fix: index by 'cve_municipio'
        locations='cve_municipio',
        color='total',
        hover_name='NOMGEO',
        hover_data={'total': True},
        mapbox_style="carto-darkmatter",
        center={"lat": 23, "lon": -102},
        zoom=5
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color="#f2f2f2")  # Opcional: contorno claro

    ## Resumen texto ##
    num_registros = df_filtrado['total'].sum()
    resumen = f"{num_registros:,} casos de {subtipo} en el periodo seleccionado."

    return fig, resumen


## Ejecución ##

if __name__ == "__main__":
    app.run(debug=True)

