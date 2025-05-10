import requests
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

class OllamaClient:
    """Client for interacting with Ollama API with performance optimizations."""
    
    def __init__(self, base_url="http://localhost:11434", model="mistral:7b", use_gpu=False):
        self.base_url = base_url
        self.model = model
        self.use_gpu = use_gpu
        # Use a connection pool for better HTTP performance
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Thread-local storage for request context
        self.local = threading.local()
        
        # Thread pool for parallel requests
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def generate(self, prompt, system_message=None, temperature=0.7, max_tokens=512):
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens  # reduced token limit
        }
        if self.use_gpu:
            payload["gpu"] = True
        if system_message:
            payload["system"] = system_message

        logger.info("Calling Ollama API for generate()")
        try:
            response = self.session.post(url, json=payload, timeout=60)  # increased timeout
            response.raise_for_status()
            result = response.json().get("response", "")
            logger.info("Ollama API responded successfully")
            return result

        except requests.exceptions.Timeout:
            logger.error("Ollama API generate() timed out")
            return "Error: Ollama API timed out"
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            return f"Error: {str(e)}"
    
    def stream_generate(self, prompt, system_message=None, temperature=0.7):
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True
        }
        if self.use_gpu:
            payload["gpu"] = True
        if system_message:
            payload["system"] = system_message
        try:
            # First check if the server is running with a quick ping
            try:
                self.session.get(f"{self.base_url}/api/tags", timeout=2)
            except requests.exceptions.RequestException:
                logger.error("Ollama server is not running or not accessible at {self.base_url}")
                yield "ERROR: Ollama server not available. Please ensure Ollama is running."
                return
                
            response = self.session.post(url, json=payload, stream=True, timeout=60)  # ensure streaming timeout
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_line = json.loads(decoded_line)
                        if "response" in json_line:
                            yield json_line["response"]
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode JSON: {decoded_line}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error streaming from Ollama API: {e}")
            yield f"Error: {str(e)}"
    
    def get_available_models(self):
        url = f"{self.base_url}/api/tags"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json().get("models", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching models from Ollama: {e}")
            return []
    
    def shutdown(self):
        """Clean up resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        if hasattr(self, 'session'):
            self.session.close()
