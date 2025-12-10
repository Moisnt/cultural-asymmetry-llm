import warnings
warnings.filterwarnings("ignore")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
from tqdm import tqdm
import os
import argparse
import json

# --- Clases de Wrappers (Actualizadas para Qwen) ---
class AttnWrapper(torch.nn.Module):
    def __init__(self, attn):
        super().__init__()
        self.attn = attn
        self.activations = None
        self.add_tensor = None

    def forward(self, *args, **kwargs):
        output = self.attn(*args, **kwargs)
        if self.add_tensor is not None:
            output = (output[0] + self.add_tensor,) + output[1:]
        self.activations = output[0]
        return output

    def reset(self):
        self.activations = None
        self.add_tensor = None

class BlockOutputWrapper(torch.nn.Module):
    def __init__(self, block, lm_head, norm):
        super().__init__()
        self.block = block
        self.lm_head = lm_head
        self.norm = norm
        
        # Wrap attention module
        self.block.self_attn = AttnWrapper(self.block.self_attn)
        self.post_attention_layernorm = self.block.post_attention_layernorm

        # Store intermediate activations
        self.attn_mech_output_unembedded = None
        self.intermediate_res_unembedded = None
        self.mlp_output_unembedded = None
        self.block_output_unembedded = None

    def forward(self, x, past_key_value=None, attention_mask=None, position_ids=None, **kwargs):
        output = self.block(x, past_key_value=past_key_value, attention_mask=attention_mask, 
                          position_ids=position_ids, **kwargs)
        
        # Get hidden states
        if isinstance(output, tuple):
            hidden_states = output[0]
        else:
            hidden_states = output
            
        # Get attention output and compute intermediate activations
        attn_output = self.block.self_attn.activations
        self.attn_mech_output_unembedded = self.lm_head(self.norm(attn_output))
        
        # Add residual connection
        attn_output += x
        self.intermediate_res_unembedded = self.lm_head(self.norm(attn_output))
        
        # MLP output
        mlp_output = self.block.mlp(self.post_attention_layernorm(attn_output))
        self.mlp_output_unembedded = self.lm_head(self.norm(mlp_output))
        
        # Block output
        self.block_output_unembedded = self.lm_head(self.norm(hidden_states))

        return output

    def attn_add_tensor(self, tensor):
        self.block.self_attn.add_tensor = tensor

    def reset(self):
        self.block.self_attn.reset()
        self.attn_mech_output_unembedded = None
        self.intermediate_res_unembedded = None
        self.mlp_output_unembedded = None
        self.block_output_unembedded = None

    def get_attn_activations(self):
        return self.block.self_attn.activations

    def __getattr__(self, name):
        """Delegate unknown attributes to the underlying block."""
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.block, name)

