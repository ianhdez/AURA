import torch

from transformers import AutoModelForCausalLM, AutoTokenizer

from .base import ModelBackend


class TransformersBackend(ModelBackend):

    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

    def load(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            local_files_only=True,
            dtype=torch.bfloat16,
            device_map="auto"
        )

    def unload(self):
        self.model = None
        self.tokenizer = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generate(self, messages, **kwargs):
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt"
        )

        inputs = {
            key: value.to("cuda")
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                **kwargs
            )

        response = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )

        if "<think>" in response:
            response = response.split("</think>", 1)[-1].strip()

        return response

    def is_loaded(self):
        return self.model is not None

    def get_status(self):
        if not self.is_loaded():
            return {
                "loaded": False
            }

        return {
            "loaded": True,
            "device": str(self.model.device),
            "model": str(self.model_path)
        }