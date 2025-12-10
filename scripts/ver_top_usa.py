import json
from collections import Counter

FILE_USA = "usa_qa.json"

print(f"--- Analizando Top 50 USA en {FILE_USA} ---")

with open(FILE_USA, 'r', encoding='utf-8') as f:
    data = json.load(f)

conteo = Counter()
for item in data:
    try:
        # Extraemos la entidad (mismo método que antes)
        entidad = item['pregunta'].split(" de ")[-1].replace("?", "").strip()
        # Filtro básico: Que empiece con Mayúscula y tenga más de 3 letras
        if len(entidad) > 3 and entidad[0].isupper():
            conteo[entidad] += 1
    except:
        pass

print("\nCandidatos USA:")
for ent, count in conteo.most_common(50):
    print(f"'{ent}' ({count})")