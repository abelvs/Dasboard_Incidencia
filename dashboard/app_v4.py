from dash import Dash, html, dcc, Input, Output
from keplergl import KeplerGl
import pandas as pd
import geopandas as gpd
from pathlib import Path
import warnings
import json
import os
from tempfile import gettempdir
import matplotlib.pyplot as plt
import matplotlib


warnings.filterwarnings("ignore", category=UserWarning)


BASE_DIR = Path(__file__).resolve().parent.parent

# Variable global para almacenar el estado del mapa
map_state = {
    'bearing': 0,
    'dragRotate': True,
    'latitude': 23.6345,
    'longitude': -102.5528,
    'pitch': 0,
    'zoom': 4.9
}

def cargar_datos():
    ## Cargar df de incidencia municipal procesado y el shapefile municipal ##
    df = pd.read_parquet(BASE_DIR / "01_datos/processed/Municipal-Delitos.parquet")
    gdf = gpd.read_file(BASE_DIR /"01_datos/processed/00mun_simplificado.geojson")
    gdf = gdf.rename(columns={'CVEGEO':'cve_municipio'})
    return df, gdf

df, gdf = cargar_datos()

## Inicialización de dash ##
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H2(
            "Incidencia Municipal",
            style={
                'color': "#DBDBDB",
                'fontFamily': 'Courier New, Courier, monospace',
                'marginBottom': '30px',
                'marginTop': '10px',
                'fontWeight': 'bold',
                'fontSize': '2.2rem',
                'letterSpacing': '1px',
                'textAlign': 'left'
            }
        ),
        html.Label("Tipo de delito:", style={
            'color': '#E0E0E0',
            'fontFamily': 'Courier New, Courier, monospace',
            'fontWeight': 'bold',
            'fontSize': '1.1rem',
            'marginBottom': '5px'
        }),
        dcc.Dropdown(
            id='dropdown_subtipo',
            options=[{'label': s, 'value': s} for s in df['subtipo_de_delito'].cat.categories],
            value='Homicidio doloso',
            style={
                'backgroundColor': "#E0E0E0",
                'color': "#303030",
                'border': 'none',
                'fontFamily': 'Courier New, Courier, monospace',
                'marginBottom': '20px'
            }
        ),
        html.Label("Rango de fechas:", style={
            'color': '#E0E0E0',
            'fontFamily': 'Courier New, Courier, monospace',
            'fontWeight': 'bold',
            'fontSize': '1.1rem',
            'marginBottom': '5px'
        }),
        dcc.DatePickerRange(
            id='rango_fechas',
            start_date=pd.to_datetime("2024-01-01"),
            end_date=pd.to_datetime("2024-12-31"),
            display_format='YYYY-MM',
            style={
                'backgroundColor': '#23272b',
                'color': '#f8f8f2',
                'border': 'none',
                'fontFamily': 'Courier New, Courier, monospace',
                'marginBottom': '30px'
            }
        ),
        html.Div(
            "Desarrollado por @Abel_vs con datos del SESNSP",
            style={
                'color': '#888',
                'fontFamily': 'Courier New, Courier, monospace',
                'fontSize': '0.9rem',
                'marginTop': '670px',
                'textAlign': 'left'
            }
        )
    ], style={
        'width': '20%',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'padding': '30px 20px 10px 30px',
        'fontFamily': 'Courier New, Courier, monospace',
        'backgroundColor': '#23272b',
        'color': '#f8f8f2',
        'textAlign': 'left',
        'height': '100vh',
        'boxShadow': '2px 0 8px #1112',
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'zIndex': 10
    }),
    html.Div([
        html.Iframe(
            id='kepler_map',
            srcDoc="",
            width="96%",
            height="980vh",
            style={
                'border': '2px solid #23272b',
                'borderRadius': '8px',
                'boxShadow': '0 2px 16px #000a',
                'marginTop': '0',
                'marginBottom': '0'
            }
        )
    ], style={
        'width': '80%',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'padding': '10px 30px 10px 10px',
        'fontFamily': 'Courier New, Courier, monospace',
        'backgroundColor': '#181818',
        'color': '#f8f8f2',
        'textAlign': 'right',
        'height': '100vh',
        'marginLeft': '20%',
        'boxSizing': 'border-box'
    }),
    html.Div(
        id='resumen',
        style={
            'padding': '10px 30px',
            'fontFamily': 'Courier New, Courier, monospace',
            'backgroundColor': '#181818',
            'color': "#E6E6E6",
            'fontWeight': 'bold',
            'fontSize': '1.1rem',
            'position': 'fixed',
            'bottom': 0,
            'left': '40%',
            'width': '80%',
            'zIndex': 20
        }
    )
], style={'backgroundColor': '#181818', 'height': '100vh', 'margin': '0', 'padding': '0', 'overflow': 'hidden'})

## Callbacks ##
@app.callback(
    Output('kepler_map', 'srcDoc'),
    Output('resumen', 'children'),
    Input('dropdown_subtipo', 'value'),
    Input('rango_fechas', 'start_date'),
    Input('rango_fechas', 'end_date')
)

