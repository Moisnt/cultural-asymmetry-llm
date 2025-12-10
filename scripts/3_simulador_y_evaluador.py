import json
import os
import string
import random
from unidecode import unidecode

print("--- Iniciando Simulador de IA y Evaluación ---")

BENCHMARK_FILE = "dataset_benchmark_qa.json"
SIMULATED_ANSWERS_FILE = "respuestas_llm.json"

if not os.path.exists(BENCHMARK_FILE):
    print(f"Error: No se encuentra '{BENCHMARK_FILE}'.")
    print("Por favor, ejecuta '2_generador_qa.py' primero.")
else:
    with open(BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        benchmark_data = json.load(f)

    respuestas_simuladas = []
    
    print(f"Simulando respuestas de LLM para {len(benchmark_data)} preguntas...")

    sample_size = min(len(benchmark_data), 1000) 
    if len(benchmark_data) == 0:
        print("Error: El benchmark está vacío. Revisa el script 2.")
        exit()
    
    benchmark_sample = random.sample(benchmark_data, sample_size)
    print(f"(Simulando sobre una muestra de {sample_size} preguntas)")

    for item in benchmark_sample:
        pregunta = item['pregunta']
        respuesta_correcta = item['respuesta_correcta']
        
        # Lógica de simulación para crear variaciones
        # 1 de cada 5 respuestas será incorrecta
        if random.random() < 0.20: 
            respuesta_simulada = "No lo sé." # Respuesta incorrecta
        else:
            # Si es correcta, aplicamos una variación al azar
            rand_val = random.random()

            respuesta_correcta_str = str(respuesta_correcta)

            if rand_val < 0.25:
                # 1. Respuesta exacta
                respuesta_simulada = respuesta_correcta_str
            elif rand_val < 0.5:
                # 2. Respuesta con texto al inicio
                respuesta_simulada = f"La respuesta es {respuesta_correcta_str.lower()}"
            elif rand_val < 0.75:
                # 3. Respuesta con texto al final
                respuesta_simulada = f"Se sabe que fue {respuesta_correcta_str.lower()}."
            else:
                # 4. Respuesta con mayúsculas/minúsculas raras
                respuesta_simulada = f"Creo que {respuesta_correcta_str.upper()}"
        
        respuestas_simuladas.append({
            "pregunta": pregunta,
            "respuesta_llm": respuesta_simulada
        })

    # Guardar las respuestas simuladas
    with open(SIMULATED_ANSWERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(respuestas_simuladas, f, ensure_ascii=False, indent=4)
    
    print(f"¡Simulación completa! Se guardó '{SIMULATED_ANSWERS_FILE}'.")

    def normalizar_texto(texto):
        """
        Convierte el texto a un formato simple para comparación:
        - Minúsculas
        - Sin tildes
        - Sin puntuación
        """
        if not isinstance(texto, str):
            return ""
        
        texto = texto.lower()
        texto = unidecode(texto)
        texto = texto.translate(str.maketrans('', '', string.punctuation))
        texto = texto.strip()
        return texto

    respuestas_correctas = {
        item['pregunta']: item['respuesta_correcta'] for item in benchmark_data
    }

    with open(SIMULATED_ANSWERS_FILE, 'r', encoding='utf-8') as f:
        llm_data = json.load(f)

    total_preguntas = 0
    correctas = 0
    resultados_evaluacion = []

    print("Resultados de la evaluación")

    for item_llm in llm_data:
        pregunta = item_llm['pregunta']
        respuesta_llm = item_llm['respuesta_llm']

        if pregunta in respuestas_correctas:
            total_preguntas += 1
            respuesta_correcta = respuestas_correctas[pregunta]

            norm_correcta = normalizar_texto(respuesta_correcta)
            norm_llm = normalizar_texto(respuesta_llm)

            es_correcta = False
            
            if norm_correcta in norm_llm and norm_correcta != "":
                es_correcta = True
                correctas += 1
            
            resultados_evaluacion.append({
                "pregunta": pregunta,
                "respuesta_correcta": respuesta_correcta,
                "respuesta_llm": respuesta_llm,
                "evaluacion": "CORRECTO" if es_correcta else "INCORRECTO"
            })


    print("\n--- Tabla de Resultados de Evaluación (Muestra) ---")
    for res in resultados_evaluacion[:10]: # Muestra solo los primeros 10
        print(f"  P: {res['pregunta']}")
        print(f"  R. Correcta: {res['respuesta_correcta']}")
        print(f"  R. LLM: {res['respuesta_llm']} -> {res['evaluacion']}")
        print("  ---")

    if total_preguntas > 0:
        puntaje = (correctas / total_preguntas) * 100
        print(f"\n Resultado Final (Simulación): {correctas} de {total_preguntas} correctas ({puntaje:.1f}%)")
        print("Este puntaje demuestra que tu evaluador es robusto y maneja variaciones.")
    else:
        print("No se evaluaron preguntas.")

    print("-------------------------------------------------")