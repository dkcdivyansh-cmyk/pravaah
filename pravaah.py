# ============================================================
#  Pravaah — Full Stack in one Python file (built by DKC)
#  Backend : Flask  |  AI : OpenAI-compatible proxy
#  Frontend: Glassmorphism + Aurora UI
#  Run with:  python pravaah.py
#  Then open: http://localhost:5000
# ============================================================

import json
import os
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, Response, request, stream_with_context
from openai import OpenAI
import httpx

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5").strip()
PORT = int(os.getenv("PORT") or os.getenv("PRAVAAH_PORT") or "5000")
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
VERIFY_SSL = os.getenv("PRAVAAH_VERIFY_SSL", "true").lower() not in ("0", "false", "no")
EXTRA_BODY_JSON = os.getenv("PRAVAAH_EXTRA_BODY_JSON", "").strip()
NEMOTRON_MIN_THINKING_TOKENS = os.getenv(
    "PRAVAAH_NEMOTRON_MIN_THINKING_TOKENS", ""
).strip()
NEMOTRON_MAX_THINKING_TOKENS = os.getenv(
    "PRAVAAH_NEMOTRON_MAX_THINKING_TOKENS", ""
).strip()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTRUCTIONS_PATH = os.getenv(
    "PRAVAAH_CUSTOM_INSTRUCTIONS_PATH",
    os.path.join(SCRIPT_DIR, "custom_instructions.txt"),
)

if not API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
    )

http_client = httpx.Client(
    timeout=httpx.Timeout(60.0, connect=20.0),
    verify=VERIFY_SSL,
)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL, http_client=http_client)
app = Flask(__name__)


def load_custom_instructions() -> str:
    try:
        if os.path.exists(INSTRUCTIONS_PATH):
            with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
    except OSError as e:
        print(f"Warning: could not read custom instructions: {e}")
    return ""


def build_extra_body() -> Optional[dict]:
    """
    Optional passthrough for OpenAI-compatible providers.
    Useful for Nemotron's thinking token controls.
    """
    if EXTRA_BODY_JSON:
        try:
            return json.loads(EXTRA_BODY_JSON)
        except Exception:
            return None

    out: dict = {}
    if NEMOTRON_MIN_THINKING_TOKENS:
        try:
            out["min_thinking_tokens"] = int(NEMOTRON_MIN_THINKING_TOKENS)
        except Exception:
            pass
    if NEMOTRON_MAX_THINKING_TOKENS:
        try:
            out["max_thinking_tokens"] = int(NEMOTRON_MAX_THINKING_TOKENS)
        except Exception:
            pass

    return out or None


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<title>Pravaah</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='url(%23g)'/><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='%237c6dfa'/><stop offset='100%' stop-color='%2300e5ff'/></linearGradient></defs></svg>"/>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#030308;
  --surface:rgba(255,255,255,0.03);
  --surface2:rgba(255,255,255,0.06);
  --border:rgba(255,255,255,0.08);
  --border2:rgba(255,255,255,0.12);
  --text:#f0f0f5;
  --muted:rgba(240,240,245,0.6);
  --accent:#7c6dfa;
  --accent2:#00e5ff;
  --user-bg:linear-gradient(135deg,#7c6dfa,#00e5ff);
  --glow:0 0 40px rgba(124,109,250,0.15);
  --r:20px;
  --font:'Outfit',sans-serif;
  --mono:'JetBrains Mono',monospace;
  --ease:cubic-bezier(0.25, 1, 0.5, 1);
}
html,body{height:100%;overflow:hidden}
body{
  font-family:var(--font);
  background:var(--bg);
  color:var(--text);
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  -webkit-font-smoothing: antialiased;
}
/* Bubble Background */
.bg-container {
  position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
  background: radial-gradient(circle at 50% 0%, #151030, #030308 70%);
}
.bubble-anim {
  position:absolute;
  border-radius:50%;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.1), rgba(255,255,255,0.02) 60%, transparent 80%);
  box-shadow: inset 0 0 20px rgba(255,255,255,0.05), inset 10px 0 40px rgba(124,109,250,0.1), inset -10px 0 40px rgba(0,229,255,0.1);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  will-change: transform;
}
.b1 { width:300px;height:300px;left:-50px;top:20%;animation:float 20s ease-in-out infinite alternate; }
.b2 { width:400px;height:400px;right:-100px;top:10%;animation:float 25s ease-in-out infinite alternate-reverse; }
.b3 { width:200px;height:200px;left:20%;bottom:-50px;animation:float 18s ease-in-out infinite alternate; }
.b4 { width:150px;height:150px;right:30%;bottom:20%;animation:float 22s ease-in-out infinite alternate-reverse; }
.b5 { width:80px;height:80px;left:40%;top:30%;animation:float 15s ease-in-out infinite alternate; }

