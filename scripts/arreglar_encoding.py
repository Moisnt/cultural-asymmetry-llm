import json

INPUT_FILE = "subset_experimento_preliminar.json"
OUTPUT_FILE = "subset_experimento_final.json"

print(f"Limpiando agresivamente {INPUT_FILE}...")

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    # Leemos todo el contenido como texto
    content = f.read()

# Diccionario de reemplazos manuales basados en tu snippet
replacements = {
    # Patrones con 'í' (lo que me mostraste ahora)
    "í±": "ñ",
    "í©": "é",
    "í¡": "á",
    "íº": "ú",
    "í­": "í",  # A veces la í se rompe así
    "í³": "ó",
    
    # Patrones con 'Ã' (por si quedan algunos del tipo anterior)
    "Ã±": "ñ",
    "Ã©": "é",
    "Ã¡": "á",
    "Ãº": "ú",
    "Ã³": "ó",
    "Ã": "í",   # A veces la í suelta queda como Ã
    
    # Arreglos específicos de palabras rotas comunes en tu data
    "pelí­cula": "película",
    "televisión": "televisión", # Asegurar
    "míºsico": "músico",
    "Garcí­a": "García",
    "Mí¡rquez": "Márquez",
    "Sí©bastien": "Sébastien",
    "crí­menes": "crímenes"
}

# Aplicar reemplazos
for bad, good in replacements.items():
    content = content.replace(bad, good)

# Verificar que siga siendo un JSON válido
try:
    data_json = json.loads(content)
    
    # Guardar
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_json, f, ensure_ascii=False, indent=4)
        
    print(f"¡Listo! Archivo limpio guardado en: {OUTPUT_FILE}")
    print("Revisa este archivo visualmente. Si se ve bien, mándaselo a Gonza.")

except json.JSONDecodeError:
    print("Error: Los reemplazos rompieron el formato JSON. Revisa el script.")