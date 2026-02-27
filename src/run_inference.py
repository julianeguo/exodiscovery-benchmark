# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer

# MODEL = "Qwen/Qwen3-8B"

# def main():
#     device = "mps" if torch.backends.mps.is_available() else "cpu"
#     print("Using device:", device)

#     tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
#     model = AutoModelForCausalLM.from_pretrained(
#         MODEL,
#         torch_dtype=torch.float16 if device != "cpu" else None,
#         device_map=None,
#         trust_remote_code=True,
#     ).to(device)

#     messages = [
#         {"role": "system", "content": "Return JSON only."},
#         {"role": "user", "content": "/no_think\nSay hello in JSON with key 'msg'."},
#     ]
#     text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
#     inputs = tok(text, return_tensors="pt").to(device)

#     with torch.no_grad():
#         out = model.generate(**inputs, max_new_tokens=64, temperature=0.0, do_sample=False)
#     print(tok.decode(out[0], skip_special_tokens=True))

# if __name__ == "__main__":
#     main()