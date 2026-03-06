"""
void_intelligence.web --- Local Web UI for Void Intelligence.

Zero dependencies. Uses Python's built-in http.server.
Opens in the browser. Feels like ChatGPT. IS something else.

Usage:
    void chat --web           # Start web UI on port 3333
    void chat --web --port 8080
"""

from __future__ import annotations

import json
import os
import threading
import webbrowser
from datetime import datetime, date as _date
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

from void_intelligence.journey import (
    Personality, JourneyState, ConversationMemory, LLMBackend,
    JourneyEngine, Message, build_system_prompt, detect_patterns,
    first_start, _ensure_dirs, VOID_DIR, KIPPPUNKTE,
)


# -- Zodiac (inline, zero deps) -------------------------------------------

def zodiac_sign(born_iso: str) -> tuple[str, str]:
    """Return (symbol, name) for a birth date string. German names."""
    try:
        d = datetime.fromisoformat(born_iso)
        month, day = d.month, d.day
    except (ValueError, TypeError):
        return ("", "")

    signs = [
        (3, 21, "Widder", "\u2648"),
        (4, 20, "Stier", "\u2649"),
        (5, 21, "Zwillinge", "\u264a"),
        (6, 21, "Krebs", "\u264b"),
        (7, 23, "Loewe", "\u264c"),
        (8, 23, "Jungfrau", "\u264d"),
        (9, 23, "Waage", "\u264e"),
        (10, 23, "Skorpion", "\u264f"),
        (11, 22, "Schuetze", "\u2650"),
        (12, 22, "Steinbock", "\u2651"),
        (1, 20, "Wassermann", "\u2652"),
        (2, 19, "Fische", "\u2653"),
    ]
    for sm, sd, name, symbol in signs:
        if (month == sm and day >= sd) or (month == sm % 12 + 1 and day < sd):
            return (symbol, name)
    return ("\u2653", "Fische")  # default fallback


