import json
import os
import subprocess   # new import
from loguru import logger

class ConfigManager:
    """Loads and manages configuration settings."""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = {}

        # --- begin GPU detection block ---
        gpu_detected = False
        try:
            import torch
            gpu_detected = torch.cuda.is_available()
        except ImportError:
            logger.warning("PyTorch not installed; checking NVIDIA driver via nvidia-smi")
            try:
                result = subprocess.run(
                    ["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                gpu_detected = (result.returncode == 0)
            except Exception:
                gpu_detected = False
        if gpu_detected:
            logger.info("GPU detected on system → enabling GPU usage")
        else:
            logger.info("No GPU detected → running on CPU")
        # override or set use_gpu
        self.config["use_gpu"] = gpu_detected
        # --- end GPU detection block ---

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config.update(json.load(f))
        else:
            # Default configuration
            self.config.update({
                "ollama_model": "llama2:7b",  # Changed from mistral:7b
                "human_like": True,
                "tesseract_path": None,
                "use_gpu": self.config.get("use_gpu", True)
            })
        return self.config
    
    @property
    def recommended_models(self):
        """List of recommended Ollama models for this application"""
        return [
            "llama2:7b",       # Reliable, fast model
            "phi:2.7b",        # Microsoft's model, good for instructions
            "orca-mini:7b",    # Good for tasks and reasoning
            "gemma:7b",        # Google's model
            "mistral:7b"       # Original model
        ]

    def get(self, key, default=None):
        return self.config.get(key, default)