@keyframes float {
  0% { transform: translate3d(0,0,0) rotate(0deg) scale(1); }
  100% { transform: translate3d(100px,-100px,0) rotate(45deg) scale(1.1); }
}

.app{
  position:relative;z-index:2;
  width:min(880px,96vw);
  height:min(88vh,900px);
  display:flex;flex-direction:column;
  background:rgba(10,10,18,0.4);
  backdrop-filter:blur(24px) saturate(180%);
  -webkit-backdrop-filter:blur(24px) saturate(180%);
  border:1px solid var(--border2);
  border-radius:24px;
  box-shadow:0 24px 64px rgba(0,0,0,0.4),var(--glow);
  overflow:hidden;
}
.header{
  display:flex;align-items:center;gap:16px;
  padding:20px 28px;
  border-bottom:1px solid var(--border);
  background:rgba(255,255,255,0.015);
  flex-shrink:0;
}
.logo-svg{
  width:42px;height:42px;
  animation: pulse-logo 4s ease-in-out infinite alternate;
}
@keyframes pulse-logo {
  0% { filter: drop-shadow(0 0 10px rgba(124,109,250,0.6)); transform: scale(1); }
  100% { filter: drop-shadow(0 0 20px rgba(0,229,255,0.8)); transform: scale(1.05); }
}
.header-info h1{font-size:1.15rem;font-weight:800;letter-spacing:0.5px;background:var(--user-bg);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.status-dot{
  margin-left:auto;
  display:flex;align-items:center;gap:8px;
  font-size:.8rem;color:var(--muted);font-family:var(--font);font-weight:600;
}
.dot{
  width:8px;height:8px;border-radius:50%;
  background:#00e5ff;
  box-shadow:0 0 10px #00e5ff;
  animation:blink 2.5s ease-in-out infinite;
}
@keyframes blink{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(0.8);}}
.messages{
  flex:1;overflow-y:auto;padding:28px;
  display:flex;flex-direction:column;gap:24px;
  scroll-behavior:smooth;
}
.messages::-webkit-scrollbar{width:6px}
.messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.15);border-radius:6px}
.welcome{
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;flex:1;gap:20px;
  text-align:center;padding:32px;
  animation:fade-up 0.8s var(--ease) both;
}
.welcome svg{
  width:80px;height:80px;
  filter:drop-shadow(0 0 20px rgba(124,109,250,.4));
}
.welcome h2{font-size:2rem;font-weight:800;letter-spacing:-0.5px}
.welcome p{color:var(--muted);font-size:1.05rem;max-width:450px;line-height:1.6}
.welcome-chips{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-top:12px}
.welcome-chip{
  padding:10px 20px;border-radius:30px;font-size:.9rem;font-weight:600;
  border:1px solid var(--border2);background:var(--surface);
  cursor:pointer;transition:all .3s var(--ease);color:var(--text);
  backdrop-filter: blur(8px);
}
.welcome-chip:hover{
  background:var(--surface2);border-color:rgba(124,109,250,0.5);
  transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.3), 0 0 15px rgba(124,109,250,0.2);
}
.msg{display:flex;gap:16px;animation:fade-up .4s var(--ease) both;will-change: transform, opacity;}
.msg.user{flex-direction:row-reverse}
@keyframes fade-up{
  from{opacity:0;transform:translate3d(0,20px,0)}
  to{opacity:1;transform:translate3d(0,0,0)}
}
.avatar{
  width:38px;height:38px;border-radius:12px;
  flex-shrink:0;display:grid;place-items:center;align-self:flex-end;
}
.msg.user .avatar{
  background:var(--user-bg);box-shadow:0 4px 16px rgba(124,109,250,.4);
}
.msg.user .avatar svg { width:20px; height:20px; fill: white; }
.msg.ai .avatar{
  background:rgba(255,255,255,.05);border:1px solid var(--border2);
}
.msg.ai .avatar svg { width:22px; height:22px; }
.bubble{
  max-width:75%;padding:16px 20px;border-radius:24px;
  font-size:1rem;line-height:1.7;word-break:break-word;
}
.msg.user .bubble{
  background:var(--user-bg);border-bottom-right-radius:6px;
  box-shadow:0 8px 32px rgba(124,109,250,.25);color:#fff;
}
.msg.ai .bubble{
  background:rgba(255,255,255,0.04);border:1px solid var(--border);
  border-bottom-left-radius:6px;backdrop-filter:blur(12px);
  box-shadow:0 4px 24px rgba(0,0,0,0.1);
}
.bubble pre{
  background:rgba(0,0,0,.6);border:1px solid var(--border2);
  border-radius:12px;padding:16px;margin:12px 0;overflow-x:auto;
  font-family:var(--mono);font-size:.85rem;line-height:1.5;position:relative;
}
.bubble code{
  font-family:var(--mono);font-size:.85em;
  background:rgba(124,109,250,.2);padding:3px 8px;border-radius:6px;
}
.bubble pre code{background:none;padding:0}
.copy-btn{
  position:absolute;top:10px;right:10px;padding:6px 12px;font-size:.75rem;
  background:rgba(255,255,255,.1);border:1px solid var(--border2);
  border-radius:8px;color:var(--text);cursor:pointer;font-family:var(--mono);
  transition:all .2s var(--ease);
}
.copy-btn:hover{background:var(--accent);border-color:var(--accent);color:#fff;}
.typing-dots{display:flex;gap:6px;align-items:center;padding:6px 4px}
.typing-dots span{
  width:8px;height:8px;border-radius:50%;background:var(--accent2);
  animation:bounce-dot 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(2){animation-delay:.2s;background:var(--accent);}
.typing-dots span:nth-child(3){animation-delay:.4s;background:#fa6d9a;}
@keyframes bounce-dot{
  0%,80%,100%{transform:translate3d(0,0,0);opacity:.5}
  40%{transform:translate3d(0,-10px,0);opacity:1;box-shadow:0 4px 12px rgba(124,109,250,0.4)}
}
.input-area{
  padding:20px 28px;border-top:1px solid var(--border);
  background:rgba(255,255,255,0.02);flex-shrink:0;
}
.input-row{
  display:flex;align-items:flex-end;gap:12px;
  background:rgba(0,0,0,0.3);border:1px solid var(--border2);
  border-radius:24px;padding:12px 16px;
  transition:all .3s var(--ease);
}
.input-row:focus-within{
  border-color:var(--accent2);
  box-shadow:0 0 0 4px rgba(0,229,255,.1),0 8px 32px rgba(0,0,0,0.3);
  background:rgba(0,0,0,0.5);
}
textarea{
  flex:1;background:none;border:none;outline:none;color:var(--text);
  font-family:var(--font);font-size:1rem;resize:none;
  max-height:180px;line-height:1.6;padding:4px 0;
}
textarea::placeholder{color:var(--muted)}
.send-btn{
  width:44px;height:44px;border-radius:14px;
  background:var(--user-bg);border:none;cursor:pointer;
  display:grid;place-items:center;flex-shrink:0;
  transition:all .25s var(--ease);
  box-shadow:0 4px 20px rgba(0,229,255,.3);
}
.send-btn:hover:not(:disabled){transform:scale(1.08) translate3d(0,-2px,0);box-shadow:0 8px 28px rgba(0,229,255,.5)}
.send-btn:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none;}
.send-btn svg{width:20px;height:20px;fill:none;stroke:#030308;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.input-hint{font-size:.75rem;color:var(--muted);font-family:var(--font);margin-top:10px;text-align:center;font-weight:300;}
.error-banner{
  margin:0 28px 16px;padding:12px 16px;border-radius:16px;
  background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.4);
  color:#fca5a5;font-size:.85rem;font-family:var(--mono);display:none;
}
@media (max-width: 600px) {
  .app{width:100%;height:100%;border-radius:0;border:none;}
  .bubble{max-width:90%;}
  .header{padding:16px 20px;}
  .messages{padding:20px;}
  .input-area{padding:16px 20px;}
}
</style>
</head>
<body>
<div class="bg-container">
  <div class="bubble-anim b1"></div>
  <div class="bubble-anim b2"></div>
  <div class="bubble-anim b3"></div>
  <div class="bubble-anim b4"></div>
  <div class="bubble-anim b5"></div>
</div>
<div class="app">
  <div class="header">
    <svg class="logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#7c6dfa" />
          <stop offset="100%" stop-color="#00e5ff" />
        </linearGradient>
      </defs>
      <path d="M50 10 C30 10 10 30 10 50 C10 70 30 90 50 90 C70 90 90 70 90 50 C90 30 70 10 50 10 Z M50 25 C65 25 75 35 75 50 C75 65 65 75 50 75 C35 75 25 65 25 50 C25 35 35 25 50 25 Z M50 40 A10 10 0 1 0 50 60 A10 10 0 1 0 50 40 Z" fill="url(#logoGrad)"/>
    </svg>
    <div class="header-info">
      <h1>Pravaah</h1>
    </div>
    <div class="status-dot"><div class="dot"></div><span>Active</span></div>
  </div>
  <div class="error-banner" id="error-banner"></div>
  <div class="messages" id="messages">
    <div class="welcome" id="welcome">
      <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M50 10 C30 10 10 30 10 50 C10 70 30 90 50 90 C70 90 90 70 90 50 C90 30 70 10 50 10 Z M50 25 C65 25 75 35 75 50 C75 65 65 75 50 75 C35 75 25 65 25 50 C25 35 35 25 50 25 Z M50 40 A10 10 0 1 0 50 60 A10 10 0 1 0 50 40 Z" fill="url(#logoGrad)"/>
      </svg>
      <h2>Hey, I'm Pravaah</h2>
      <p>Fluid thought, pure expression. Experience the next generation AI chat.</p>
      <div class="welcome-chips">
        <div class="welcome-chip" onclick="quickSend('Who built you and what does Pravaah mean?')">✨ About Pravaah</div>
        <div class="welcome-chip" onclick="quickSend('Explain quantum computing simply')">🔬 Quantum Physics</div>
        <div class="welcome-chip" onclick="quickSend('Write a python script to reverse a string')">💻 Code Snippets</div>
        <div class="welcome-chip" onclick="quickSend('What can you do?')">🚀 Explore Features</div>
      </div>
    </div>
  </div>
  <div class="input-area">
    <div class="input-row">
      <textarea id="inp" rows="1" placeholder="Message Pravaah…" onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
      <button class="send-btn" id="send-btn" onclick="sendMessage()" title="Send">
        <svg viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </button>
    </div>
    <div class="input-hint">Enter to send · Shift+Enter for new line</div>
  </div>
</div>
<script>
const DEFAULT_MODEL = __MODEL_JSON__;
const STORAGE_KEY = "pravaah.history.v3";
let history = [];
let isStreaming = false;

function loadHistory(){
  try{
    const raw = localStorage.getItem(STORAGE_KEY);
    if(!raw) return;
    const data = JSON.parse(raw);
    if(!Array.isArray(data)) return;
    history = data.filter(m => m && m.role && m.content);
    const welcome = document.getElementById("welcome");
    if(history.length && welcome) welcome.remove();
    for(const m of history){
      appendMessage(m.role === "user" ? "user" : "ai", m.content, false);
    }
    scrollBottom();
  }catch(e){ console.warn(e); }
}

function saveHistory(){
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-80)));
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("inp").focus();
  loadHistory();
});

