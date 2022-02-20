import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

"""load model"""
# from https://github.com/kakaobrain/kogpt#python
tokenizer = AutoTokenizer.from_pretrained(
    # or float32 version: revision=KoGPT6B-ryan1.5b
    'kakaobrain/kogpt', revision='KoGPT6B-ryan1.5b-float16',
    bos_token='[BOS]', eos_token='[EOS]', unk_token='[UNK]', pad_token='[PAD]', mask_token='[MASK]'
)
model = AutoModelForCausalLM.from_pretrained(
    # or float32 version: revision=KoGPT6B-ryan1.5b
    'kakaobrain/kogpt', revision='KoGPT6B-ryan1.5b-float16',
    pad_token_id=tokenizer.eos_token_id,
    torch_dtype='auto', low_cpu_mem_usage=True
).to(device='cuda', non_blocking=True)
# _ = model.eval()
print("Model Loaded.")

"""inference"""
with torch.no_grad():
    tokens = tokenizer.encode(prompt, return_tensors='pt').to(
        device='cuda', non_blocking=True)
    gen_tokens = model.generate(
        tokens, do_sample=True, temperature=temperature, max_length=max_length)
    generated = tokenizer.batch_decode(gen_tokens)[0]
return generated
