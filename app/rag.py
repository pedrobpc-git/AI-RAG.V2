from app.chunker import chunk_text
from app.document_loader import load_documents
from app.vector_store import VectorStore
from config import CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_DIR, EMBEDDING_MODEL, STORAGE_DIR


def build_index():
    documents = load_documents(DOCUMENTS_DIR)
    chunks = []

    for doc in documents:
        doc_chunks = chunk_text(doc["text"], CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(doc_chunks):
            chunks.append({
                "source": doc["source"],
                "chunk_id": i,
                "text": chunk,
            })

    if not chunks:
        raise ValueError(f"Nu am găsit documente suportate în folderul: {DOCUMENTS_DIR}")

    store = VectorStore(EMBEDDING_MODEL, STORAGE_DIR)
    store.build(chunks)

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "storage_dir": STORAGE_DIR,
    }
