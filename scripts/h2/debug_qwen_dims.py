import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

# Mock Wrapper to test dimensions
class BlockOutputWrapper(torch.nn.Module):
    def __init__(self, block, lm_head, norm):
        super().__init__()
        self.block = block
        self.lm_head = lm_head
        self.norm = norm
        self.block_output_unembedded = None

    def forward(self, x, *args, **kwargs):
        output = self.block(x, *args, **kwargs)
        if isinstance(output, tuple):
            hidden_states = output[0]
        else:
            hidden_states = output
        
        self.block_output_unembedded = self.lm_head(self.norm(hidden_states))
        return output
    
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.block, name)

def main():
    token = os.environ.get("HUGGING_FACE_TOKEN")
    if not token:
        print("No token found")
        return

    print("Loading Qwen...")
    try:
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B", trust_remote_code=True, token=token)
        model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-8B", trust_remote_code=True, token=token, device_map="cuda:0")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Wrap one layer
    layer_idx = 0
    model.model.layers[layer_idx] = BlockOutputWrapper(model.model.layers[layer_idx], model.lm_head, model.model.norm)
    
    prompt = "Hello world"
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda:0")
    
    print("Running forward pass...")
    with torch.no_grad():
        model(inputs.input_ids)
    
    output = model.model.layers[layer_idx].block_output_unembedded
    print(f"Output shape: {output.shape}")
    print(f"Output dim: {output.dim()}")

if __name__ == "__main__":
    main()
