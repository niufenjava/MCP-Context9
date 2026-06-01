from fastembed import TextEmbedding

class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-small"):
        self.model_name = model_name
        self.model = TextEmbedding(model_name=model_name)

    def encode(self, texts: str | list[str]) -> list[list[float]]:
        if isinstance(texts, str):
            texts = [texts]
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

    @property
    def dimension(self) -> int:
        return self.model.embedding_size