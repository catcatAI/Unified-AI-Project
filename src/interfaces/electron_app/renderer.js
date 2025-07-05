document.addEventListener('DOMContentLoaded', () => {
    const userInputField = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatDisplay = document.getElementById('chatDisplay');

    let currentSessionId = null;
    const apiBaseUrl = 'http://localhost:8000/api/v1'; // Assuming the API server runs on port 8000

    function appendMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');

        const strong = document.createElement('strong');
        strong.textContent = sender === 'user' ? 'You: ' : 'AI: ';

        messageDiv.appendChild(strong);
        messageDiv.appendChild(document.createTextNode(text));

        chatDisplay.appendChild(messageDiv);
        chatDisplay.scrollTop = chatDisplay.scrollHeight; // Auto-scroll to bottom
    }

    async function startNewSession() {
        try {
            appendMessage('Starting new session...', 'system'); // System message
            const response = await fetch(`${apiBaseUrl}/session/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}) // Send empty JSON object for now, can add user_id if needed
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            currentSessionId = data.session_id;
            appendMessage(data.greeting, 'ai');
            console.log('Session started:', currentSessionId);
        } catch (error) {
            console.error('Error starting session:', error);
            appendMessage(`Error starting session: ${error.message}`, 'system-error');
        }
    }

    async function sendMessage() {
        const text = userInputField.value.trim();
        if (!text) return;

        if (!currentSessionId) {
            appendMessage('Session not started. Please wait or try restarting.', 'system-error');
            // Optionally, try to start a new session again here
            // await startNewSession();
            // if (!currentSessionId) return; // if still no session, abort
            return;
        }

        appendMessage(text, 'user');
        userInputField.value = ''; // Clear input field

        try {
            const response = await fetch(`${apiBaseUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    session_id: currentSessionId
                    // user_id could be added here if available
                })
            });
            if (!response.ok) {
                const errorData = await response.text(); // Try to get more error info
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorData}`);
            }
            const data = await response.json();
            appendMessage(data.response_text, 'ai');
        } catch (error) {
            console.error('Error sending message:', error);
            appendMessage(`Error sending message: ${error.message}`, 'system-error');
        }
    }

    sendButton.addEventListener('click', sendMessage);
    userInputField.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Start a session when the renderer is ready
    startNewSession();
});
