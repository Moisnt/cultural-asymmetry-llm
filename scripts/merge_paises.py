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

print("--- Iniciando Script: Mezclador de CSVs de Países (Forzando sep=';') ---")

# --- CONFIGURACIÓN ---
archivo1 = "tripletas_argentina.csv"
archivo2 = "tripletas_chile.csv"
archivo3 = "tripletas_peru.csv"

archivo_salida = "tripletas_paises_ES.csv"
# --------------------------------------------

archivos_entrada = [archivo1, archivo2, archivo3]
columnas_estandar = ['entidad', 'relacion', 'valor']
lista_dfs_limpios = []

archivos_faltantes = [f for f in archivos_entrada if not os.path.exists(f)]
if archivos_faltantes:
    print(f"Error: No se encontraron los siguientes archivos CSV: {', '.join(archivos_faltantes)}")
    exit()

print("Procesando archivos...")

for i, archivo in enumerate(archivos_entrada):
    print(f"\nProcesando: {archivo}")
    try:
        # --- INICIO DE LA CORRECCIÓN ---
        # Forzamos el separador ';' y la codificación 'latin-1'
        df = pd.read_csv(archivo, index_col=False, encoding='latin-1', sep=';')
        # --- FIN DE LA CORRECCIÓN ---

        print(f"Columnas encontradas: {df.columns.tolist()}")
        
        # 1. Determinar columnas a usar
        columnas_a_usar = ['entidad', 'relacion']
        columna_valor_input = None
        
        if 'valor_es' in df.columns:
            columnas_a_usar.append('valor_es')
            columna_valor_input = 'valor_es'
            print("Priorizando columna 'valor_es'.")
        elif 'valor' in df.columns:
            columnas_a_usar.append('valor')
            columna_valor_input = 'valor'
            print("Usando columna 'valor' (no se encontró 'valor_es').")
        else:
            print("Error: No se encontró 'valor' ni 'valor_es'. Saltando archivo.")
            continue
            
        if not all(col in df.columns for col in ['entidad', 'relacion']):
            print("Error: Faltan las columnas 'entidad' o 'relacion'. Saltando archivo.")
            continue
            
        # 2. Seleccionar y copiar
        df_procesado = df[columnas_a_usar].copy()
        
        # 3. Renombrar a 'valor' estándar
        if columna_valor_input != 'valor':
            df_procesado = df_procesado.rename(columns={columna_valor_input: 'valor'})
            
        df_procesado = df_procesado[columnas_estandar]
            
        # 4. Limpieza inicial (NaNs)
        df_procesado = df_procesado.dropna()
        
        df_procesado['entidad'] = df_procesado['entidad'].astype(str)
        df_procesado['relacion'] = df_procesado['relacion'].astype(str)
        df_procesado['valor'] = df_procesado['valor'].astype(str)

        if len(df_procesado) > 0:
            lista_dfs_limpios.append(df_procesado)
            print(f"Procesado OK: {len(df_procesado)} filas limpias añadidas.")
        else:
            print("Archivo vacío después de limpieza inicial.")

    except KeyError as e:
        print(f"Error procesando {archivo}: Falta la columna {e}. Saltando archivo.")
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

print(f"\n¡Éxito! Se unieron los archivos y se filtró por español.")
print(f"Se guardó el archivo '{archivo_salida}' con {len(df_filtrado_es)} tripletas.")
print("-------------------------------------------------")