const chatDisplay = document.getElementById("chat-display");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const pdfInput = document.getElementById("pdf-input");
const progressWrap = document.getElementById("progress-wrap");
const statusLine = document.getElementById("status-line");
const historyList = document.getElementById("history-list");
const footerSession = document.getElementById("footer-session");

let documentReady = false;

function appendBubble(sender, message) {
  const wrap = document.createElement("div");
  const cls = sender === "You" ? "you" : sender === "Bot" ? "bot" : "system";
  wrap.className = `msg ${cls}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = message;

  wrap.appendChild(bubble);
  chatDisplay.appendChild(wrap);
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function clearChat() {
  chatDisplay.innerHTML = "";
}

function setStatus(text, type) {
  statusLine.textContent = `STATUS: ${text}`;
  statusLine.className = `status-line ${type || ""}`;
}

function setInputEnabled(enabled) {
  chatInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
}

async function refreshHistory() {
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    historyList.innerHTML = "";
    data.sessions.forEach((session) => {
      const item = document.createElement("div");
      item.className = "history-item";
      item.textContent = session.session_name;
      item.addEventListener("click", () => loadOldSession(session));
      historyList.appendChild(item);
    });
  } catch (err) {
    console.error("Failed to load history", err);
  }
}

function loadOldSession(session) {
  clearChat();
  session.messages.forEach((msg) => appendBubble(msg.sender, msg.message));
  footerSession.textContent = `VIEWING: ${session.session_name}`;
  setStatus("VIEWING HISTORY (READ-ONLY)", "");
  setInputEnabled(false);
  chatInput.placeholder = "Re-upload a PDF to continue chatting.";
  documentReady = false;
}

pdfInput.addEventListener("change", async () => {
  const file = pdfInput.files[0];
  if (!file) return;

  clearChat();
  progressWrap.classList.remove("hidden");
  setStatus("PROCESSING PDF...", "");
  setInputEnabled(false);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }
    const data = await res.json();
    appendBubble("System", data.message);
    setStatus("INDEX READY", "ok");
    documentReady = true;
    setInputEnabled(true);
    chatInput.placeholder = "Ask a question about the document...";
    footerSession.textContent = `SESSION: ${data.session_name}`;
    refreshHistory();
  } catch (err) {
    appendBubble("System", `Error: ${err.message}`);
    setStatus("ERROR", "error");
    setInputEnabled(false);
  } finally {
    progressWrap.classList.add("hidden");
    pdfInput.value = "";
  }
});

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message || !documentReady) return;

  appendBubble("You", message);
  chatInput.value = "";
  setInputEnabled(false);

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Request failed");
    }
    const data = await res.json();
    appendBubble("Bot", data.answer);
  } catch (err) {
    appendBubble("System", `Error: ${err.message}`);
  } finally {
    setInputEnabled(true);
    chatInput.focus();
    refreshHistory();
  }
});

refreshHistory();
