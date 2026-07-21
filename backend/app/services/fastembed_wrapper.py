from langchain_core.embeddings import Embeddings
from fastembed import TextEmbedding

class FastEmbedWrapper(Embeddings):
    def __init__(self):
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(vec) for vec in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(self.model.embed([text]))[0]