function showError(msg){
  const el = document.getElementById("error-banner");
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 8000);
}

function autoResize(el){
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

function handleKey(e){
  if(e.key === "Enter" && !e.shiftKey){ e.preventDefault(); sendMessage(); }
}

function quickSend(text){
  document.getElementById("inp").value = text;
  sendMessage();
}

async function sendMessage(){
  const inp = document.getElementById("inp");
  const text = inp.value.trim();
  if(!text || isStreaming) return;

  const welcome = document.getElementById("welcome");
  if(welcome) welcome.remove();

  inp.value = "";
  inp.style.height = "auto";

  history.push({ role: "user", content: text });
  appendMessage("user", text);
  saveHistory();

  const typingId = appendTyping();
  setLoading(true);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history, model: DEFAULT_MODEL })
    });

    if(!res.ok){
      let err = "HTTP " + res.status;
      try {
        const j = await res.json();
        if(j.error) err = j.error;
      } catch(_){}
      throw new Error(err);
    }

    removeTyping(typingId);
    const msgId = appendMessage("ai", "");
    const bubble = document.getElementById("bubble-" + msgId);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let full = "";
    let buffer = "";

    while(true){
      const { done, value } = await reader.read();
      if(done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\\n");
      buffer = lines.pop() || "";

      for(const line of lines){
        if(!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if(data === "[DONE]") continue;
        try {
          const j = JSON.parse(data);
          if(j.error) {
            const pieces = [j.error, j.type, j.cause, j.hint].filter(Boolean);
            throw new Error(pieces.join(" | "));
          }
          const delta = j.choices?.[0]?.delta?.content || "";
          if(delta){
            full += delta;
            bubble.innerHTML = renderMarkdown(full);
            scrollBottom();
          }
        } catch(e){
          if(e instanceof SyntaxError) continue;
          throw e;
        }
      }
    }

    if(!full.trim()){
      full = "(No response from the model.)";
      bubble.innerHTML = renderMarkdown(full);
    }

    history.push({ role: "assistant", content: full });
    saveHistory();
  } catch(err){
    removeTyping(typingId);
    appendMessage("ai", "⚠️ " + (err.message || String(err)));
    showError(err.message || String(err));
    history.pop();
    saveHistory();
  } finally {
    setLoading(false);
  }
}

