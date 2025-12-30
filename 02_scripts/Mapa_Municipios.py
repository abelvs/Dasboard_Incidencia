import geopandas as gpd
import folium

gdf = gpd.read_file('01_datos/raw/mg_2025_integrado/conjunto_de_datos/00mun.shp')

gdf = gdf.to_crs(epsg=4326)

gdf["geometry"] = gdf.geometry.simplify(tolerance=0.001, preserve_topology=True)


print(gdf.head())
print(gdf.columns)
print(gdf.geometry.type.value_counts())
print(gdf.crs)


centro = [
    gdf.geometry.centroid.y.mean(),
    gdf.geometry.centroid.x.mean()
]

m = folium.Map(
    location=centro,
    zoom_start=6,
    tiles="cartodbdark_matter"
)




folium.GeoJson(
    gdf,
    name="Entidades",
    style_function=lambda x: {
        "fillColor": "#3186cc",
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.4,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["NOMGEO"],
        aliases=["Municipio:"]
    )
).add_to(m)

m.save("dashboard/municipios.html")
