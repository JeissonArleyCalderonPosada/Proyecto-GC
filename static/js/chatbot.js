document.addEventListener("DOMContentLoaded", () => {
  const openBotLink = document.getElementById("ziloyBotLink");
  const chatbotPopup = document.getElementById("chatbotPopup");
  const closeChatbot = document.getElementById("closeChatbot");
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const sendMessage = document.getElementById("sendMessage");

  let chatMode = null; // "faq" o "predictivo"

  // Abrir ventana del chatbot
  openBotLink.addEventListener("click", (e) => {
    e.preventDefault();
    chatbotPopup.style.display = "flex";
    chatMessages.innerHTML = ""; // Limpia el chat anterior
    showWelcomeMessage();
  });

  // Cerrar ventana
  closeChatbot.addEventListener("click", () => {
    chatbotPopup.style.display = "none";
  });

  // Enviar mensaje con Enter
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      send();
    }
  });

  sendMessage.addEventListener("click", send);

  // =============================
  // FUNCIONES
  // =============================

  function showWelcomeMessage() {
    appendMessage("bot", "¡Hola! Soy ZiloyBot ¿Cómo puedo ayudarte hoy?");
    const optionsDiv = document.createElement("div");
    optionsDiv.className = "bot-options";
    optionsDiv.innerHTML = `
      <button class="option-btn" id="faqBtn">Preguntas frecuentes</button>
      <button class="option-btn" id="prediccionBtn">Necesito ayuda con mi producto</button>
    `;
    chatMessages.appendChild(optionsDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    document.getElementById("faqBtn").addEventListener("click", () => {
      chatMode = "faq";
      appendMessage("bot", "¡Perfecto! Puedo responder tus preguntas sobre Ziloy y nuestros productos.");
      optionsDiv.remove();
    });

    document.getElementById("prediccionBtn").addEventListener("click", () => {
      chatMode = "predictivo";
      appendMessage("bot", "Excelente! Envíame los datos de tu bebida para predecir cuánto tardará en enfriarse. Para comenzar escribe OK");
      optionsDiv.remove();
    });
  }

  function appendMessage(sender, text) {
    const wrap = document.createElement("div");
    wrap.className = sender === "user" ? "msg user-msg" : "msg bot-msg";
    wrap.innerHTML = `<strong>${sender === "user" ? "Tú" : "ZiloyBot"}:</strong> <span>${escapeHtml(text)}</span>`;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function send() {
    const message = chatInput.value.trim();
    if (!message || !chatMode) return;

    appendMessage("user", message);
    chatInput.value = "";
    appendMessage("bot", "...");

    const endpoint = chatMode === "faq" ? "/chat" : "/prediccion";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      const last = chatMessages.querySelectorAll(".msg.bot-msg");
      if (last.length) last[last.length - 1].remove();

      if (data.reply) appendMessage("bot", data.reply);
      else appendMessage("bot", "Lo siento, no obtuve respuesta.");
    } catch (err) {
      console.error(err);
      appendMessage("bot", "Error de conexión con el servidor del chatbot.");
    }
  }

  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
