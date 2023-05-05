document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatHistory = document.getElementById("chat-history");

    chatForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const prompt = chatInput.value.trim();
        if (!prompt) {
            return;
        }

        chatInput.value = "";
        chatHistory.innerHTML += `<p><strong>User:</strong> ${prompt}</p>`;

        fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ prompt: prompt })
        })
        .then(response => response.json())
        .then(data => {
            chatHistory.innerHTML += `<p><strong>DaevasAGI:</strong> ${data.response}</p>`;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        });
    });
});
