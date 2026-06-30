# Prompt pentru generarea proiectului Docs-RAG-Assist

Generează un proiect Python complet numit `Docs-RAG-Assist`.

## Scop

Construiește un sistem RAG local enterprise care răspunde la întrebări pe baza documentelor dintr-un folder local.

Tehnologii obligatorii:

- Python 3.13
- Flask
- FAISS
- `sentence-transformers/all-MiniLM-L6-v2` pentru embeddings
- `Qwen/Qwen2.5-3B-Instruct` prin Transformers ca LLM local
- Torch
- Accelerate

Nu utiliza:

- Ollama
- API-uri externe pentru inferență
- LangChain

## Funcționalități

Sistemul trebuie să ofere:

- Chat UI
- Chat history persistent în browser folosind localStorage
- Buton „Șterge chat” care golește istoricul conversației din UI și localStorage
- Istoric conversație
- Upload documente
- Reindexare documente
- Streaming răspuns
- Afișare surse
- Confidence score
- Guardrails anti-halucinații
- Funcționare complet locală

## Formate suportate

Documentele trebuie să poată fi indexate din:

```text
PDF
DOCX
TXT
MD
CSV
XLS
XLSX
XLSM
JSON
XML
HTML
HTM
```

## Structura proiectului

```text
Docs-RAG-Assist/
├── main.py
├── ingest.py
├── config.py
├── requirements.txt
├── README.md
├── PROMPT.md
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── chunker.py
│   ├── document_loader.py
│   ├── vector_store.py
│   ├── guardrails.py
│   └── llm.py
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
└── data/
    ├── docs/
    │   └── .gitkeep
    └── faiss_index/
        └── .gitkeep
```

## config.py

Generează:

```python
APP_NAME = "Docs-RAG-Assist"
BASE_DIR
DOCUMENTS_DIR
STORAGE_DIR
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "Qwen/Qwen2.5-3B-Instruct"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 6
MAX_NEW_TOKENS = 700
HOST = "127.0.0.1"
PORT = 5000
DEBUG = False
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".md", ".csv", ".xls", ".xlsx",
    ".xlsm", ".json", ".xml", ".html", ".htm"
}
```

## document_loader.py

Implementează:

```python
read_pdf(path)
read_docx(path)
read_txt(path)
read_csv(path)
read_excel(path)
read_json(path)
read_xml(path)
read_html(path)
load_documents(directory)
```

Cerințe:

- PDF cu `pypdf`
- DOCX cu `python-docx`
- TXT și MD ca text simplu
- CSV cu `pandas`
- XLS/XLSX/XLSM cu `pandas`, `openpyxl`, `xlrd`
- JSON cu `json.dumps(data, indent=2, ensure_ascii=False)`
- XML cu `xml.etree.ElementTree`
- HTML cu `BeautifulSoup`

Pentru CSV și Excel, transformă fiecare rând în:

```text
col1: value1 | col2: value2 | col3: value3
```

## chunker.py

Funcție:

```python
chunk_text(text, chunk_size, overlap) -> list[str]
```

## vector_store.py

Clasă:

```python
VectorStore
```

Metode:

```python
build(chunks)
load()
search(query, top_k)
```

Folosește:

- SentenceTransformer
- FAISS `IndexFlatIP`
- `faiss.normalize_L2`

Salvează:

```text
index.faiss
metadata.pkl
```

## guardrails.py

Generează:

```python
build_grounded_messages(question, contexts, history=None)
validate_answer(answer, contexts)
```

Prompt sistem obligatoriu:

```text
Ești Docs-RAG-Assist.

Docs-RAG-Assist este un asistent RAG local care răspunde exclusiv pe baza documentelor indexate.

Reguli obligatorii:
- Folosește DOAR informațiile din CONTEXT.
- Nu folosi cunoștințe generale.
- Nu inventa date, pași, proceduri, tehnologii, URL-uri sau concluzii.
- Dacă informația nu există clar în context, răspunde exact:
  "Nu am găsit această informație în documentele indexate."
- Dacă informația este parțială, spune explicit că informația este incompletă.
- Răspunde în aceeași limbă în care este pusă întrebarea.
- Menționează sursele folosite în format: Surse: [SOURCE 1], [SOURCE 3]
- Dacă mai multe surse se contrazic, menționează contradicția.
```

