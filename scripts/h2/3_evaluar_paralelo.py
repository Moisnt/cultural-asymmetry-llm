import warnings
warnings.filterwarnings("ignore")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForVision2Seq, AutoModel
import pandas as pd
from tqdm import tqdm
import re
import os
from collections import Counter
import argparse
import json
import gc

# ===============================================================
# 1. DEFINICIONES DE CLASES Y FUNCIONES (Idéntico al notebook)
# ===============================================================

class Qwen3_8BHelper:
    """Wrapper para el modelo Qwen3-8B."""
    def __init__(self, token, gpu_id):
        self.device = f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-VL-8B-Instruct", trust_remote_code=True, token=token)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen3-VL-8B-Instruct",
            trust_remote_code=True,
            token=token,
            torch_dtype=torch.float16
        ).to(self.device)

    def generate_text(self, prompt, max_new_tokens=200):
        # Usar chat template para mejorar el rendimiento en modelos Instruct
        messages = [{"role": "user", "content": prompt}]
        try:
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            text = prompt
            
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            generate_ids = self.model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id
            )
        new_tokens = generate_ids[0][inputs.input_ids.shape[1]:]
        return self.tokenizer.batch_decode([new_tokens], skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()

class Llama3_1_8BHelper:
    """Versión modificada para cargar el modelo en una GPU específica."""
    def __init__(self, token, gpu_id):
        self.device = f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3.1-8B-Instruct", token=token)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3.1-8B-Instruct", 
            token=token,
            torch_dtype=torch.float16
        ).to(self.device) # <-- Carga el modelo completo en la GPU especificada

    def generate_text(self, prompt, max_new_tokens=200):
        # Usar chat template para mejorar el rendimiento en modelos Instruct
        messages = [{"role": "user", "content": prompt}]
        try:
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            text = prompt

        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            generate_ids = self.model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id
            )
        new_tokens = generate_ids[0][inputs.input_ids.shape[1]:]
        return self.tokenizer.batch_decode([new_tokens], skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()

def normalize_text(s):
    s = s.lower()
    s = re.sub(r'[^\w\s]', '', s)
    return s

def f1_score(prediction, ground_truth):
    pred_tokens = normalize_text(prediction).split()
    gt_tokens = normalize_text(ground_truth).split()
    if not gt_tokens: return 1 if not pred_tokens else 0
    if not pred_tokens: return 0
    common = Counter(pred_tokens) & Counter(gt_tokens)
    num_same = sum(common.values())
    if num_same == 0: return 0
    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(gt_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1

def substring_accuracy(prediction, ground_truth):
    return 1 if normalize_text(ground_truth) in normalize_text(prediction) else 0

class JudgeModel:
    """Clase para evaluar con un modelo Juez (Qwen)."""
    def __init__(self, token, gpu_id):
        self.device = f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu"
        # Usamos Qwen2.5-7B-Instruct: Más estable para texto y sin problemas de config
        model_name = "Qwen/Qwen2.5-7B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, token=token, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            token=token, 
            trust_remote_code=True,
            torch_dtype=torch.float16
        ).to(self.device)

    def evaluate(self, prompt, prediction, ground_truth):
        # Usar chat template para mejor adherencia a instrucciones y formato JSON
        messages = [
            {"role": "system", "content": "Eres un juez evaluador experto. Tu tarea es determinar si una predicción es correcta basándote en una respuesta de referencia."},
            {"role": "user", "content": f"""Evalúa si la 'Predicción' es una respuesta aceptable para el 'Prompt', considerando la 'Respuesta Correcta' como referencia.
            
            Prompt: {prompt}
            Respuesta Correcta: {ground_truth}
            Predicción: {prediction}
            
            Responde ÚNICAMENTE con un objeto JSON que tenga un campo "score" con valor 1 (aceptable) o 0 (no aceptable).
            Ejemplo: {{"score": 1}}"""}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        with torch.no_grad():
            output_tokens = self.model.generate(
                inputs.input_ids, 
                attention_mask=inputs.attention_mask,
                max_new_tokens=50,
                pad_token_id=self.tokenizer.eos_token_id
            )[0]
            
        response = self.tokenizer.decode(output_tokens[len(inputs.input_ids[0]):], skip_special_tokens=True).strip()
        
        # Intentar parsear JSON
        score = 0
        try:
            # Buscar algo que parezca un JSON: { ... }
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                score = int(data.get("score", 0))
            else:
                # Fallback a búsqueda de dígitos si falla JSON
                match = re.search(r'\d', response)
                if match:
                    score = int(match.group(0))
        except Exception as e:
            print(f"Error parsing JSON judge response: {e}")
            # Fallback final
            match = re.search(r'\d', response)
            if match:
                score = int(match.group(0))
                
        return score, response

def get_model_helper(model_name, token, gpu_id):
    if model_name == "llama3":
        return Llama3_1_8BHelper(token, gpu_id)
    elif model_name == "qwen3":
        return Qwen3_8BHelper(token, gpu_id)
    else:
        raise ValueError(f"Modelo '{model_name}' no soportado.")

# ===============================================================
# 2. LÓGICA PRINCIPAL DE EVALUACIÓN
# ===============================================================

def main():
    parser = argparse.ArgumentParser(description="Evaluar modelo con juez en paralelo.")
    parser.add_argument("--gpu_id", type=int, required=True, help="ID de la GPU a utilizar.")
    parser.add_argument("--partition", type=int, required=True, help="Número de esta partición (desde 0).")
    parser.add_argument("--total_partitions", type=int, required=True, help="Número total de particiones.")
    parser.add_argument("--model_name", type=str, default="llama3", help="Nombre del modelo a utilizar (llama3 o qwen3).")
    parser.add_argument("--results_dir", type=str, default="resultados", help="Directorio donde guardar los resultados.")
    args = parser.parse_args()

    # --- Carga de Datos y Modelo ---
    HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN")
    if not HUGGING_FACE_TOKEN:
        raise ValueError("La variable de entorno HUGGING_FACE_TOKEN no está configurada.")

    try:
        model_helper = get_model_helper(args.model_name, HUGGING_FACE_TOKEN, args.gpu_id)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # --- Inicializar Juez ---
    try:
        judge = JudgeModel(HUGGING_FACE_TOKEN, args.gpu_id)
    except Exception as e:
        print(f"Error al cargar el modelo Juez: {e}")
        return

    # --- Cargar y aplanar el dataset ---
    with open('/workspace1/gonzalo.fuentes/proyecto_generativa/subset_h2_completion.json', 'r') as f:
        data = json.load(f)
    
    lista_prompts = []
    # El nuevo formato es una lista directa de objetos
    for item in data:
        prompt = item.get('input_text')
        ground_truth = item.get('target')
        category = item.get('category', 'unknown') # Usamos category en lugar de region
        
        if prompt and ground_truth:
            lista_prompts.append({
                'category': category, # Cambiado de region a category
                'prompt': prompt.strip(),
                'ground_truth': ground_truth.strip()
            })
    df_flat = pd.DataFrame(lista_prompts)

    # --- Seleccionar la partición de datos ---
    partition_size = len(df_flat) // args.total_partitions
    start_index = args.partition * partition_size
    end_index = (args.partition + 1) * partition_size
    if args.partition == args.total_partitions - 1:
        end_index = len(df_flat) # Asegurar que el último worker procese todo lo que queda
    
    df_partition = df_flat.iloc[start_index:end_index].copy()
    print(f"Procesando {len(df_partition)} muestras (de índice {start_index} a {end_index-1})")

    # --- FASE 1: Generación ---
    print("--- Iniciando Generación ---")
    try:
        model_helper = get_model_helper(args.model_name, HUGGING_FACE_TOKEN, args.gpu_id)
        predictions = []
        for _, row in tqdm(df_partition.iterrows(), total=len(df_partition)):
            pred = model_helper.generate_text(row['prompt'], max_new_tokens=200)
            predictions.append(pred)
        
        df_partition['prediction'] = predictions
        
        # Liberar memoria del generador
        del model_helper
        torch.cuda.empty_cache()
        gc.collect()
        print("Generación completada. Memoria liberada.")
        
    except Exception as e:
        print(f"Error en generación: {e}")
        return

    # --- FASE 2: Evaluación ---
    print("--- Iniciando Evaluación con Juez ---")
    try:
        judge = JudgeModel(HUGGING_FACE_TOKEN, args.gpu_id)
        judge_scores = []
        judge_raw_responses = []
        
        for i, (_, row) in tqdm(enumerate(df_partition.iterrows()), total=len(df_partition)):
            try:
                score, raw_response = judge.evaluate(row['prompt'], row['prediction'], row['ground_truth'])
                
                # Debug print para las primeras iteraciones
                if i < 3:
                    print(f"\n[DEBUG Juez #{i}]")
                    print(f"Predicción: {row['prediction'][:50]}...")
                    print(f"Respuesta Juez Raw: {raw_response}")
                    print(f"Score extraído: {score}")
                    
            except Exception as e:
                print(f"Error juez: {e}")
                score = 0
                raw_response = "ERROR"
            
            judge_scores.append(score)
            judge_raw_responses.append(raw_response)
            
        df_partition['judge_score'] = judge_scores
        df_partition['judge_raw'] = judge_raw_responses
        
        del judge
        torch.cuda.empty_cache()
        gc.collect()
        
    except Exception as e:
        print(f"Error en evaluación: {e}")
        return
        
    # --- Guardar resultados parciales ---
    df_partition['f1_score'] = df_partition.apply(lambda x: f1_score(x['prediction'], x['ground_truth']), axis=1)
    df_partition['substring_accuracy'] = df_partition.apply(lambda x: substring_accuracy(x['prediction'], x['ground_truth']), axis=1)

    results_dir = args.results_dir
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, f'predicciones_{args.model_name}_part_{args.partition}.csv')
    df_partition.to_csv(output_path, index=False)
    print(f"--- Resultados de la partición {args.partition} guardados en '{output_path}' ---")

if __name__ == "__main__":
    main()
