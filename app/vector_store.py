import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, embedding_model_name: str, storage_dir: str):
        self.storage_dir = storage_dir
        self.index_path = os.path.join(storage_dir, "index.faiss")
        self.meta_path = os.path.join(storage_dir, "metadata.pkl")
        self.model = SentenceTransformer(embedding_model_name)
        self.index = None
        self.metadata = []

    def build(self, chunks):
        if not chunks:
            raise ValueError("Nu există chunk-uri pentru indexare.")

        os.makedirs(self.storage_dir, exist_ok=True)

        texts = [item["text"] for item in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.metadata = chunks

        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        if not os.path.exists(self.index_path) or not os.path.exists(self.meta_path):
            raise FileNotFoundError(
                f"Indexul nu există în {self.storage_dir}. Rulează mai întâi: python ingest.py"
            )

        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "rb") as f:
            self.metadata = pickle.load(f)

    def search(self, query: str, top_k: int = 5):
        if self.index is None:
            self.load()

        query_embedding = self.model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(query_embedding)

        scores, ids = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            item = dict(self.metadata[idx])
            item["score"] = float(score)
            results.append(item)

        return results
