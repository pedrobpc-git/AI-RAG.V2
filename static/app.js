const messagesEl = document.getElementById("messages");
const questionEl = document.getElementById("question");
const askBtn = document.getElementById("askBtn");
const uploadBtn = document.getElementById("uploadBtn");
const reindexBtn = document.getElementById("reindexBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const fileInput = document.getElementById("fileInput");
const statusEl = document.getElementById("status");

const CHAT_HISTORY_KEY = "docs-rag-assist-chat-history-v1";
let history = loadHistory();

function setStatus(text) {
  statusEl.textContent = text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(CHAT_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_) {
    return [];
  }
}

function saveHistory() {
  localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history));
}

function renderHistory() {
  messagesEl.innerHTML = "";
  for (const item of history) {
    if (item.user) addMessage("user", item.user, {}, false);
    if (item.assistant) {
      addMessage("assistant", item.assistant, {
        sources: item.sources || [],
        confidence: item.confidence,
        warnings: item.warnings || []
      }, false);
    }
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function clearChat() {
  history = [];
  saveHistory();
  renderHistory();
  setStatus("Chat șters.");
  questionEl.focus();
}

function addMessage(role, content, extra = {}, scroll = true) {
  const div = document.createElement("div");
  div.className = `message ${role}`;

  let html = `<div class="meta">${role === "user" ? "Tu" : "Docs-RAG-Assist"}</div>`;
  html += `<div>${escapeHtml(content).replaceAll("\n", "<br>")}</div>`;

  if (extra.confidence) {
    html += `<div class="meta">Confidence: ${escapeHtml(extra.confidence)}</div>`;
  }

  if (extra.warnings && extra.warnings.length) {
    html += extra.warnings.map(w => `<div class="warning">${escapeHtml(w)}</div>`).join("");
  }

  if (extra.sources && extra.sources.length) {
    html += `<div class="sources"><strong>Surse</strong>`;
    for (const src of extra.sources) {
      html += `<div class="source">
        <div><strong>${escapeHtml(src.source)}</strong></div>
        <div>Chunk: ${escapeHtml(src.chunk_id)} | Score: ${escapeHtml(src.score)}</div>
        <div>${escapeHtml(src.preview)}</div>
      </div>`;
    }
    html += `</div>`;
  }

  div.innerHTML = html;
  messagesEl.appendChild(div);
  if (scroll) messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function ask() {
  const question = questionEl.value.trim();
  if (!question) return;

  addMessage("user", question);
  questionEl.value = "";
  setStatus("Se generează răspunsul...");

  const assistantDiv = document.createElement("div");
  assistantDiv.className = "message assistant";
  assistantDiv.innerHTML = `<div class="meta">Docs-RAG-Assist</div><div class="stream-content"></div>`;
  messagesEl.appendChild(assistantDiv);

  const contentDiv = assistantDiv.querySelector(".stream-content");
  let fullAnswer = "";

  try {
    const response = await fetch("/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history })
    });

    if (!response.ok) {
      throw new Error("Eroare la streaming.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      fullAnswer += chunk;

      contentDiv.innerHTML = escapeHtml(fullAnswer).replaceAll("\n", "<br>");
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    history.push({
      user: question,
      assistant: fullAnswer
    });

    saveHistory();
    setStatus("Ready.");
  } catch (err) {
    setStatus(`Eroare: ${err.message}`);
  }
}

async function upload() {
  if (!fileInput.files.length) {
    setStatus("Alege cel puțin un fișier.");
    return;
  }
  const formData = new FormData();
  for (const file of fileInput.files) {
    formData.append("files", file);
  }
  setStatus("Upload în curs...");
  try {
    const response = await fetch("/upload", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Upload failed");
    setStatus(`Upload OK\nSaved: ${data.saved.join(", ") || "-"}\nRejected: ${data.rejected.join(", ") || "-"}\nRulează Reindex.`);
  } catch (err) {
    setStatus(`Eroare upload: ${err.message}`);
  }
}

async function reindex() {
  setStatus("Reindexare în curs...");
  try {
    const response = await fetch("/reindex", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Reindex failed");
    setStatus(data.message);
  } catch (err) {
    setStatus(`Eroare reindex: ${err.message}`);
  }
}

askBtn.addEventListener("click", ask);
uploadBtn.addEventListener("click", upload);
reindexBtn.addEventListener("click", reindex);
clearChatBtn.addEventListener("click", clearChat);
questionEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.ctrlKey) ask();
});

renderHistory();
