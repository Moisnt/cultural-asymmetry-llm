import pandas as pd
import os
import sys
try:
    from langdetect import detect, LangDetectException
except ImportError:
    print("Error: Necesitas 'langdetect'. Instálalo con: pip install langdetect")
    exit()
try:
    from unidecode import unidecode # Although not strictly needed here, good practice
except ImportError:
    print("Error: Necesitas 'unidecode'. Instálalo con: pip install unidecode")
    exit()

print("--- Iniciando Script: Mezclador de CSVs USA (Filtra EN) ---")

# --- CONFIGURACIÓN: CAMBIA ESTOS 2 NOMBRES ---
archivos_entrada = [
    "peliculas_us_176688Entities.csv",
    "pintores_us_60610Entities.csv"
]
archivo_salida = "tripletas_usa_EN.csv"
# --------------------------------------------

# Columnas que queremos extraer (priorizamos 'valor' para USA)
columnas_deseadas = ['entidad', 'relacion', 'valor']
lista_dfs_limpios = [] # Lista para guardar los DataFrames procesados

# Verificar que todos los archivos existan
archivos_faltantes = [f for f in archivos_entrada if not os.path.exists(f)]
if archivos_faltantes:
    print(f"Error: No se encontraron los siguientes archivos CSV: {', '.join(archivos_faltantes)}")
    exit()

print("Procesando archivos...")

for archivo in archivos_entrada:
    print(f"\nProcesando: {archivo}")
    try:
        # Leer CSV: Asumimos coma (,) como separador y latin-1 encoding. Ignorar líneas malas.
        df = pd.read_csv(archivo, index_col=False, encoding='latin-1', on_bad_lines='skip')
        
        print(f"Columnas encontradas: {df.columns.tolist()}")

        # Limpiar espacios en los nombres de columnas
        df.columns = df.columns.str.strip()

        # Verificar que las columnas deseadas existan
        if not all(col in df.columns for col in columnas_deseadas):
            print(f"Error: El archivo {archivo} no tiene las columnas esperadas {columnas_deseadas}. Saltando.")
            # Intentar mostrar columnas disponibles si falla
            print(f"Columnas disponibles: {df.columns.tolist()}")
            continue

        # 1. Seleccionar y copiar
        df_procesado = df[columnas_deseadas].copy()
        
        # 2. Limpieza inicial (NaNs)
        df_procesado = df_procesado.dropna()
        
        # 3. Convertir todo a string
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

print("Iniciando filtrado por idioma inglés ('en')... (Puede tardar)")
def es_ingles(texto):
    # Ignorar textos muy cortos o no strings
    if not isinstance(texto, str) or len(texto.strip()) < 2: return False
    try:
        # Detectar idioma y verificar si es inglés ('en')
        return detect(texto) == 'es'
    except LangDetectException:
        return False # Si no puede detectar, descartar
    except Exception:
        return False # Otros errores, descartar

# Aplicar filtro
df_completo['es_ingles'] = df_completo['valor'].apply(es_ingles)
filas_antes_idioma = len(df_completo)
df_filtrado_en = df_completo[df_completo['es_ingles'] == True].copy()
df_filtrado_en = df_filtrado_en.drop(columns=['es_ingles'])
print(f"Filtrado completo. Se conservaron {len(df_filtrado_en)} tripletas en inglés.")

# --- Guardar Resultado ---
# Guardamos en UTF-8 estándar
df_filtrado_en.to_csv(archivo_salida, index=False, encoding='utf-8')

print(f"\n¡Éxito! Se unieron los archivos y se filtró por inglés.")
print(f"Se guardó el archivo '{archivo_salida}' con {len(df_filtrado_en)} tripletas.")
print("-------------------------------------------------")