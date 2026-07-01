import os

APP_NAME = "Docs-RAG-Assist"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "data", "docs")
STORAGE_DIR = os.path.join(BASE_DIR, "data", "faiss_index")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "Qwen/Qwen2.5-3B-Instruct"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 4
MAX_NEW_TOKENS = 512

HOST = "127.0.0.1"
PORT = 5000
DEBUG = False

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".csv",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".json",
    ".xml",
    ".html",
    ".htm",
}
