import logging
import os
from dotenv import load_dotenv
from chromadb.api.types import (
    Documents,
    EmbeddingFunction,
    Embeddings,
)
import requests
from utils.constants import LOG_FORMAT

try:
    from chromadb.is_thin_client import is_thin_client
except ImportError:
    is_thin_client = False

load_dotenv()
logging.basicConfig(format=LOG_FORMAT,level=logging.DEBUG)
logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    This class is used to get embeddings for a list of texts using the HuggingFace API.
    It requires an API key and a model name. The default model name is "sentence-transformers/all-MiniLM-L6-v2".
    """

    def __init__(self, model_name: str) -> None:
        """
        Initialize the OllamaEmbeddingFunction.

        Args:
            model_name (str, optional): The name of the model to use for text embeddings.
        """
        self._api_url = f"{os.getenv('ollama_server')}/api/embeddings"
        self._session = requests.Session()
        self._model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        """
        Get the embeddings for a list of texts.

        Args:
            texts (Documents): A list of texts to get embeddings for.

        Returns:
            Embeddings: The embeddings for the texts.

        Example:
            >>> ollama_embed = OllamaEmbeddingFunction(model_name="your_model_name")
            >>> texts = ["Hello, world!", "How are you?"]
            >>> embeddings = ollama_embed(texts)
        """
        # Call Ollama Embedding API for each document
        embeddings = []
        for text in input:
            logger.debug(text)
            logger.debug(self._model_name)
            
            response = self._session.post(
                self._api_url,
                json={"prompt": text, "model": self._model_name},
            ).json()

            if "embedding" in response:
                embeddings.append(response["embedding"])

        return embeddings