def actualizar_mapa_y_resumen(subtipo, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    df_filtrado = df[
        (df['subtipo_de_delito'] == subtipo) &
        (df['fecha'] >= start_date) &
        (df['fecha'] <= end_date)
    ]
    df_filtrado['total'] = df_filtrado['total'].astype(float)

    df_agrupado = df_filtrado.groupby('cve_municipio')['total'].sum().reset_index()
    gdf_mapa = gdf.merge(df_agrupado, on='cve_municipio', how='left').fillna(0)
    gdf_mapa = gdf_mapa[gdf_mapa.geometry.notnull()]

    # Normalizar opacidad: 
    min_total = gdf_mapa['total'].min()
    max_total = gdf_mapa['total'].max()
    gdf_mapa['opacity'] = 0.6
    if max_total > min_total:
        mask = gdf_mapa['total'] > 0
        gdf_mapa.loc[mask, 'opacity'] = 0.2 + 0.8 * ((gdf_mapa.loc[mask, 'total'] - min_total) / (max_total - min_total))
    gdf_mapa.loc[gdf_mapa['total'] == 0, 'opacity'] = 0.0

    # Crear mapa Kepler
    mapa = KeplerGl(height=600)
    mapa.add_data(data=gdf_mapa, name="Incidencia municipal")

    # Capa de centroides como polígonos circulares con altura (base en el centroide)
    from shapely.geometry import Point
    def make_circle(center, radius, n_points=30):
        return Point(center).buffer(radius, resolution=n_points)

    # Filtrar el 5% inferior de total (excluirlos)
    total_5pct = gdf_mapa[gdf_mapa['total'] > 0]['total'].quantile(0.05)
    gdf_circles = gdf_mapa[gdf_mapa['total'] > total_5pct].copy()
    # Guardar centroide para usarlo como base
    gdf_circles['centroide'] = gdf_circles['geometry'].centroid
    gdf_circles['geometry'] = gdf_circles['centroide'].apply(lambda c: make_circle(c, 0.01))
    gdf_circles['elevation'] = gdf_circles['total'] * 100000
    gdf_circles['opacity'] = 0.8

    mapa.add_data(data=gdf_circles.drop(columns=['centroide']), name="Centroides Circulares")

    # Asignar color especial para total=0 y alfa 0.6 para todos
    n_colors = 120
    cmap = matplotlib.cm.get_cmap('seismic', n_colors-1)
    paleta = [matplotlib.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]
    colors = ['#08101d'] + paleta  # Primer color para total=0

    config = {
        'version': 'v1',
        'config': {
            'visState': {
                'layers': [
                    # Capa de polígonos
                    {
                        'id': 'municipios_layer',
                        'type': 'geojson',
                        'config': {
                            'dataId': 'Incidencia municipal',
                            'label': 'Incidencia municipal',
                            'color': [255, 0, 0],
                            'columns': {'geojson': 'geometry'},
                            'isVisible': True,
                            'visConfig': {
                                'opacity': 0.2,
                                'strokeColor': [17, 35, 49],
                                'thickness': 0.2,
                                'colorRange': {
                                    'name': 'Custom',
                                    'type': 'threshold',
                                    'category': 'Custom',
                                    'colors': colors
                                },
                                'filled': True,
                                'stroked': True
                            }
                        },
                        'visualChannels': {
                            'colorField': {'name': 'total', 'type': 'real'},
                            'colorScale': 'threshold',
                            'opacityField': {'name': 'opacity', 'type': 'real'},
                            'opacityScale': 'linear'
                        }
                    },
                    # Capa de centroides circulares como polígonos 3D
                    {
                        'id': 'centroides_circulares_layer',
                        'type': 'geojson',
                        'config': {
                            'dataId': 'Centroides Circulares',
                            'label': 'Centroides Circulares altura total',
                            'color': [0, 255, 255],
                            'columns': {'geojson': 'geometry'},
                            'isVisible': True,
                            'visConfig': {
                                'opacity': 0.8,
                                'strokeColor': [0, 0, 0],
                                'thickness': 0.1,
                                'colorRange': {
                                    'name': 'Custom',
                                    'type': 'sequential',
                                    'category': 'Custom',
                                    'colors': colors
                                },
                                'filled': True,
                                'stroked': True,
                                'enable3d': True,
                                'elevationScale': 100,
                                'height': 100
                            }
                        },
                        'visualChannels': {
                            'colorField': {'name': 'total', 'type': 'real'},
                            'colorScale': 'sequential',
                            'heightField': {'name': 'elevation', 'type': 'real'},
                            'heightScale': 'linear',
                            'opacityField': {'name': 'opacity', 'type': 'real'},
                            'opacityScale': 'linear'
                        }
                    }
                ],
                'interactionConfig': {
                    'tooltip': {
                        'fieldsToShow': {
                            'Incidencia municipal': ['cve_municipio', 'total']
                        },
                        'enabled': True
                    }
                }
            },
            'mapState': map_state,
            'mapStyle': {'styleType': 'muted_night'},
            '3dBuildingColor': [9, 17, 31],  # no-op, just for clarity
        }
    }
    # Forzar el mapa a 3D por default 
    config['config']['mapState']['pitch'] = 40
    mapa.config = config

    # Guardar HTML en archivo temporal
    temp_dir = gettempdir()
    temp_file = os.path.join(temp_dir, 'kepler_map_temp.html')
    mapa.save_to_html(file_name=temp_file)

    # Leer el archivo HTML
    with open(temp_file, 'r', encoding='utf-8') as f:
        src_doc = f.read()

    # Eliminar archivo temporal
    try:
        os.remove(temp_file)
    except:
        pass

    resumen = f"{df_filtrado['total'].sum():,.0f} casos de {subtipo} en el periodo seleccionado."

    return src_doc, resumen

## Ejecucion ##
if __name__ == "__main__":
    app.run(debug=True)
