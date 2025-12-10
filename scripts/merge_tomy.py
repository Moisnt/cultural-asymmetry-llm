import pandas as pd
import os
import sys
try:
    from langdetect import detect, LangDetectException
except ImportError:
    print("Error: Necesitas 'langdetect'. Instálalo con: pip install langdetect")
    exit()
try:
    from unidecode import unidecode
except ImportError:
    print("Error: Necesitas 'unidecode'. Instálalo con: pip install unidecode")
    exit()

print("--- Iniciando Script: Mezclador de 5 CSVs de Tomy (v2 - Usa comas y salta errores) ---")

# --- CONFIGURACIÓN: Reemplaza con los 5 nombres de archivo de Tomy ---
archivos_entrada = [
    "cine_latam_151363Entities.csv",
    "danzas_por_pais_latam_1401Entities.csv",
    "landmarks_LATAM_103493Entities.csv",
    "pintores_latam_4671Entities.csv",
    "pueblos_indigenas_latam_4079Entities.csv"
]
archivo_salida = "tripletas_tomy_ES.csv"
# --------------------------------------------

columnas_deseadas = ['entidad', 'relacion', 'valor_es']
columnas_estandar = ['entidad', 'relacion', 'valor']
lista_dfs_limpios = []

archivos_faltantes = [f for f in archivos_entrada if not os.path.exists(f)]
if archivos_faltantes:
    print(f"Error: No se encontraron los siguientes archivos CSV: {', '.join(archivos_faltantes)}")
    exit()

print("Procesando archivos...")

for archivo in archivos_entrada:
    print(f"\nProcesando: {archivo}")
    try:
        # --- INICIO DE LA CORRECCIÓN ---
        # 1. Quitamos 'sep=';' para que use la coma (,) por defecto.
        # 2. Agregamos 'on_bad_lines='skip'' para ignorar líneas con errores de formato.
        df = pd.read_csv(archivo, index_col=False, encoding='latin-1', on_bad_lines='skip')
        # --- FIN DE LA CORRECCIÓN ---
        
        print(f"Columnas encontradas: {df.columns.tolist()}")

        # Limpiar espacios en los nombres de columnas (por si acaso)
        df.columns = df.columns.str.strip()

        if not all(col in df.columns for col in columnas_deseadas):
            print(f"Error: El archivo {archivo} no tiene las columnas esperadas {columnas_deseadas}. Saltando.")
            continue

        df_procesado = df[columnas_deseadas].copy()
        df_procesado = df_procesado.rename(columns={'valor_es': 'valor'})
        df_procesado = df_procesado.dropna()
        
        df_procesado['entidad'] = df_procesado['entidad'].astype(str)
        df_procesado['relacion'] = df_procesado['relacion'].astype(str)
        df_procesado['valor'] = df_procesado['valor'].astype(str)

        if len(df_procesado) > 0:
            lista_dfs_limpios.append(df_procesado)
            print(f"Procesado OK: {len(df_procesado)} filas limpias añadidas.")
        else:
            print("Archivo vacío después de limpieza inicial.")

    except Exception as e:
        print(f"Error inesperado procesando {archivo}: {e}. Saltando archivo.")

# --- Unir y Filtrar por Idioma ---
if not lista_dfs_limpios:
    print("\nError: No se pudo procesar ningún archivo CSV correctamente.")
    exit()

print("\nUniendo DataFrames procesados...")
df_completo = pd.concat(lista_dfs_limpios, ignore_index=True)

filas_antes_duplicados = len(df_completo)
df_completo = df_completo.drop_duplicates()
print(f"Eliminados {filas_antes_duplicados - len(df_completo)} duplicados.")

print("Iniciando filtrado por idioma español... (Puede tardar)")
def es_espanol(texto):
    if not isinstance(texto, str) or len(texto.strip()) < 2: return False
    try: return detect(texto) == 'es'
    except LangDetectException: return False
    except Exception: return False

df_completo['es_espanol'] = df_completo['valor'].apply(es_espanol)
filas_antes_idioma = len(df_completo)
df_filtrado_es = df_completo[df_completo['es_espanol'] == True].copy()
df_filtrado_es = df_filtrado_es.drop(columns=['es_espanol'])
print(f"Filtrado completo. Se conservaron {len(df_filtrado_es)} tripletas en español.")

# --- Guardar Resultado ---
df_filtrado_es.to_csv(archivo_salida, index=False, encoding='utf-8')

print(f"\n¡Éxito! Se unieron los 5 archivos y se filtró por español.")
print(f"Se guardó el archivo '{archivo_salida}' con {len(df_filtrado_es)} tripletas.")
print("-------------------------------------------------")