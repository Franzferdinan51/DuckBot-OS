import json
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
import os

# Step 1: Load dataset
import os

# Search for the dataset file in Kaggle's input directory
dataset_path = None
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        if filename == 'duckbot_expert_training.jsonl':
            dataset_path = os.path.join(dirname, filename)
            break
    if dataset_path:
        break

# If not found in Kaggle, try a local path (for development)
if dataset_path is None:
    local_path = "training_data/duckbot_expert_training.jsonl"
    if os.path.exists(local_path):
        dataset_path = local_path
    else:
        # If it's still not found, raise a clear error
        raise FileNotFoundError(
            "Could not find 'duckbot_expert_training.jsonl'. "
            "Please ensure the file is uploaded to your Kaggle dataset "
            "or available at 'training_data/duckbot_expert_training.jsonl' for local execution."
        )

print(f"Loading dataset from: {dataset_path}")

# Load as Hugging Face dataset
dataset = load_dataset("json", data_files=dataset_path, split="train")

# Step 2: Format for instruction tuning
def format_example(example):
    """
    Formats each example into a structured instruction-response pair.
    This helps the model learn to follow instructions based on the provided context.
    """
    # Create a descriptive instruction using the file's source and summary
    prompt = f"Analyze the following file: `{example['source']}`. The file is summarized as: '{example['summary']}'. Provide the full content of this file."
    
    # The "completion" is the full content of the file
    completion = example.get('content', '')
    
    # Create the final formatted text
    text = f"### Instruction:\n{prompt}\n\n### Response:\n{completion}"
    return {"text": text}

# Apply the formatting to the dataset
dataset = dataset.map(format_example)

# Step 3: Tokenizer and Model Setup
model_name = "Qwen/Qwen1.5-1.8B-Chat"  # Using a valid and efficient Qwen model
tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# Tokenize function
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding=True, max_length=512)

tokenized_dataset = dataset.map(tokenize_function, batched=True)
tokenized_dataset = tokenized_dataset.train_test_split(test_size=0.1)  # 90/10 split

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,  # Causal LM
)

# Step 4: LoRA Config (efficient fine-tuning)
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]  # Correct for Qwen1.5
)
model = get_peft_model(model, lora_config)

# Step 5: Training Args (Kaggle GPU-friendly: short epochs, small batch)
training_args = TrainingArguments(
    output_dir="./duckbot_finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    evaluation_strategy="steps",
    eval_steps=50,
    save_steps=100,
    load_best_model_at_end=True,
    fp16=True,  # Mixed precision
    dataloader_pin_memory=False,  # Kaggle optimization
)

# Step 6: Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    data_collator=data_collator,
    tokenizer=tokenizer,
)

# Step 7: Train and Save
trainer.train()
trainer.save_model("./duckbot_model_final")
tokenizer.save_pretrained("./duckbot_model_final")

# Inference example
def generate_response(prompt):
    inputs = tokenizer(f"### Instruction:\n{prompt}\n\n### Response:\n", return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

print("Training complete! Example:", generate_response("How does DuckBot handle MCP integration?"))
