import os
from typing import Iterable, List, Dict, Any


NO_ANSWER_MESSAGE = "Nu am găsit această informație în documentele indexate."


def _format_sources(contexts: Iterable[Dict[str, Any]], max_context_chars: int) -> str:
    parts = []
    total = 0

    for i, ctx in enumerate(contexts, start=1):
        source = os.path.basename(ctx.get("source", "unknown"))
        chunk_id = ctx.get("chunk_id", "?")
        text = (ctx.get("text") or "").strip()
        block = f"[SOURCE {i}: {source}, chunk {chunk_id}]\n{text}"

        if total + len(block) > max_context_chars:
            remaining = max_context_chars - total
            if remaining > 300:
                parts.append(block[:remaining])
            break

        parts.append(block)
        total += len(block)

    return "\n\n".join(parts)


def build_grounded_messages(question: str, contexts, history=None, max_context_chars: int = 7000):
    context_text = _format_sources(contexts, max_context_chars)

    system_message = (
        "Ești un asistent RAG local. Răspunzi STRICT pe baza contextului primit din documentele indexate. "
        "Nu folosi cunoștințe externe. Nu inventa nume, date, proceduri, linkuri sau pași. "
        f"Dacă răspunsul nu este susținut clar de context, răspunde exact: '{NO_ANSWER_MESSAGE}' "
        "Răspunde în română. Include la final o secțiune scurtă 'Surse folosite' cu numele fișierelor relevante."
    )

    user_message = (
        "Context din documente:\n"
        f"{context_text if context_text else '[fără context relevant]'}\n\n"
        f"Întrebare:\n{question}\n\n"
        "Răspuns:"
    )

    messages = [{"role": "system", "content": system_message}]

    # Keep only the last turns and avoid growing the prompt too much.
    for item in (history or [])[-6:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content[:1000]})

    messages.append({"role": "user", "content": user_message})
    return messages


def validate_answer(answer: str, contexts) -> Dict[str, Any]:
    warnings: List[str] = []
    answer_lower = (answer or "").lower()

    if not contexts:
        warnings.append("Nu au fost găsite surse relevante în FAISS.")

    if NO_ANSWER_MESSAGE.lower() in answer_lower:
        return {"confidence": "low", "warnings": warnings}

    risky_phrases = [
        "probabil",
        "în general",
        "de obicei",
        "se poate presupune",
        "nu sunt sigur",
        "ar trebui să",
    ]

    for phrase in risky_phrases:
        if phrase in answer_lower:
            warnings.append(f"Răspunsul conține formulare potențial nesigură: '{phrase}'.")

    max_score = max((ctx.get("score", 0.0) for ctx in contexts), default=0.0)
    if max_score < 0.25:
        warnings.append("Scorul de similaritate al surselor este scăzut.")

    if warnings:
        confidence = "medium"
    else:
        confidence = "high" if max_score >= 0.35 else "medium"

    return {"confidence": confidence, "warnings": warnings}
