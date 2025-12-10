import json
import os
from collections import Counter

print("--- Generando Subset LIMPIO para Experimento ---")

# Archivos de entrada
FILES_LATAM = ["tomy_qa.json", "justo_qa.json"]
FILE_USA = "usa_qa.json"
OUTPUT_FILE = "subset_experimento_preliminar.json"

# Lista de palabras a ignorar (Basura detectada)
BLACKLIST = [
    "hierro", "sangre", "dólares", "la muerte", "los simios", "Che", "Pilot",
    "Mayo", "2014", "2015", "2012", "2013", "2011", "2010"
]

def cargar_y_filtrar(filenames, top_n=10):
    conteo = Counter()
    data_por_entidad = {}
    
    for filename in filenames:
        if not os.path.exists(filename):
            continue
            
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            try:
                # Extraer entidad
                entidad = item['pregunta'].split(" de ")[-1].replace("?", "").strip()
                
                # --- FILTROS DE LIMPIEZA ---
                # 1. Ignorar si está en la lista negra
                if entidad in BLACKLIST: continue
                # 2. Ignorar si tiene caracteres rotos (encoding)
                if "Ã" in entidad or "Â" in entidad: continue
                # 3. Ignorar si es muy corta (menos de 3 letras)
                if len(entidad) < 3: continue
                # ---------------------------

                conteo[entidad] += 1
                
                if entidad not in data_por_entidad:
                    data_por_entidad[entidad] = []
                data_por_entidad[entidad].append(item)
            except:
                continue
    
    # Devolver los Top N que pasaron los filtros
    return conteo.most_common(top_n), data_por_entidad

# 1. Procesar
print("Procesando LATAM...")
top_latam, data_latam = cargar_y_filtrar(FILES_LATAM, 10)

print("Procesando USA...")
top_usa, data_usa = cargar_y_filtrar([FILE_USA], 10)

# 2. Construir JSON final
subset_final = {"latam": [], "usa": []}

print("\n--- ENTIDADES SELECCIONADAS (CLEAN) ---")
print("LATAM:")
for ent, count in top_latam:
    print(f"  - {ent}")
    subset_final["latam"].append({"entidad": ent, "preguntas": data_latam[ent]})

print("\nUSA:")
for ent, count in top_usa:
    print(f"  - {ent}")
    subset_final["usa"].append({"entidad": ent, "preguntas": data_usa[ent]})

# 3. Guardar
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(subset_final, f, ensure_ascii=False, indent=4)

print(f"\n¡Listo! Archivo '{OUTPUT_FILE}' generado.")