let msgCount = 0;

function appendMessage(role, text, animate = true){
  const id = ++msgCount;
  const msgs = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg " + role;
  if(!animate) div.style.animation = "none";
  
  const userAvatar = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const aiAvatar = `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><path d="M50 10 C30 10 10 30 10 50 C10 70 30 90 50 90 C70 90 90 70 90 50 C90 30 70 10 50 10 Z M50 25 C65 25 75 35 75 50 C75 65 65 75 50 75 C35 75 25 65 25 50 C25 35 35 25 50 25 Z M50 40 A10 10 0 1 0 50 60 A10 10 0 1 0 50 40 Z" fill="url(#logoGrad)"/></svg>`;
  
  div.innerHTML = `
    <div class="avatar">${role === "user" ? userAvatar : aiAvatar}</div>
    <div class="bubble" id="bubble-${id}">${renderMarkdown(text)}</div>
  `;
  msgs.appendChild(div);
  scrollBottom();
  return id;
}

function appendTyping(){
  const id = "typing-" + Date.now();
  const msgs = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg ai";
  div.id = id;
  
  const aiAvatar = `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><path d="M50 10 C30 10 10 30 10 50 C10 70 30 90 50 90 C70 90 90 70 90 50 C90 30 70 10 50 10 Z M50 25 C65 25 75 35 75 50 C75 65 65 75 50 75 C35 75 25 65 25 50 C25 35 35 25 50 25 Z M50 40 A10 10 0 1 0 50 60 A10 10 0 1 0 50 40 Z" fill="url(#logoGrad)"/></svg>`;
  
  div.innerHTML = `
    <div class="avatar">${aiAvatar}</div>
    <div class="bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>
  `;
  msgs.appendChild(div);
  scrollBottom();
  return id;
}

