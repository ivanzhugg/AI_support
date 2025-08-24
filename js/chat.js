(function () {
  // ---------- Конфиг внешнего вида ----------
  const ACCENT_COLOR = 'rgb(198, 42, 30)';
  const CHAT_BG_COLOR = 'rgb(228, 230, 232)';
  const ONLINE_INDICATOR = 'rgb(34, 197, 94)';
  const AGENT_NAME = 'Биба';
  const AVATAR_URL = new URL('/static/avatar.png', document.currentScript.src).href;



  // ---------- Конфиг API ----------
  const currentScript = document.currentScript;
  const API_BASE = "https://n8nsolution.ru/api";
  const REPLY_URL = `${API_BASE}/v1/reply`;

  // ---------- Новый SID при каждом обновлении страницы ----------
  function fallbackUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      const v = c === "x" ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  const SID = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : fallbackUUID();

  // ---------- Подготовка DOM ----------
  function init() {
    if (document.getElementById('chat-widget-container')) return;

    // Tailwind
    const tw = document.createElement('link');
    tw.rel = 'stylesheet';
    tw.href = 'https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.16/tailwind.min.css';
    document.head.appendChild(tw);

    // Стили + анимация «печатает…»
    const style = document.createElement('style');
    style.innerHTML = `
      .hidden { display: none; }
      #chat-widget-container {
        position: fixed; bottom: 20px; right: 20px;
        display: flex; flex-direction: column; z-index: 2147483647;
      }
      #chat-popup {
        height: 70vh; max-height: 70vh; transition: all .3s;
        overflow: hidden; background-color: ${CHAT_BG_COLOR};
        border-radius: .5rem; box-shadow: 0 8px 24px rgba(0,0,0,.12);
      }
      @media (max-width: 768px) {
        #chat-popup {
          position: fixed; top: 0; right: 0; bottom: 0; left: 0;
          width: 100%; height: 100%; max-height: 100%; border-radius: 0;
        }
      }
      .typing-bar {
        display: inline-flex; align-items: center; gap: .35rem;
        font-size: 12px; color: #6b7280;
      }
      .typing-bar .dots { display: inline-flex; gap: .18rem; }
      .typing-bar .dot {
        width: .35rem; height: .35rem; border-radius: 50%;
        background: #9ca3af; opacity: .3; animation: blink 1s infinite;
      }
      .typing-bar .dot:nth-child(2){ animation-delay: .2s; }
      .typing-bar .dot:nth-child(3){ animation-delay: .4s; }
      @keyframes blink {
        0%, 20% { opacity: .3; transform: translateY(0); }
        50%     { opacity: 1;  transform: translateY(-1px); }
        100%    { opacity: .3; transform: translateY(0); }
      }
    `;
    document.head.appendChild(style);

    // Контейнер и разметка
    const container = document.createElement('div');
    container.id = 'chat-widget-container';
    container.innerHTML = `
      <!-- Плавающая кнопка -->
      <div id="chat-bubble"
           class="w-16 h-16 rounded-full flex items-center justify-center cursor-pointer shadow-lg"
           style="background-color:${ACCENT_COLOR};color:#fff;"
           title="Открыть чат">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>

      <!-- Всплывающее окно -->
      <div id="chat-popup" class="hidden absolute bottom-20 right-0 w-96 flex flex-col text-sm">
        <!-- Шапка -->
        <div id="chat-header" class="flex items-center justify-between p-4 rounded-t-md"
             style="background-color:${ACCENT_COLOR};color:#fff;">
          <div class="flex items-center">
            <img src="${AVATAR_URL}" alt="Avatar" class="rounded-full w-8 h-8 mr-2" />
            <div class="leading-tight">
              <div class="text-base font-semibold">${AGENT_NAME}</div>
              <div class="flex items-center text-xs">
                <span class="inline-block w-2 h-2 rounded-full mr-1" style="background-color:${ONLINE_INDICATOR};"></span>
                <span>онлайн</span>
              </div>
            </div>
          </div>
          <button id="close-popup" class="bg-transparent border-none cursor-pointer" style="color:#fff;">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Сообщения (скролл) -->
        <div id="chat-messages" class="flex-1 p-4 overflow-y-auto space-y-3"></div>

        <!-- Полоса «печатает…», закреплена под списком сообщений -->
        <div id="typing-indicator" class="hidden px-4 pb-1">
          <div class="typing-bar">
            <span>печатает</span>
            <span class="dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </span>
          </div>
        </div>

        <!-- Панель ввода -->
        <div id="chat-input-container" class="p-4 border-t" style="background-color:${CHAT_BG_COLOR}; border-color: rgba(0,0,0,.1);">
          <div class="flex space-x-4 items-center">
            <input type="text" id="chat-input"
                   class="flex-1 rounded-md px-4 py-2 outline-none border border-gray-300"
                   placeholder="Введите сообщение..." autocomplete="off" />
            <button id="chat-submit" class="rounded-md px-4 py-2 cursor-pointer shadow"
                    style="background-color:${ACCENT_COLOR};color:#fff;">
              Отправить
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(container);

    // Элементы
    const chatBubble = document.getElementById('chat-bubble');
    const chatPopup = document.getElementById('chat-popup');
    const closePopup = document.getElementById('close-popup');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSubmit = document.getElementById('chat-submit');
    const typingWrap = document.getElementById('typing-indicator');

    // Тогглер окна
    function togglePopup() {
      chatPopup.classList.toggle('hidden');
      if (!chatPopup.classList.contains('hidden')) chatInput.focus();
      // при закрытии — на всякий случай прячем индикатор
      if (chatPopup.classList.contains('hidden')) hideTyping();
    }
    chatBubble.addEventListener('click', togglePopup);
    closePopup.addEventListener('click', togglePopup);

    // Безопасная вставка текста
    function escapeHTML(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    // Рендер сообщений
    function addUserMessage(text) {
      const wrap = document.createElement('div');
      wrap.className = 'flex justify-end';
      wrap.innerHTML = `
        <div class="rounded-lg py-2 px-4 max-w-[70%] bg-white text-black shadow">${escapeHTML(text)}</div>
      `;
      chatMessages.appendChild(wrap);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    function addBotMessage(text) {
      const wrap = document.createElement('div');
      wrap.className = 'flex flex-col items-start';
      wrap.innerHTML = `
        <div class="flex items-center mb-1">
          <img src="${AVATAR_URL}" alt="Avatar" class="w-6 h-6 rounded-full mr-2" />
          <span class="text-xs text-gray-600 font-medium">${AGENT_NAME}</span>
        </div>
        <div class="rounded-lg py-2 px-4 max-w-[70%] bg-white text-black shadow">${escapeHTML(text)}</div>
      `;
      chatMessages.appendChild(wrap);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    function addSysMessage(text) {
      const el = document.createElement('div');
      el.className = 'text-center text-gray-500 text-xs';
      el.textContent = text;
      chatMessages.appendChild(el);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ------- Индикация «печатает…» (приклеена к низу) -------
    let typingTimer = null;
    function showTyping() {
      typingWrap.classList.remove('hidden');
    }
    function hideTyping() {
      if (typingTimer) { clearTimeout(typingTimer); typingTimer = null; }
      typingWrap.classList.add('hidden');
    }

    // Отправка на бэкенд
    async function sendMessage(text) {
      chatSubmit.disabled = true;

      // Показать «печатает…» через 2 секунды, если ответа ещё нет
      typingTimer = setTimeout(showTyping, 2000);

      const ctrl = new AbortController();
      const timeout = setTimeout(() => ctrl.abort(), 30000); // 30s
      try {
        const resp = await fetch(REPLY_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sid: SID, message: text }),
          signal: ctrl.signal,
        });
        if (!resp.ok) {
          const errText = await resp.text().catch(() => '');
          throw new Error(`HTTP ${resp.status} ${errText}`);
        }
        const data = await resp.json();
        addBotMessage(data.reply ?? '(пусто)');
      } catch (e) {
        addSysMessage(e.name === 'AbortError' ? 'Таймаут запроса' : `Ошибка: ${e.message || e}`);
      } finally {
        hideTyping();
        clearTimeout(timeout);
        chatSubmit.disabled = false;
      }
    }

    // Обработчики ввода
    function handleSubmit() {
      const text = (chatInput.value || '').trim();
      if (!text) return;
      addUserMessage(text);
      chatInput.value = '';
      sendMessage(text);
    }
    chatSubmit.addEventListener('click', handleSubmit);
    chatInput.addEventListener('keyup', (ev) => {
      if (ev.key === 'Enter') handleSubmit();
    });
  }

  if (document.body) init();
  else window.addEventListener('DOMContentLoaded', init);
})();
