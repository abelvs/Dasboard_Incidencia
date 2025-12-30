import pandas as pd
from Funciones_Procesamiento import *

if __name__ == "__main__":
    path = "01_datos/raw/Municipal-Delitos-2015-2025_nov2025/Municipal-Delitos - Noviembre 2025 (2015-2025).csv"


df_final = (
    leer_datos(path)
    .pipe(recode_meses)
    .pipe(agregar_por_subtipo)
    .pipe(pivotear_meses)
    .pipe(crear_fecha)
    .pipe(pad_clave_inegi)
    .pipe(recode_categoricas)
    .pipe(reordenar_cols)
)


print(df_final.head(10))

df_final.to_parquet("01_datos/processed/Municipal-Delitos.parquet", index = False)

