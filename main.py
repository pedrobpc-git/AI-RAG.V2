import os
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request
from werkzeug.utils import secure_filename

from app.guardrails import validate_answer
from app.llm import ask_local_qwen, stream_local_qwen
from app.vector_store import VectorStore
from config import (
    ALLOWED_EXTENSIONS,
    APP_NAME,
    DEBUG,
    DOCUMENTS_DIR,
    EMBEDDING_MODEL,
    HOST,
    LLM_MODEL,
    MAX_NEW_TOKENS,
    PORT,
    STORAGE_DIR,
    TOP_K,
)
from ingest import build_index

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

store = VectorStore(EMBEDDING_MODEL, STORAGE_DIR)


def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _source_payload(contexts):
    sources = []
    for ctx in contexts:
        text = ctx.get("text", "")
        sources.append({
            "source": ctx.get("source"),
            "chunk_id": ctx.get("chunk_id"),
            "score": round(float(ctx.get("score", 0.0)), 4),
            "preview": text[:500] + ("..." if len(text) > 500 else ""),
        })
    return sources


@app.route("/")
def index():
    return render_template("index.html", app_name=APP_NAME)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": APP_NAME})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    history = data.get("history") or []

    if not question:
        return jsonify({"error": "Întrebarea este goală."}), 400

    try:
        contexts = store.search(question, top_k=TOP_K)
        answer = ask_local_qwen(question, contexts, LLM_MODEL, MAX_NEW_TOKENS, history)
        validation = validate_answer(answer, contexts)
        return jsonify({
            "answer": answer,
            "sources": _source_payload(contexts),
            "confidence": validation["confidence"],
            "warnings": validation["warnings"],
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/stream", methods=["POST"])
def stream():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    history = data.get("history") or []

    if not question:
        return jsonify({"error": "Întrebarea este goală."}), 400

    try:
        contexts = store.search(question, top_k=TOP_K)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    def generate():
        for token in stream_local_qwen(question, contexts, LLM_MODEL, MAX_NEW_TOKENS, history):
            yield token

    return Response(generate(), mimetype="text/plain; charset=utf-8")


@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return jsonify({"error": "Nu au fost trimise fișiere."}), 400

    files = request.files.getlist("files")
    saved = []
    rejected = []

    for file in files:
        filename = secure_filename(file.filename or "")
        if not filename:
            continue
        if not _allowed_file(filename):
            rejected.append(filename)
            continue
        target_path = os.path.join(DOCUMENTS_DIR, filename)
        file.save(target_path)
        saved.append(filename)

    return jsonify({"saved": saved, "rejected": rejected})


@app.route("/reindex", methods=["POST"])
def reindex():
    global store
    try:
        result = build_index()
        store = VectorStore(EMBEDDING_MODEL, STORAGE_DIR)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