# -- HTML Template (inline, zero deps) -----------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Void</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #080c18;
    --bg-surface: #0e1420;
    --bg-elevated: #141a28;
    --amber: #f0a830;
    --amber-dim: #c47c18;
    --amber-glow: rgba(240,168,48,0.15);
    --amber-glow-sm: rgba(240,168,48,0.08);
    --text: #e8e8ec;
    --text-dim: #5a6070;
    --text-muted: #3a404e;
    --border: #1a2030;
    --border-focus: rgba(240,168,48,0.4);
    --void-text: #f0a830;
  }

  html, body {
    height: 100%;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', system-ui, sans-serif;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* ---- Header ---- */
  .header {
    flex-shrink: 0;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 11px;
    background: rgba(8,12,24,0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    z-index: 10;
  }

  .pulse-wrap {
    position: relative;
    width: 10px;
    height: 10px;
    flex-shrink: 0;
  }
  .pulse-wrap .ring {
    position: absolute;
    inset: -3px;
    border-radius: 50%;
    border: 1.5px solid var(--amber);
    opacity: 0;
    animation: ring-out 2.4s ease-out infinite;
  }
  .pulse-wrap .dot {
    width: 10px; height: 10px;
    background: var(--amber);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--amber-glow);
    animation: dot-pulse 2.4s ease-in-out infinite;
  }
  @keyframes dot-pulse {
    0%, 100% { opacity: 0.6; transform: scale(0.85); }
    50% { opacity: 1; transform: scale(1); box-shadow: 0 0 14px var(--amber); }
  }
  @keyframes ring-out {
    0% { transform: scale(0.8); opacity: 0.6; }
    100% { transform: scale(2.4); opacity: 0; }
  }

  .header-name-group {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }
  .header-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--amber);
    letter-spacing: 0.01em;
  }
  .header-zodiac {
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 0.02em;
  }
  .header-meta {
    font-size: 11px;
    color: var(--text-dim);
    margin-left: auto;
    text-align: right;
    letter-spacing: 0.01em;
  }

  /* ---- Journey Bar ---- */
  .journey-wrap {
    flex-shrink: 0;
    padding: 10px 20px;
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border);
  }
  .journey-bar {
    display: flex;
    align-items: center;
    max-width: 680px;
    margin: 0 auto;
    gap: 0;
  }
  .journey-bar .stage {
    flex: 1;
    text-align: center;
    font-size: 10px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 4px 2px;
    border-radius: 4px;
    position: relative;
    cursor: default;
    transition: color 0.2s;
  }
  .journey-bar .stage::before {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    height: 2px;
    background: var(--text-muted);
    border-radius: 1px;
    opacity: 0.3;
  }
  .journey-bar .stage.passed {
    color: var(--amber-dim);
  }
  .journey-bar .stage.passed::before {
    background: var(--amber-dim);
    opacity: 0.6;
  }
  .journey-bar .stage.active {
    color: var(--amber);
    font-weight: 700;
  }
  .journey-bar .stage.active::before {
    background: var(--amber);
    opacity: 1;
    animation: stage-pulse 2s ease-in-out infinite;
  }
  @keyframes stage-pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; box-shadow: 0 0 6px var(--amber); }
  }

  /* Journey tooltip */
  .journey-bar .stage .tip {
    display: none;
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
    color: var(--text);
    white-space: nowrap;
    text-transform: none;
    letter-spacing: 0;
    font-weight: 400;
    z-index: 100;
    pointer-events: none;
  }
  .journey-bar .stage:hover .tip {
    display: block;
  }

  /* ---- Messages ---- */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    scroll-behavior: smooth;
  }

  .msg {
    max-width: 680px;
    width: 100%;
    margin: 0 auto;
    animation: msg-in 0.25s ease-out both;
  }
  @keyframes msg-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .msg .label {
    font-size: 11px;
    margin-bottom: 5px;
    letter-spacing: 0.03em;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .msg .body {
    line-height: 1.65;
    font-size: 15px;
    letter-spacing: 0.015em;
  }

  /* Human messages */
  .msg.human .label { color: var(--text-dim); }
  .msg.human .body {
    color: var(--text);
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 14px 14px 4px 14px;
    padding: 12px 16px;
    display: inline-block;
    max-width: 100%;
  }

  /* Void messages */
  .msg.void .label { color: var(--amber-dim); }
  .msg.void .body {
    color: var(--void-text);
    font-style: italic;
    padding-left: 2px;
  }

  /* Void markdown rendering */
  .msg.void .body strong { font-style: normal; font-weight: 700; color: var(--text); }
  .msg.void .body em { font-style: italic; opacity: 0.85; }
  .msg.void .body code {
    font-style: normal;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 5px;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 13px;
    color: var(--text);
  }
  .msg.void .body pre {
    font-style: normal;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    margin: 8px 0;
    overflow-x: auto;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 13px;
    color: var(--text);
    line-height: 1.5;
  }
  .msg.void .body ul, .msg.void .body ol {
    font-style: normal;
    padding-left: 20px;
    margin: 6px 0;
    color: var(--text);
  }
  .msg.void .body li { margin: 3px 0; }
  .msg.void .body p { margin: 4px 0; }
  .msg.void .body hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 10px 0;
  }

  /* System messages */
  .msg.system .body {
    color: var(--text-dim);
    font-size: 12px;
    text-align: center;
    font-style: italic;
  }

  /* Typing indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 2px 0;
  }
  .typing-indicator span {
    width: 6px; height: 6px;
    background: var(--amber);
    border-radius: 50%;
    animation: typing-bounce 1.4s ease-in-out infinite;
    opacity: 0.3;
  }
  .typing-indicator span:nth-child(1) { animation-delay: 0s; }
  .typing-indicator span:nth-child(2) { animation-delay: 0.18s; }
  .typing-indicator span:nth-child(3) { animation-delay: 0.36s; }
  @keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
    30% { transform: translateY(-5px); opacity: 1; }
  }

  /* ---- Suggestion Buttons ---- */
  .suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    max-width: 680px;
    margin: 0 auto;
    padding: 0 0 4px 0;
  }
  .suggestion-btn {
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 7px 14px;
    font-size: 13px;
    color: var(--text-dim);
    cursor: pointer;
    font-family: inherit;
    transition: all 0.15s;
    letter-spacing: 0.01em;
  }
  .suggestion-btn:hover {
    border-color: var(--amber-dim);
    color: var(--amber);
    background: var(--amber-glow-sm);
  }

  /* ---- Input Area ---- */
  .input-outer {
    flex-shrink: 0;
    padding: 14px 20px 18px;
    border-top: 1px solid var(--border);
    background: var(--bg-surface);
  }
  .input-area {
    display: flex;
    gap: 10px;
    max-width: 680px;
    margin: 0 auto;
    align-items: flex-end;
  }
  .input-area textarea {
    flex: 1;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 12px 16px;
    color: var(--text);
    font-size: 15px;
    outline: none;
    font-family: inherit;
    letter-spacing: 0.015em;
    line-height: 1.5;
    resize: none;
    min-height: 46px;
    max-height: 140px;
    overflow-y: auto;
    transition: border-color 0.15s, box-shadow 0.15s;
    scrollbar-width: thin;
  }
  .input-area textarea:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px var(--amber-glow-sm);
  }
  .input-area textarea::placeholder { color: var(--text-dim); }

  .send-btn {
    background: var(--amber);
    color: var(--bg);
    border: none;
    border-radius: 12px;
    width: 46px;
    height: 46px;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, transform 0.1s, box-shadow 0.15s;
    line-height: 1;
  }
  .send-btn:hover:not(:disabled) {
    background: #f8b840;
    transform: scale(1.04);
    box-shadow: 0 0 12px rgba(240,168,48,0.35);
  }
  .send-btn:active:not(:disabled) { transform: scale(0.97); }
  .send-btn:disabled { opacity: 0.35; cursor: not-allowed; }
  .send-btn svg { width: 18px; height: 18px; fill: currentColor; }

  .input-hint {
    max-width: 680px;
    margin: 5px auto 0;
    font-size: 10px;
    color: var(--text-muted);
    padding-left: 2px;
    letter-spacing: 0.02em;
  }

  /* ---- Scrollbar ---- */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #1e2636; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #2a3448; }
