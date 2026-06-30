import threading
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer


_tokenizer = None
_model = None
_device = None


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_model(model_name: str):
    """Load the local LLM once.

    Important: do not use device_map="auto" here. On CPU-only laptops, accelerate can
    leave some tensors on the "meta" device, which causes:
    RuntimeError: Tensor on device cpu is not on the expected device meta!
    """
    global _tokenizer, _model, _device

    if _tokenizer is None or _model is None:
        _device = _select_device()

        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
        )

        dtype = torch.float16 if _device == "cuda" else torch.float32

        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            trust_remote_code=True,
            low_cpu_mem_usage=False,
        )
        _model.to(_device)
        _model.eval()

    return _tokenizer, _model, _device


def _build_messages(question: str, contexts, history=None):
    history = history or []
    context_text = "\n\n".join(
        f"[Sursa {idx + 1}: {ctx.get('source', 'necunoscut')} | chunk {ctx.get('chunk_id', '-')} | score {ctx.get('score', 0):.3f}]\n{ctx.get('text', '')}"
        for idx, ctx in enumerate(contexts)
    )

    compact_history = []
    for item in history[-6:]:
        role = item.get("role")
        content = item.get("content", "").strip()
        if role in {"user", "assistant"} and content:
            compact_history.append({"role": role, "content": content[:1500]})

    messages = [
        {
            "role": "system",
            "content": (
                "Ești un asistent RAG local. Răspunde în română. "
                "Folosește prioritar și explicit contextul primit din documente. "
                "Dacă răspunsul nu este în context, spune clar că nu ai găsit informația în documentele indexate. "
                "Când folosești informații din context, include referințe scurte de forma [Sursa 1], [Sursa 2]."
            ),
        }
    ]
    messages.extend(compact_history)
    messages.append(
        {
            "role": "user",
            "content": f"Context din documente:\n{context_text}\n\nÎntrebare:\n{question}",
        }
    )
    return messages


def _tokenize_prompt(tokenizer, prompt: str, device: str):
    inputs = tokenizer(prompt, return_tensors="pt")
    return {key: value.to(device) for key, value in inputs.items()}


def ask_local_qwen(question: str, contexts, model_name: str, max_new_tokens: int = 512, history=None) -> str:
    tokenizer, model, device = _load_model(model_name)
    messages = _build_messages(question, contexts, history)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = _tokenize_prompt(tokenizer, prompt, device)

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def stream_local_qwen(question: str, contexts, model_name: str, max_new_tokens: int = 512, history=None):
    tokenizer, model, device = _load_model(model_name)
    messages = _build_messages(question, contexts, history)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = _tokenize_prompt(tokenizer, prompt, device)

    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )

    thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for token in streamer:
        yield token

    thread.join()
