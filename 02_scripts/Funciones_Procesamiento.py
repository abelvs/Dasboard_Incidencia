import pandas as pd
import janitor

meses = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]

mes_a_num = {mes: i+1 for i, mes in enumerate(meses)}

def leer_datos(path):
    ## Lee el CSV de "raw". Se actualiza mensualmente ##
    df = pd.read_csv(path, encoding = "latin1")
    return df.clean_names()

def recode_meses(df):
    ## Convierte cols de meses a int y strings a category para optimización ##
    for mes in meses:
        df[mes] = pd.to_numeric(df[mes],errors='coerce').astype("Int32")
    return df

def agregar_por_subtipo(df):
    ## Agrega df por año, mes, municipio y subtipo de delito ##
    return df.groupby(['ano', 'cve_municipio', 'subtipo_de_delito'], as_index = False) \
    .agg({mes: "sum" for mes in meses})

def pivotear_meses(df):
    ## Pivot longer de las columnas de mes ##
    return df.melt(
        id_vars = ['ano', 'cve_municipio', 'subtipo_de_delito'],
        value_vars = meses,
        var_name = "mes",
        value_name = "total"
    )

def crear_fecha(df):
    ## Genera mes numerico y crea columna de fecha ##
    df['mes_num'] = df['mes'].map(mes_a_num)
    df['fecha'] = pd.to_datetime(dict(year = df['ano'],
                                      month = df['mes_num'],
                                      day = 1))
    return df

def pad_clave_inegi(df):
    ## Aplica padding a la izquierda para coincidir con catálogo INEGI ##
    df['cve_municipio'] = df['cve_municipio'].astype(str).str.zfill(5)
    return df

def recode_categoricas(df):
    ## Convierte columnas strings con campos repetidos en category ##
    df['subtipo_de_delito'] = df['subtipo_de_delito'].astype('category')
    df['mes_num'] = df['mes_num'].astype('category')
    df['mes'] = df['mes'].astype('category')
    df['ano'] = df['ano'].astype('category')
    df['cve_municipio'] = df['cve_municipio'].astype('category')
    return df

def reordenar_cols(df):
    ## Reordena columnas para df final ##
    return df[['ano','mes','mes_num','fecha','cve_municipio','subtipo_de_delito','total']]