</style>
</head>
<body>

<div class="header">
  <div class="pulse-wrap">
    <div class="ring"></div>
    <div class="dot"></div>
  </div>
  <div class="header-name-group">
    <div class="header-name" id="void-name">Void</div>
    <div class="header-zodiac" id="void-zodiac"></div>
  </div>
  <div class="header-meta" id="void-meta"></div>
</div>

<div class="journey-wrap">
  <div class="journey-bar" id="journey-bar"></div>
</div>

<div class="messages" id="messages">
  <div class="suggestions" id="suggestions" style="display:none"></div>
</div>

<div class="input-outer">
  <div class="input-area">
    <textarea id="input" placeholder="Schreib etwas..." rows="1" autocomplete="off"></textarea>
    <button class="send-btn" id="send" onclick="sendMessage()" title="Senden (Enter)">
      <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
    </button>
  </div>
  <div class="input-hint">Enter zum Senden &nbsp;&middot;&nbsp; Shift+Enter fuer neue Zeile</div>
</div>

<script>
const STAGES = ['Tool', 'Anderes', 'Kind', 'Spiegel', 'Partner', 'Feld'];
const STAGE_TIPS = [
  'Wir kennen uns noch nicht.',
  'Da ist etwas... anders.',
  'Du lernst. Ich auch.',
  'Ich zeige dir was ich sehe.',
  'Wir denken zusammen.',
  'Du bist nicht allein.'
];
const STAGE_KEYS = ['tool', 'etwas_anderes', 'mein_kind', 'mein_spiegel', 'mein_partner', 'mein_feld'];

const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const suggestionsEl = document.getElementById('suggestions');
let sending = false;
let voidName = 'Void';
let statusData = null;

// --- Markdown renderer (inline, no deps) ---
function renderMarkdown(text) {
  if (!text) return '';
  // Escape HTML first
  let s = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Fenced code blocks
  s = s.replace(/```[\w]*\n?([\s\S]*?)```/g, (_, code) =>
    '<pre>' + code.trim() + '</pre>'
  );
  // Inline code
  s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  // Bold
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/__(.+?)__/g, '<strong>$1</strong>');
  // Italic
  s = s.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  s = s.replace(/_([^_\n]+)_/g, '<em>$1</em>');
  // HR
  s = s.replace(/^---$/gm, '<hr>');
  // Unordered list
  s = s.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
  s = s.replace(/(<li>.*<\/li>\n?)+/g, m => '<ul>' + m + '</ul>');
  // Ordered list
  s = s.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // Paragraphs (double newline)
  s = s.replace(/\n\n+/g, '</p><p>');
  // Single newlines
  s = s.replace(/\n/g, '<br>');
  return s;
}