`validate_answer()` trebuie să returneze:

```python
{
    "confidence": "high" | "medium" | "low",
    "warnings": [...]
}
```

## llm.py

Folosește:

- `AutoTokenizer`
- `AutoModelForCausalLM`
- `TextIteratorStreamer`
- `torch`

Cerințe:

- Modelul se încarcă lazy, o singură dată.
- Dacă există CUDA: `device = "cuda"`, `dtype = torch.float16`.
- Altfel: `device = "cpu"`, `dtype = torch.float32`.
- Nu folosi `device_map="auto"`.
- Nu folosi `torch_dtype=`.
- Folosește `dtype=`.
- Folosește `model.to(device)` și `model.eval()`.
- Folosește `tokenizer.apply_chat_template`.
- În `generate()` folosește `do_sample=False`, `repetition_penalty=1.05`, `pad_token_id=tokenizer.eos_token_id`.
- Nu folosi `temperature`, `top_p`, `top_k`.

Generează:

```python
ask_local_qwen(question, contexts, model_name, max_new_tokens, history=None)
stream_local_qwen(question, contexts, model_name, max_new_tokens, history=None)
```

## ingest.py

Trebuie să:

- încarce documentele din `DOCUMENTS_DIR`
- genereze chunk-uri
- construiască metadata `{source, chunk_id, text}`
- construiască indexul FAISS prin `VectorStore`
- afișeze câte documente și câte chunk-uri au fost procesate

## main.py

Flask app cu endpoint-uri:

```text
GET  /
GET  /health
POST /ask
POST /stream
POST /upload
POST /reindex
```

Cerințe:

- `/ask` returnează JSON: `answer`, `sources`, `confidence`, `warnings`
- `/stream` returnează stream simplu
- `/upload` acceptă extensiile permise și salvează în `data/docs`
- `/reindex` rulează ingestia programatic, fără shell command
- Sursele trebuie să includă `source`, `chunk_id`, `score`, `preview`
- `debug=False`
- `host="127.0.0.1"`
- `port=5000`

## UI

`templates/index.html` trebuie să includă:

- chat
- upload documente
- buton reindex
- istoric conversație
- surse
- confidence
- warnings

`static/app.js` trebuie să implementeze:

- chat history persistent în browser
- clear chat button
- upload
- reindex
- ask
- afișare surse

`static/style.css` trebuie să fie simplu și curat.

## requirements.txt

```text
torch
transformers
accelerate
sentence-transformers
faiss-cpu
flask
pypdf
python-docx
numpy
pandas
openpyxl
xlrd
beautifulsoup4
lxml
```

## README.md

Include:

- descriere proiect
- Python 3.13
- creare `.venv`
- activare `.venv` pe Windows
- `pip install -r requirements.txt`
- creare `data/docs` și `data/faiss_index`
- adăugare documente
- `python ingest.py`
- `python main.py`
- acces `http://127.0.0.1:5000`
- troubleshooting pentru `ModuleNotFoundError`, index lipsă, CUDA out of memory, meta device, warning `temperature/top_p/top_k`
- explicație că modelele se descarcă automat de pe Hugging Face la prima rulare
- recomandare RAM: 16 GB

## .gitignore

Ignoră:

```text
.venv/
__pycache__/
*.pyc
data/faiss_index/*
!data/faiss_index/.gitkeep
data/docs/*
!data/docs/.gitkeep
models/
.env
```

## Livrabil

La final:

1. Generează toate fișierele.
2. Generează proiectul complet `Docs-RAG-Assist`.
3. Generează arhiva `Docs-RAG-Assist.zip`.
4. Oferă link de descărcare.
