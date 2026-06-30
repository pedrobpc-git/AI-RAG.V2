from app.chunker import chunk_text
from app.document_loader import load_documents
from app.vector_store import VectorStore
from config import CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_DIR, EMBEDDING_MODEL, STORAGE_DIR


def build_index() -> dict:
    documents = load_documents(DOCUMENTS_DIR)
    chunks = []

    for doc in documents:
        source = doc["source"]
        for chunk_id, chunk in enumerate(chunk_text(doc["text"], CHUNK_SIZE, CHUNK_OVERLAP)):
            chunks.append({
                "source": source,
                "chunk_id": chunk_id,
                "text": chunk,
            })

    if not chunks:
        return {
            "documents": len(documents),
            "chunks": 0,
            "message": f"Nu am găsit documente suportate în folderul: {DOCUMENTS_DIR}",
        }

    store = VectorStore(EMBEDDING_MODEL, STORAGE_DIR)
    store.build(chunks)
    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "message": f"Index creat cu {len(chunks)} fragmente din {len(documents)} documente.",
    }


def main():
    result = build_index()
    print(result["message"])


if __name__ == "__main__":
    main()