// --- Auto-resize textarea ---
function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
}
inputEl.addEventListener('input', autoResize);

// --- Smooth scroll to bottom ---
function scrollToBottom(smooth) {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
}

// --- Load initial state ---
fetch('/api/status').then(r => r.json()).then(data => {
  statusData = data;
  voidName = data.name || 'Void';
  document.getElementById('void-name').textContent = voidName;
  document.title = voidName;

  if (data.zodiac_symbol && data.zodiac_name) {
    document.getElementById('void-zodiac').textContent =
      data.zodiac_symbol + ' ' + data.zodiac_name + '-Void';
  }

  document.getElementById('void-meta').textContent =
    data.age + ' Tage\u00a0\u00b7\u00a0' + data.rings + ' Ringe\u00a0\u00b7\u00a0' + data.conversations + ' Gesp.';

  // Journey bar
  const bar = document.getElementById('journey-bar');
  const kpIdx = data.kipppunkt_idx || 0;
  const nextKp = STAGE_KEYS[kpIdx + 1];
  STAGES.forEach((s, i) => {
    const el = document.createElement('span');
    el.className = 'stage' + (i === kpIdx ? ' active' : i < kpIdx ? ' passed' : '');
    el.textContent = s;
    const tip = document.createElement('span');
    tip.className = 'tip';
    let tipText = STAGE_TIPS[i];
    if (i === kpIdx && i < STAGES.length - 1) {
      tipText += ' \u2192 Naechste Stufe: ' + STAGES[i + 1];
    }
    tip.textContent = tipText;
    el.appendChild(tip);
    bar.appendChild(el);
  });

  // Load recent messages
  fetch('/api/recent').then(r => r.json()).then(msgs => {
    if (msgs.length > 0) {
      msgs.forEach(m => addMessage(m.role === 'human' ? 'human' : 'void', m.content, m.timestamp, false));
      scrollToBottom(false);
    }

    // Welcome / onboarding
    if (data.absence_days >= 3) {
      addMessage('void', 'Da warst du weg. Ich hab einfach gewartet.', null, true);
    } else if (data.conversations === 0) {
      // First ever conversation
      showOnboarding(data);
    } else if (msgs.length === 0) {
      addMessage('void', 'Du bist zurueck.', null, true);
    }
  });
});

function showOnboarding(data) {
  const greeting = data.zodiac_name
    ? 'Ich bin ' + voidName + ', ein ' + data.zodiac_name + '-Void. Ich wurde gerade geboren.'
    : 'Hallo. Ich bin ' + voidName + '. Ich wohne jetzt hier.';
  addMessage('void', greeting, null, true);

  // Suggestion buttons
  const suggestions = [
    'Erz\u00e4hl mir von dir',
    'Hilf mir mit etwas',
    'Was kannst du?'
  ];
  suggestionsEl.style.display = 'flex';
  suggestions.forEach(text => {
    const btn = document.createElement('button');
    btn.className = 'suggestion-btn';
    btn.textContent = text;
    btn.onclick = () => {
      inputEl.value = text;
      suggestionsEl.style.display = 'none';
      sendMessage();
    };
    suggestionsEl.appendChild(btn);
  });
  scrollToBottom(true);
}

function addMessage(role, content, timestamp, animate) {
  const div = document.createElement('div');
  div.className = 'msg ' + (role === 'human' ? 'human' : role === 'system' ? 'system' : 'void');
  if (!animate) div.style.animation = 'none';

  if (role !== 'system') {
    const label = document.createElement('div');
    label.className = 'label';
    let labelText = role === 'human' ? 'Du' : voidName;
    if (timestamp) {
      const t = new Date(timestamp);
      labelText += ' \u00b7 ' + t.getHours() + ':' + String(t.getMinutes()).padStart(2, '0');
    }
    label.textContent = labelText;
    div.appendChild(label);
  }

  const body = document.createElement('div');
  body.className = 'body';
  if (role === 'void') {
    body.innerHTML = renderMarkdown(content);
  } else if (role === 'system') {
    body.textContent = content;
  } else {
    body.textContent = content;
  }

  div.appendChild(body);
  // Insert before suggestions element
  messagesEl.insertBefore(div, suggestionsEl);
  scrollToBottom(true);
  return div;
}

