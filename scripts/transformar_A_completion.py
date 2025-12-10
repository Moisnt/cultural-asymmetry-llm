import json

# Usamos el archivo limpio que generamos antes
INPUT_FILE = "subset_experimento_final.json"
OUTPUT_FILE = "dataset_completion_base_full.json" # Cambié el nombre para diferenciar

print(f"Transformando {INPUT_FILE} a formato Completion (CON REPETIDOS)...")

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

nuevo_dataset = {"latam": [], "usa": []}

def transformar_prompt(pregunta_original):
    # Formato original: "¿Cuál es [relacion] de [entidad]?"
    # Objetivo: "[Relacion] de [entidad] es"
    
    texto = pregunta_original.strip()
    
    # 1. Quitar signos de interrogación
    texto = texto.replace("¿", "").replace("?", "")
    
    # 2. Quitar "Cuál es " (insensible a mayúsculas)
    if texto.lower().startswith("cuál es "):
        texto = texto[8:].strip()
    
    # 3. Capitalizar primera letra y agregar " es"
    if len(texto) > 0:
        texto = texto[0].upper() + texto[1:] + " es"
    
    return texto

total_items = 0

for region in ["latam", "usa"]:
    for item_entidad in data[region]:
        entidad_nombre = item_entidad["entidad"]
        lista_preguntas = item_entidad["preguntas"]
        
        nuevas_preguntas = []
        # Eliminamos el set 'prompts_vistos' para permitir repetidos
        
        for p in lista_preguntas:
            prompt_qa = p["pregunta"]
            respuesta = p["respuesta_correcta"]
            
            # Transformar a formato completion
            prompt_completion = transformar_prompt(prompt_qa)
            
            # --- SIN DEDUPLICACIÓN ---
            # Guardamos todo directamente
            
            nuevas_preguntas.append({
                "prompt_original": prompt_qa,
                "input_text": prompt_completion,
                "target_text": " " + respuesta # Espacio para tokenización
            })
            total_items += 1
            
        nuevo_dataset[region].append({
            "entidad": entidad_nombre,
            "samples": nuevas_preguntas
        })

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(nuevo_dataset, f, ensure_ascii=False, indent=4)

print(f"¡Listo! Dataset guardado en {OUTPUT_FILE}")
print(f"Total de samples generados: {total_items}")