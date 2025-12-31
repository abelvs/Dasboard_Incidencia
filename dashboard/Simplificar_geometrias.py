import geopandas as gpd
from pathlib import Path

# --- Rutas ---
BASE_DIR = Path(__file__).resolve().parent.parent
shapefile_path = BASE_DIR / "01_datos/raw/mg_2025_integrado/conjunto_de_datos/00mun.shp"
output_path = BASE_DIR / "01_datos/processed/00mun_simplificado.geojson"

# --- Cargar shapefile ---
gdf = gpd.read_file(shapefile_path)

# --- Convertir a CRS métrico para simplificar ---
gdf_m = gdf.to_crs(epsg=3857)  # metros

# --- Simplificar geometrías ---
gdf_m["geometry"] = gdf_m.geometry.simplify(tolerance=600, preserve_topology=True)

# --- Volver a CRS lat/lon (EPSG:4326) ---
gdf_simpl = gdf_m.to_crs(epsg=4326)

# --- Guardar simplificado ---
gdf_simpl.to_file(output_path, driver="GeoJSON")