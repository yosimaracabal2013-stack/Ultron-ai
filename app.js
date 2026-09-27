const form = document.querySelector('#chatForm');
const input = document.querySelector('#messageInput');
const messages = document.querySelector('#messages');
const voiceBtn = document.querySelector('#voiceBtn');
const clearBtn = document.querySelector('#clearBtn');
const statusText = document.querySelector('#statusText');
const API_URL = window.ULTRON_API_URL || '';

function addMessage(text, role) {
  const article = document.createElement('article');
  article.className = `message ${role}`;
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'assistant' ? 'U' : 'Y';
  const wrap = document.createElement('div');
  wrap.className = 'bubble-wrap';
  const speaker = document.createElement('span');
  speaker.className = 'speaker';
  speaker.textContent = role === 'assistant' ? 'ULTRON' : 'YOU';
  const time = document.createElement('time');
  time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  speaker.append(' ', time);
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  wrap.append(speaker, bubble);
  article.append(avatar, wrap);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

async function askUltron(text) {
  if (!API_URL) {
    return 'ULTRON is not connected to its inference server yet. Set ULTRON_API_URL to the server address.';
  }
  const response = await fetch(API_URL + '/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, max_tokens: 160, temperature: 0.8 })
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'ULTRON server error');
  return data.reply;
}

async function updateConnectionStatus() {
  if (!API_URL) {
    statusText.textContent = 'SYSTEM ONLINE · BACKEND NOT SET';
    return;
  }
  try {
    const response = await fetch(API_URL + '/health');
    if (!response.ok) throw new Error('offline');
    statusText.textContent = 'SYSTEM ONLINE · ULTRON v0.2';
  } catch {
    statusText.textContent = 'ULTRON SERVER OFFLINE';
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  addMessage(text, 'user');
  input.value = '';
  addMessage('Thinking…', 'assistant');
  const thinkingMessage = messages.lastElementChild;
  try {
    const reply = await askUltron(text);
    thinkingMessage.querySelector('.bubble').textContent = reply;
  } catch (error) {
    thinkingMessage.querySelector('.bubble').textContent = 'I could not reach my AI brain right now. Check the ULTRON server connection.';
    statusText.textContent = 'ULTRON SERVER OFFLINE';
  }
});

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearBtn.addEventListener('click', () => {
  messages.replaceChildren();
  addMessage("Conversation cleared. I'm standing by in demo mode.", 'assistant');
});

let recognition = null;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = navigator.language || 'en-US';
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.addEventListener('start', () => {
    voiceBtn.classList.add('listening');
    voiceBtn.setAttribute('aria-label', 'Stop voice input');
    statusText.textContent = 'MICROPHONE LISTENING';
  });
  recognition.addEventListener('result', (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript;
    if (transcript) {
      input.value = transcript;
      input.focus();
    }
  });
  recognition.addEventListener('error', () => {
    statusText.textContent = 'VOICE INPUT UNAVAILABLE';
  });
  recognition.addEventListener('end', () => {
    voiceBtn.classList.remove('listening');
    voiceBtn.setAttribute('aria-label', 'Start voice input');
    statusText.textContent = API_URL ? 'SYSTEM ONLINE · ULTRON v0.2' : 'SYSTEM ONLINE · BACKEND NOT SET';
  });
}

voiceBtn.addEventListener('click', () => {
  if (!recognition) {
    addMessage('Speech recognition is not supported in this browser. You can still type messages.', 'assistant');
    return;
  }
  try {
    recognition.start();
  } catch (error) {
    statusText.textContent = 'VOICE INPUT ALREADY ACTIVE';
  }
});


updateConnectionStatus();

updateConnectionStatus();
