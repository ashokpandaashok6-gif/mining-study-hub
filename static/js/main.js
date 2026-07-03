// AI Assistant chat logic
function initAIAssistant() {
  const form = document.getElementById("ai-form");
  if (!form) return;

  const input = document.getElementById("ai-input");
  const chatWindow = document.getElementById("chat-window");
  const sendBtn = document.getElementById("ai-send");

  function addMessage(role, text) {
    const wrap = document.createElement("div");
    wrap.className = `chat-msg ${role}`;
    const who = document.createElement("div");
    who.className = "who";
    who.textContent = role === "user" ? "You" : "AI Assistant";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    wrap.appendChild(who);
    wrap.appendChild(bubble);
    chatWindow.appendChild(wrap);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return bubble;
  }

  async function sendPrompt(promptText) {
    if (!promptText.trim()) return;
    addMessage("user", promptText);
    input.value = "";
    sendBtn.disabled = true;
    const bubble = addMessage("assistant", "Thinking...");

    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      const res = await fetch("/ai/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ prompt: promptText }),
      });
      const data = await res.json();
      if (!res.ok) {
        bubble.textContent = data.error || "Something went wrong.";
      } else {
        bubble.textContent = data.answer;
      }
    } catch (err) {
      bubble.textContent = "Network error — please try again.";
    } finally {
      sendBtn.disabled = false;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendPrompt(input.value);
  });

  document.querySelectorAll(".quick-prompts button").forEach((btn) => {
    btn.addEventListener("click", () => sendPrompt(btn.dataset.prompt));
  });
}

document.addEventListener("DOMContentLoaded", initAIAssistant);
