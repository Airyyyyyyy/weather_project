function showToast(message, duration = 1500) {
    return new Promise(resolve => {
        var toast = document.getElementById("toast");
        var msg = document.getElementById("toast-msg");
        msg.textContent = message;
        toast.classList.add("show");

        setTimeout(function() {
            toast.classList.remove("show");
            setTimeout(resolve, 500);
        }, duration);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const loader = document.getElementById('page-loader');
    const loaderText = document.getElementById('loader-text');

    function showLoader(text) {
        if (!loader) return;
        loaderText.textContent = text;
        loader.hidden = false;
    }

    const addForm = document.getElementById('add-city-form');
    if (addForm) {
        addForm.addEventListener('submit', function() {
            const input = document.getElementById('city-input');
            if (!input.value.trim()) return;
            showLoader('Fetching weather data...');
            document.getElementById('search-btn').disabled = true;
        });
    }

    document.querySelectorAll('form[action*="delete"]').forEach(function(f) {
        f.addEventListener('submit', function() { showLoader('Removing city...'); });
    });

    // Restore the page if the user comes back via the browser's back button.
    window.addEventListener('pageshow', function(e) {
        if (e.persisted && loader) loader.hidden = true;
    });

    const chatToggle = document.getElementById('chatToggle');
    const chatContainer = document.getElementById('chatContainer');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');

    chatToggle.addEventListener('click', function() {
        chatContainer.classList.toggle('active');
    });

    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        chatInput.value = '';

        const typingIndicator = addMessage('Thinking...', 'bot');

        fetch('/weather-chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            chatMessages.removeChild(typingIndicator);

            if (data.response) {
                addMessage(data.response, 'bot');
            } else if (data.error) {
                addMessage(data.error, 'bot');
            }
        })
        .catch(error => {
            chatMessages.removeChild(typingIndicator);
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        });
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    (function() {
        const messagesScript = document.getElementById('django-messages');
        if (!messagesScript) return;
        try {
            const messages = JSON.parse(messagesScript.textContent);
            (async function() {
                for (const message of messages) {
                    await showToast(message);
                }
            })();
        } catch (e) {
            console.error('Failed to parse Django messages JSON', e);
        }
    })();
});
