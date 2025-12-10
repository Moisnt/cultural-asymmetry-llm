import json
import os
import string
import random

try:
    from unidecode import unidecode
except ImportError:
    print("Error: Necesitas 'unidecode'. Instalalo con: pip install unidecode")
    exit()
try:
    from vllm import LLM, SamplingParams
except ImportError:
    print("Error: Necesitas 'vllm'. Instálalo con: pip install vllm")
    exit()

# --- MODIFICACIÓN 1: Cambiar el modelo ---
MODELO = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" 
CANTIDAD = 100

BENCHMARK_FILE = "dataset_benchmark_qa.json"
OUTPUT_FILE = f"evaluacion_real_{MODELO.split('/')[-1]}.json"

if not os.path.exists(BENCHMARK_FILE):
    print(f"Error: No se encuentra '{BENCHMARK_FILE}'. Ejecuta el script 2 primero.")
    exit()

with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
    benchmark_data = json.load(f)

if len(benchmark_data) == 0:
    print("Error: El benchmark está vacío.")
    exit()

print(f"Cargando {len(benchmark_data)} preguntas. Se probará una muestra de {CANTIDAD}.")
benchmark_sample = random.sample(benchmark_data, min(len(benchmark_data), CANTIDAD))

# --- MODIFICACIÓN 2: Cambiar el formato del prompt para TinyLlama ---
prompts = [f"<|user|>\n{item['pregunta']}<|assistant|>" for item in benchmark_sample]
# --- FIN MODIFICACIÓN 2 ---

respuestas_correctas_sample = [item['respuesta_correcta'] for item in benchmark_sample]

print(f"\nCargando modelo '{MODELO}' en la GPU. (Esto puede tardar)...")
sampling_params = SamplingParams(temperature=0.1, top_p=0.9, max_tokens=100)

# Mantenemos la utilización de memoria baja
llm = LLM(model=MODELO, gpu_memory_utilization=0.7) 

print("¡Modelo cargado! Iniciando generación de respuestas...")

outputs = llm.generate(prompts, sampling_params)
print("¡Generación completa! Evaluando respuestas...")

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower()
    texto = unidecode(texto)
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    texto = texto.strip()
    return texto

total_preguntas = 0
correctas = 0
resultados_evaluacion = []

for i, output in enumerate(outputs):
    pregunta_original = benchmark_sample[i]['pregunta'] 
    respuesta_llm = output.outputs[0].text.strip()
    respuesta_correcta_gt = respuestas_correctas_sample[i]

    norm_correcta = normalizar_texto(respuesta_correcta_gt)
    norm_llm = normalizar_texto(respuesta_llm)
    
    es_correcta = False
    if norm_correcta in norm_llm and norm_correcta != "":
        es_correcta = True
        correctas += 1
    
    total_preguntas += 1
    
    resultados_evaluacion.append({
        "pregunta": pregunta_original,
        "respuesta_correcta": respuesta_correcta_gt,
        "respuesta_llm": respuesta_llm,
        "evaluacion": "CORRECTO" if es_correcta else "INCORRECTO"
    })

print("\n--- Tabla de Resultados de Evaluación (Muestra de 10) ---")
for res in resultados_evaluacion[:10]:
    print(f"  P: {res['pregunta']}")
    print(f"  R. Correcta: {res['respuesta_correcta']}")
    print(f"  R. LLM: {res['respuesta_llm']} -> {res['evaluacion']}")
    print("  ---")

if total_preguntas > 0:
    puntaje = (correctas / total_preguntas) * 100
    print(f"\n Resultado Final ({MODELO}): {correctas} de {total_preguntas} correctas ({puntaje:.1f}%)")
else:
    print("No se evaluaron preguntas.")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(resultados_evaluacion, f, ensure_ascii=False, indent=4)
print(f"Resultados detallados guardados en '{OUTPUT_FILE}'")
print("-------------------------------------------------")