# --- Clase Helper y Función de Análisis ---
class Qwen3_8BHelper:
    def __init__(self, token, gpu_id):
        self.device = f"cuda:{gpu_id}"
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True, token=token)
        self.model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True, token=token).to(self.device)
        for i, layer in enumerate(self.model.model.layers):
            self.model.model.layers[i] = BlockOutputWrapper(layer, self.model.lm_head, self.model.model.norm).to(self.device)

    def get_logits(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            self.model(inputs.input_ids)

    def get_last_activations(self, layer):
        return self.model.model.layers[layer].block_output_unembedded[0, -1, :]

    def get_last_logits(self):
        return self.get_last_activations(len(self.model.model.layers) - 1)

    def get_all_activations(self):
        all_activations = []
        for i in range(len(self.model.model.layers)):
            all_activations.append(self.get_last_activations(i))
        return torch.stack(all_activations)

    def reset_all(self):
        for i in range(len(self.model.model.layers)):
            self.model.model.layers[i].reset()

class Llama3_1_8BHelper:
    def __init__(self, token, gpu_id):
        self.device = f"cuda:{gpu_id}"
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3.1-8B-Instruct", token=token)
        self.model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3.1-8B-Instruct", token=token).to(self.device)
        for i, layer in enumerate(self.model.model.layers):
            self.model.model.layers[i] = LlamaBlockOutputWrapper(layer, self.model.lm_head, self.model.model.norm).to(self.device)

    def get_logits(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            self.model(inputs.input_ids)
    
    def reset_all(self):
        for i in range(len(self.model.model.layers)):
            self.model.model.layers[i].reset()

class LlamaBlockOutputWrapper(torch.nn.Module):
    def __init__(self, block, lm_head, norm):
        super().__init__()
        self.block = block
        self.lm_head = lm_head
        self.norm = norm
        self.block_output_unembedded = None
    def forward(self, *args, **kwargs):
        output = self.block(*args, **kwargs)
        hidden_states = output[0]
        self.block_output_unembedded = self.lm_head(self.norm(hidden_states))
        return output
    def reset(self):
        self.block_output_unembedded = None

def get_model_helper(model_name, token, gpu_id):
    if model_name == "llama3":
        return Llama3_1_8BHelper(token, gpu_id)
    elif model_name == "qwen3":
        return Qwen3_8BHelper(token, gpu_id)
    else:
        raise ValueError(f"Modelo '{model_name}' no soportado.")

def get_probability_trajectory(model_helper, prompt, ground_truth):
    """
    Analiza un único prompt para obtener la trayectoria de probabilidad de la respuesta correcta
    a través de las capas del modelo.
    """
    # --- Comprobación de seguridad para evitar prompts/gts vacíos o que tokenizan a nada ---
    if not prompt or not ground_truth:
        return None
    
    prompt_tokens = model_helper.tokenizer(prompt, add_special_tokens=False)['input_ids']
    gt_tokens = model_helper.tokenizer(ground_truth, add_special_tokens=False)['input_ids']

    if not prompt_tokens or not gt_tokens:
        return None
    # -----------------------------------------------------------------------------------

    model_helper.reset_all()
    first_gt_token_id = gt_tokens[0]
    
    model_helper.get_logits(prompt)
    
    trajectory_data = []
    for i, layer in enumerate(model_helper.model.model.layers):
        decoded_activations = layer.block_output_unembedded

        if decoded_activations is None:
            continue
            
        # Handle 3D tensors (batch_size, seq_len, vocab_size)
        if decoded_activations.dim() == 3:
            decoded_activations = decoded_activations[0]

        if decoded_activations.dim() != 2 or decoded_activations.nelement() == 0:
            continue

        last_token_logits = decoded_activations[-1, :]
        softmaxed = torch.nn.functional.softmax(last_token_logits, dim=-1)

        vocab_size = softmaxed.shape[-1]
        if first_gt_token_id >= vocab_size:
            continue

        top_1_prob, _ = torch.topk(softmaxed, 1)
        gt_prob = softmaxed[first_gt_token_id].item()
        
        trajectory_data.append({
            'layer': i, 
            'ground_truth_prob': gt_prob, 
            'top_1_prob': top_1_prob.item()
        })
        
    return pd.DataFrame(trajectory_data)

# --- Función de Análisis Principal ---
def analizar_trayectorias(model_helper, data):
    todas_las_trayectorias = []
    for _, fila in tqdm(data.iterrows(), total=len(data)):
        df_trayectoria = get_probability_trajectory(model_helper, fila['prompt'], fila['ground_truth'])
        if df_trayectoria is not None:
            df_trayectoria['category'] = fila['category'] # Cambiado de region a category
            df_trayectoria['prompt_id'] = f"p_{_}"
            todas_las_trayectorias.append(df_trayectoria)
    return pd.concat(todas_las_trayectorias)

# --- Lógica Principal del Script ---
def main():
    parser = argparse.ArgumentParser(description="Analizar trayectorias de logits en paralelo.")
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

    # Cargar el dataset de Hugging Face
    dataset_path = '/workspace1/gonzalo.fuentes/proyecto_generativa/subset_h2_completion.json'
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    lista_prompts = []
    # El nuevo formato es una lista directa de objetos
    for item in data:
        prompt = item.get('input_text')
        ground_truth = item.get('target')
        category = item.get('category', 'unknown')
        
        if prompt and ground_truth:
            lista_prompts.append({
                'category': category,
                'prompt': prompt.strip(),
                'ground_truth': ground_truth.strip()
            })
    df_flat = pd.DataFrame(lista_prompts)

    partition_size = len(df_flat) // args.total_partitions
    start_index = args.partition * partition_size
    end_index = (args.partition + 1) * partition_size if args.partition != args.total_partitions - 1 else len(df_flat)
    df_partition = df_flat.iloc[start_index:end_index]

    print(f"Procesando {len(df_partition)} muestras...")

    # --- Procesamiento ---
    resultados = analizar_trayectorias(model_helper, df_partition)

    # --- Guardar Resultados ---
    results_dir = args.results_dir
    os.makedirs(results_dir, exist_ok=True)
    output_file = os.path.join(results_dir, f"trayectorias_{args.model_name}_part_{args.partition}.csv")
    resultados.to_csv(output_file, index=False)
    print(f"Resultados de la partición {args.partition} para el modelo '{args.model_name}' guardados en {output_file}")

if __name__ == "__main__":
    main()