function removeTyping(id){
  const el = document.getElementById(id);
  if(el) el.remove();
}

function scrollBottom(){
  const msgs = document.getElementById("messages");
  msgs.scrollTop = msgs.scrollHeight;
}

function setLoading(v){
  isStreaming = v;
  document.getElementById("send-btn").disabled = v;
}

function escHtml(t){
  return String(t)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

function renderMarkdown(text){
  if(!text) return "";
  let t = escHtml(text);
  t = t.replace(/\`\`\`(\w*)\\n?([\\s\\S]*?)\`\`\`/g, (_, lang, code) =>
    `<pre><button type="button" class="copy-btn" onclick="copyCode(this)">copy</button><code>${code.trim()}</code></pre>`
  );
  t = t.replace(/\`([^\`]+)\`/g, "<code>$1</code>");
  t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/\*(.+?)\*/g, "<em>$1</em>");
  t = t.replace(/^### (.+)$/gm, "<h4 style='margin:.8em 0 .4em'>$1</h4>");
  t = t.replace(/^## (.+)$/gm, "<h3 style='margin:.8em 0 .4em'>$1</h3>");
  t = t.replace(/^# (.+)$/gm, "<h2 style='margin:.8em 0 .4em'>$1</h2>");
  t = t.replace(/\n{2,}/g, "<br/><br/>");
  t = t.replace(/\n/g, "<br/>");
  return t;
}

function copyCode(btn){
  const code = btn.nextElementSibling.textContent;
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = "copied!";
    setTimeout(() => btn.textContent = "copy", 1500);
  });
}
</script>
</body>
</html>"""


def render_index() -> str:
    return (
        HTML.replace("__MODEL__", MODEL)
        .replace("__MODEL_JSON__", json.dumps(MODEL))
    )


@app.route("/")
def index():
    return render_index()


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    model = (data.get("model") or MODEL).strip()

    system_instruction = load_custom_instructions()
    payload_messages = []
    if system_instruction:
        payload_messages.append({"role": "system", "content": system_instruction})
    if isinstance(messages, list):
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "user")
            if role not in ("user", "assistant", "system"):
                role = "user"
            content = m.get("content", "")
            if content is None:
                continue
            content = str(content).strip()
            if not content:
                continue
            payload_messages.append({"role": role, "content": content})

    def generate():
        try:
            extra_body = build_extra_body()
            kwargs = {
                "model": model,
                "messages": payload_messages,
                "stream": True,
                "max_tokens": 4096,
            }
            if extra_body:
                # OpenAI-compatible providers (e.g., Nemotron) may accept provider-specific extra params.
                kwargs["extra_body"] = extra_body
            stream = client.chat.completions.create(
                **kwargs
            )
            for chunk in stream:
                delta = ""
                try:
                    delta = chunk.choices[0].delta.content or ""
                except (AttributeError, IndexError):
                    pass
                if delta:
                    payload = {"choices": [{"delta": {"content": delta}}]}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            # The OpenAI SDK often wraps underlying httpx errors into a generic
            # "Connection error." message. Include the exception type and cause
            # so the UI can show something actionable (DNS/SSL/timeout/etc.).
            cause = getattr(e, "__cause__", None)
            err = {
                "error": str(e) or e.__class__.__name__,
                "type": e.__class__.__name__,
                "cause": (str(cause) if cause else None),
                "hint": (
                    "If this is an SSL/cert issue, set PRAVAAH_VERIFY_SSL=false in .env and retry."
                    if VERIFY_SSL
                    else "SSL verification is disabled (PRAVAAH_VERIFY_SSL=false)."
                ),
            }
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/health")
def health():
    return {
        "ok": True,
        "app": "Pravaah",
        "model": MODEL,
        "base_url": BASE_URL,
        "has_key": bool(API_KEY),
        "instructions_loaded": bool(load_custom_instructions()),
    }


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Pravaah - An experimental AI chatbot built by DKC")
    print(f"  Model:   {MODEL}")
    print(f"  Base:    {BASE_URL}")
    print(f"  Open:    http://localhost:{PORT}")
    print("  Ctrl+C to stop")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG, threaded=True)
