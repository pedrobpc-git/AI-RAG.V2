# Docs-RAG-Assist

Docs-RAG-Assist este un RAG local pentru interogarea documentelor din `data/docs`, folosind:

- Flask pentru Web UI
- FAISS pentru vector store local
- `sentence-transformers/all-MiniLM-L6-v2` pentru embeddings
- `Qwen/Qwen2.5-3B-Instruct` prin Transformers ca LLM local
- Guardrails anti-halucinații
- Upload documente și reindexare din UI
- Chat history persistent în browser
- Buton „Șterge chat” pentru resetarea conversației

Nu folosește Ollama și nu trimite întrebările/documentele către un API extern pentru inferență.

---

## Formate suportate

- PDF
- DOCX
- TXT
- MD
- CSV
- XLS
- XLSX
- XLSM
- JSON
- XML
- HTML / HTM

---

## Structură proiect

```text
Docs-RAG-Assist/
├── main.py
├── ingest.py
├── config.py
├── requirements.txt
├── README.md
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

---

## Cerințe

Recomandat:

```text
Windows 10/11
Python 3.13
16 GB RAM
```

Dacă ai GPU NVIDIA, aplicația va încerca să folosească CUDA pentru Qwen.

Verifică Python:

```cmd
python --version
```

---

## Instalare

Rulează din folderul proiectului.

### 1. Creează mediul virtual

```cmd
python -m venv .venv
.venv\Scripts\activate.ps1
```

Trebuie să vezi `(.venv)` în prompt.

### 2. Actualizează pip

```cmd
python -m pip install --upgrade pip setuptools wheel
```

### 3. Instalează dependențele

```cmd
pip install -r requirements.txt
```

Notă: la prima rulare, modelul `Qwen/Qwen2.5-3B-Instruct` și modelul de embeddings `all-MiniLM-L6-v2` vor fi descărcate automat din Hugging Face în cache-ul local.

---

## Pregătire documente

Copiază documentele în:

```text
data/docs/
```

Exemplu:

```text
data/docs/onboarding.pdf
data/docs/proceduri.docx
data/docs/export.xlsx
data/docs/config.json
```

---

## Ingestie / creare index

Rulează:

```cmd
python ingest.py
```

La final trebuie să existe:

```text
data/faiss_index/index.faiss
data/faiss_index/metadata.pkl
```

---

## Pornire aplicație

```cmd
python main.py
```

Deschide în browser:

```text
http://127.0.0.1:5000
```

---

## Flow complet

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python ingest.py
python main.py
```

---

## Utilizare

În UI poți:

1. Pune întrebări despre documentele indexate.
2. Încărca documente noi.
3. Apăsa `Reindex` după upload.
4. Vedea sursele folosite, scorul semantic, preview-ul sursei, confidence și warnings.
5. Păstra istoricul conversației în browser.
6. Șterge conversația cu butonul `Șterge chat`.

---

## Configurare

Fișierul principal este `config.py`.

Setări importante:

```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "Qwen/Qwen2.5-3B-Instruct"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 6
MAX_NEW_TOKENS = 700
```

---

## Troubleshooting

### ModuleNotFoundError

Exemplu:

```text
ModuleNotFoundError: No module named 'pypdf'
```

Soluție:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

Verifică Python-ul folosit:

```cmd
where python
```

Primul rezultat trebuie să fie din `.venv`.

---

### Indexul nu există

Mesaj:

```text
Indexul nu există. Rulează mai întâi: python ingest.py
```

Soluție:

```cmd
python ingest.py
```

---

### CUDA out of memory

Dacă ai GPU cu VRAM mic, Qwen poate să nu încapă complet pe GPU.

Soluții:

1. Închide alte aplicații care folosesc GPU.
2. Rulează pe CPU prin dezactivarea CUDA în cod sau în environment.
3. Redu `MAX_NEW_TOKENS` în `config.py`.
4. Redu `TOP_K` în `config.py`.

---

### Tensor on device cpu is not on expected device meta

Acest proiect evită intenționat:

```python
device_map="auto"
```

Modelul este încărcat explicit pe `cuda` sau `cpu`, prin `model.to(device)`.

---

### Warning temperature/top_p/top_k

Acest proiect folosește:

```python
do_sample=False
```

și nu trimite `temperature`, `top_p` sau `top_k` în `generate()`.

---

## Reguli anti-halucinații

Docs-RAG-Assist trebuie să răspundă doar pe baza contextului extras din documente.

Dacă informația nu există în documente, răspunsul standard este:

```text
Nu am găsit această informație în documentele indexate.
```

---

## Recomandări RAM

Pentru `Qwen/Qwen2.5-3B-Instruct` prin Transformers:

```text
8 GB RAM minim
16 GB RAM recomandat
```

Pe CPU, prima rulare poate fi lentă deoarece modelul este descărcat și încărcat local.
