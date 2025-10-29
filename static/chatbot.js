document.addEventListener("DOMContentLoaded", () => {
  const openBotLink = document.getElementById('ziloyBotLink');
  const chatbotPopup = document.getElementById('chatbotPopup');
  const closeChatbot = document.getElementById('closeChatbot');
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const sendMessage = document.getElementById('sendMessage');

  if (openBotLink) openBotLink.addEventListener('click', (e) => { e.preventDefault(); chatbotPopup.style.display = 'flex'; chatInput.focus(); });
  if (closeChatbot) closeChatbot.addEventListener('click', () => { chatbotPopup.style.display = 'none'; });

  chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); send(); } });
  sendMessage.addEventListener('click', send);

  function appendMessage(sender, text){
    const wrap = document.createElement('div');
    wrap.className = sender === 'user' ? 'msg user-msg' : 'msg bot-msg';
    wrap.innerHTML = `<strong>${sender === 'user' ? 'Tú' : 'ZiloyBot'}:</strong> <span>${escapeHtml(text)}</span>`;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function send(){
    const message = chatInput.value.trim();
    if (!message) return;
    appendMessage('user', message);
    chatInput.value = '';
    appendMessage('bot', '...');
    try {
      const res = await fetch("http://127.0.0.1:5001/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ message })
      });
      const data = await res.json();
      // quitar "..." mensaje temporal
      const last = chatMessages.querySelectorAll('.msg.bot-msg');
      if (last.length) last[last.length - 1].remove();
      if (data.reply) appendMessage('bot', data.reply);
      else appendMessage('bot', 'Lo siento, no obtuve respuesta.');
    } catch (err) {
      console.error(err);
      appendMessage('bot', 'Error de conexión con el servidor del chatbot.');
    }
  }

  function escapeHtml(unsafe) {
      return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                   .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
});