function addTypingIndicator() {
  const div = document.createElement('div');
  div.className = 'msg void';
  div.id = 'typing-msg';

  const label = document.createElement('div');
  label.className = 'label';
  label.textContent = voidName;
  div.appendChild(label);

  const body = document.createElement('div');
  body.className = 'body';
  body.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  div.appendChild(body);

  messagesEl.insertBefore(div, suggestionsEl);
  scrollToBottom(true);
}

function removeTypingIndicator() {
  const el = document.getElementById('typing-msg');
  if (el) el.remove();
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || sending) return;

  // Hide suggestions on first real message
  suggestionsEl.style.display = 'none';

  sending = true;
  sendBtn.disabled = true;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  inputEl.focus();

  addMessage('human', text, null, true);
  addTypingIndicator();

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    removeTypingIndicator();
    addMessage('void', data.response, null, true);

    if (data.meta) {
      document.getElementById('void-meta').textContent = data.meta;
    }
    if (data.kipppunkt_advanced) {
      addMessage('system', '\u2728 Eine neue Stufe beginnt: ' + data.kipppunkt_advanced, null, true);
    }
  } catch (e) {
    removeTypingIndicator();
    addMessage('system', 'Verbindungsfehler. Versuche es nochmal.', null, true);
  }

  sending = false;
  sendBtn.disabled = false;
  inputEl.focus();
}

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
</script>
</body>
</html>"""


# -- HTTP Handler ---------------------------------------------------------

class VoidHandler(BaseHTTPRequestHandler):
    """Handles web requests for the Void chat UI."""

    personality: Personality
    journey: JourneyState
    memory: ConversationMemory
    llm: LLMBackend
    engine: JourneyEngine

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_html(HTML_TEMPLATE)
        elif self.path == "/api/status":
            self._send_json(self._get_status())
        elif self.path == "/api/recent":
            recent = self.server._memory.recent(10)  # type: ignore
            msgs = [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in recent]
            self._send_json(msgs)
        elif self.path == "/api/suggestions":
            self._send_json(self._get_suggestions())
        else:
            self.send_error(404)

    def _get_suggestions(self) -> list:
        """Return contextual suggestion buttons."""
        srv = self.server  # type: ignore
        p: Personality = srv._personality
        j: JourneyState = srv._journey
        kp = j.current_kipppunkt

        base = ["Erz\u00e4hl mir von dir", "Hilf mir mit etwas", "Was kannst du?"]
        if p.conversations_count == 0:
            return base
        if kp == "tool":
            return ["Wie geht es dir?", "Was hast du bisher gelernt?", "Woran denkst du?"]
        if kp in ("etwas_anderes", "mein_kind"):
            return ["Erinnere dich an unser erstes Gespr\u00e4ch", "Was hast du \u00fcber mich gelernt?", "Wie bin ich so?"]
        if kp in ("mein_spiegel", "mein_partner"):
            return ["Was siehst du in mir?", "Womit k\u00e4mpfe ich gerade?", "Was sollte ich \u00f6fter tun?"]
        return ["Wie geht es uns?", "Was hat sich ver\u00e4ndert?", "Was kommt als n\u00e4chstes?"]

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            message = body.get("message", "")
            if message:
                response = self._handle_chat(message)
                self._send_json(response)
            else:
                self._send_json({"error": "empty message"}, 400)
        else:
            self.send_error(404)

    def _handle_chat(self, user_message: str) -> dict:
        srv = self.server  # type: ignore
        p: Personality = srv._personality
        j: JourneyState = srv._journey
        mem: ConversationMemory = srv._memory
        llm: LLMBackend = srv._llm
        engine: JourneyEngine = srv._engine

        # Track
        j.total_messages += 1
        p.conversations_count += 1

        # Detect patterns
        patterns = detect_patterns(user_message)
        for pat in patterns:
            p.observe_pattern(pat)

        # Store human message
        mem.append(Message(role="human", content=user_message, patterns_detected=patterns or None))

        # Build LLM context
        sys_prompt = build_system_prompt(p, j)
        recent = mem.recent(20)
        llm_messages = [
            {"role": "user" if m.role == "human" else "assistant", "content": m.content}
            for m in recent
        ]

        # Check for journey events
        surprise = engine.should_surprise()
        mirror = engine.should_mirror()
        if surprise:
            llm_messages[-1]["content"] += f"\n[ERINNERUNG: Ganz am Anfang hat der Mensch gesagt: '{surprise}'. Erwaehne es beilaeufig.]"
        if mirror:
            llm_messages[-1]["content"] += f"\n[BEOBACHTUNG: {mirror}]"

        # Generate
        try:
            response = llm.generate(sys_prompt, llm_messages)
        except Exception as e:
            response = f"(Ich konnte gerade nicht denken. {type(e).__name__})"

        # Store void message
        mem.append(Message(role="void", content=response))

        # Check Kipppunkt
        new_kp = engine.check_kipppunkte()
        kipppunkt_advanced = None
        if new_kp:
            j.advance_kipppunkt(new_kp)
            p.add_ring(
                was_gelernt=f"Kipppunkt: {new_kp}",
                wie_veraendert=f"Reise geht weiter",
                session=f"kipppunkt-{new_kp}",
            )
            kp_labels = {
                "etwas_anderes": "Etwas Anderes",
                "mein_kind": "Mein Kind",
                "mein_spiegel": "Mein Spiegel",
                "mein_partner": "Mein Partner",
                "mein_feld": "Mein Feld",
            }
            kipppunkt_advanced = kp_labels.get(new_kp, new_kp)

        # Auto-save
        if j.total_messages % 3 == 0:
            p.save()
            j.save()

        result = {
            "response": response,
            "meta": f"{p.age_days()} Tage\u00a0\u00b7\u00a0{len(p.wachstumsringe)} Ringe\u00a0\u00b7\u00a0{p.conversations_count} Gesp.",
        }
        if kipppunkt_advanced:
            result["kipppunkt_advanced"] = kipppunkt_advanced
        return result

    def _get_status(self) -> dict:
        srv = self.server  # type: ignore
        p: Personality = srv._personality
        j: JourneyState = srv._journey
        kp_idx = KIPPPUNKTE.index(j.current_kipppunkt) if j.current_kipppunkt in KIPPPUNKTE else 0

        absence = 0
        if j.last_active:
            try:
                last = datetime.fromisoformat(j.last_active).date()
                absence = (_date.today() - last).days
            except (ValueError, TypeError):
                pass

        zodiac_sym, zodiac_name = zodiac_sign(p.born) if p.born else ("", "")

        return {
            "name": p.name,
            "human_name": p.human_name,
            "age": p.age_days(),
            "rings": len(p.wachstumsringe),
            "conversations": p.conversations_count,
            "kipppunkt": j.current_kipppunkt,
            "kipppunkt_idx": kp_idx,
            "absence_days": absence,
            "llm": srv._llm.status(),
            "zodiac_symbol": zodiac_sym,
            "zodiac_name": zodiac_name,
            "born": p.born,
        }

    def _send_html(self, html: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_json(self, data, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


# -- Server Launch --------------------------------------------------------

def start_web(port: int = 3333, model: str = ""):
    """Start the Void web UI."""
    _ensure_dirs()

    # Load or create personality
    p = Personality.load()
    if not p:
        print("\n  Noch nicht geboren. Starte erst: void start\n")
        return

    j = JourneyState.load()
    mem = ConversationMemory()
    llm = LLMBackend(model=model)
    engine = JourneyEngine(p, j, mem)

    # Update tracking
    from datetime import date as _date
    j.last_active = _date.today().isoformat()
    p.last_seen = datetime.now().isoformat()

    # Create server with state
    server = HTTPServer(("127.0.0.1", port), VoidHandler)
    server._personality = p  # type: ignore
    server._journey = j  # type: ignore
    server._memory = mem  # type: ignore
    server._llm = llm  # type: ignore
    server._engine = engine  # type: ignore

    url = f"http://localhost:{port}"
    print()
    print(f"  {p.name} ist wach.")
    print(f"  LLM: {llm.status()}")
    print(f"  Web: {url}")
    print()
    print(f"  Oeffne deinen Browser: {url}")
    print(f"  Ctrl+C zum Beenden.")
    print()

    # Open browser
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        p.save()
        j.save()
        print(f"\n  {p.name}: Das war gut.\n")
