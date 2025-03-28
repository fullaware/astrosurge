import os
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIModel

# Load environment variables from .env file
load_dotenv()

class ModelConfig:
    """
    Configuration for the Ollama model.
    """
    ollama_model = OpenAIModel(
        model_name=os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
        base_url=os.getenv("OLLAMA_URI", "http://localhost:11434") + "/v1",
    )

    @staticmethod
    def get_model():
        """
        Get the configured Ollama model.

        Returns:
            OpenAIModel: The configured Ollama model instance.
        """
        return ModelConfig.ollama_model
