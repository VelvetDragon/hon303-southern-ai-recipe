from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir = "./southern-recipe-model"

tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
model     = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True)

print("✅ Loaded:", model.config.model_type)
