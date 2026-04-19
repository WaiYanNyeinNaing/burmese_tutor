const startLessonBtn = document.getElementById('startLessonBtn');
const input = document.getElementById('inputText');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessagesEl = document.getElementById('chatMessages');
const sendChatBtn = document.getElementById('sendChatBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const chatStatus = document.getElementById('chatStatus');

const chatMessages = [];
let lessonStarted = false;

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatText(text) {
  return escapeHtml(text).replace(/\n/g, '<br>');
}

function setChatBusy(isBusy, label = 'Idle') {
  startLessonBtn.disabled = isBusy;
  sendChatBtn.disabled = isBusy;
  chatInput.disabled = isBusy;
  chatStatus.textContent = label;
  chatStatus.className = isBusy
    ? 'rounded-2xl bg-amber-50 px-3 py-2 text-xs text-amber-700'
    : 'rounded-2xl bg-emerald-50 px-3 py-2 text-xs text-emerald-700';
}

function renderChatMessages() {
  if (!chatMessages.length) {
    chatMessagesEl.innerHTML = `
      <div class="max-w-[85%] rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3 text-sm leading-7 text-slate-600 shadow-sm">
        ဘယ်ဘက်မှာ source text ထည့်ပြီး <strong>Start Lesson</strong> ကိုနှိပ်ပါ။ Burmese Tutor က စတင်မေးပြီး lesson ကို တစ်ချက်ချင်းသင်ပေးပါမယ်။
      </div>
    `;
    return;
  }

  chatMessagesEl.innerHTML = chatMessages.map((message) => {
    const isUser = message.role === 'user';
    const bubbleClass = isUser
      ? 'ml-auto bg-slate-900 text-white rounded-tr-md'
      : 'mr-auto bg-white text-slate-800 rounded-tl-md border border-slate-200';
    const label = isUser ? 'You' : 'Burmese Tutor';
    return `
      <div class="flex ${isUser ? 'justify-end' : 'justify-start'}">
        <div class="max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-7 shadow-sm ${bubbleClass}">
          <div class="mb-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${isUser ? 'text-slate-300' : 'text-slate-400'}">${label}</div>
          <div>${formatText(message.content)}</div>
        </div>
      </div>
    `;
  }).join('');

  chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

async function streamResponse(url, payload, assistantMessage) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });

  if (!res.ok || !res.body) {
    throw new Error(`Request failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);

      if (event.error) {
        throw new Error(event.error);
      }

      if (event.delta) {
        assistantMessage.content += event.delta;
        renderChatMessages();
      }
    }

    if (done) {
      if (buffer.trim()) {
        const finalEvent = JSON.parse(buffer);
        if (finalEvent.error) {
          throw new Error(finalEvent.error);
        }
        if (finalEvent.delta) {
          assistantMessage.content += finalEvent.delta;
          renderChatMessages();
        }
      }
      return;
    }
  }
}

async function startLesson() {
  const sourceText = input.value.trim();
  if (!sourceText) {
    setChatBusy(false, 'Need text');
    chatMessages.length = 0;
    chatMessages.push({
      role: 'assistant',
      content: 'Lesson စတင်ဖို့ ဘယ်ဘက်မှာ study text ကို paste လုပ်ပေးပါ။',
    });
    renderChatMessages();
    return;
  }

  chatMessages.length = 0;
  const assistantMessage = { role: 'assistant', content: '' };
  chatMessages.push(assistantMessage);
  renderChatMessages();
  setChatBusy(true, 'Starting...');

  try {
    await streamResponse('/api/tutor/start', { sourceText }, assistantMessage);
    if (!assistantMessage.content.trim()) {
      assistantMessage.content = 'Lesson start response was empty.';
      renderChatMessages();
    }
    lessonStarted = true;
    setChatBusy(false, 'Lesson ready');
  } catch (error) {
    assistantMessage.content = `Error: ${String(error)}`;
    renderChatMessages();
    lessonStarted = false;
    setChatBusy(false, 'Error');
  } finally {
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    startLessonBtn.disabled = false;
    chatInput.focus();
  }
}

startLessonBtn.addEventListener('click', startLesson);

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const content = chatInput.value.trim();
  if (!content) return;
  if (!lessonStarted) {
    await startLesson();
    return;
  }

  const userMessage = { role: 'user', content };
  const assistantMessage = { role: 'assistant', content: '' };

  chatMessages.push(userMessage, assistantMessage);
  renderChatMessages();
  chatInput.value = '';
  setChatBusy(true, 'Streaming...');

  try {
    await streamResponse(
      '/api/chat',
      { messages: chatMessages.slice(0, -1), sourceText: input.value.trim() },
      assistantMessage
    );
    if (!assistantMessage.content.trim()) {
      assistantMessage.content = 'No response received.';
      renderChatMessages();
    }
    setChatBusy(false, 'Done');
  } catch (error) {
    assistantMessage.content = `Error: ${String(error)}`;
    renderChatMessages();
    setChatBusy(false, 'Error');
  } finally {
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    chatInput.focus();
  }
});

chatInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

clearChatBtn.addEventListener('click', () => {
  chatMessages.length = 0;
  lessonStarted = false;
  renderChatMessages();
  setChatBusy(false, 'Idle');
  chatInput.focus();
});
