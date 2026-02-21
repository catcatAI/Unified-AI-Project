/**
 * Angela AI Desktop App - Dialogue UI
 * Simple chat interface for interacting with Angela
 */

class DialogueUI {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.messages = [];
        this.init();
    }

    init() {
        // Create dialogue container
        const container = document.createElement('div');
        container.id = 'dialogue-container';
        container.innerHTML = `
            <div id="dialogue-panel">
                <div id="dialogue-header">
                    <span class="title">💬 Chat with Angela</span>
                    <button id="btn-toggle-dialogue" class="toggle-btn">−</button>
                </div>
                <div id="dialogue-messages"></div>
                <div id="dialogue-input-area">
                    <input type="text" id="dialogue-input" placeholder="Type a message..." />
                    <button id="btn-send">Send</button>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #dialogue-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 400px;
                max-width: 90vw;
                z-index: var(--z-index-dialogue, 1000);
            }

            #dialogue-panel {
                background: rgba(30, 30, 30, 0.95);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                overflow: hidden;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            #dialogue-header {
                padding: 12px 16px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: 600;
            }

            .toggle-btn {
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            #dialogue-messages {
                height: 300px;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            #dialogue-messages::-webkit-scrollbar {
                width: 6px;
            }

            #dialogue-messages::-webkit-scrollbar-thumb {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
            }

            .message {
                padding: 10px 14px;
                border-radius: 12px;
                max-width: 80%;
                word-wrap: break-word;
                animation: fadeIn 0.3s ease-in;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .message.user {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                align-self: flex-end;
                margin-left: auto;
            }

            .message.angela {
                background: rgba(255, 255, 255, 0.1);
                color: #e0e0e0;
                align-self: flex-start;
            }

            .message.system {
                background: rgba(255, 193, 7, 0.2);
                color: #ffc107;
                align-self: center;
                font-size: 12px;
                text-align: center;
            }

            .message-time {
                font-size: 10px;
                opacity: 0.7;
                margin-top: 4px;
            }

            #dialogue-input-area {
                padding: 12px;
                background: rgba(0, 0, 0, 0.3);
                display: flex;
                gap: 8px;
            }

            #dialogue-input {
                flex: 1;
                padding: 10px 14px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
                outline: none;
            }

            #dialogue-input:focus {
                border-color: #667eea;
                background: rgba(255, 255, 255, 0.15);
            }

            #btn-send {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }

            #btn-send:hover {
                transform: scale(1.05);
            }

            #btn-send:active {
                transform: scale(0.95);
            }

            #btn-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            #dialogue-panel.collapsed #dialogue-messages,
            #dialogue-panel.collapsed #dialogue-input-area {
                display: none;
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(container);

        // Bind events
        this.bindEvents();

        // Add welcome message
        this.addSystemMessage('Connected to Angela AI. Say hello!');
    }

    bindEvents() {
        const input = document.getElementById('dialogue-input');
        const sendBtn = document.getElementById('btn-send');
        const toggleBtn = document.getElementById('btn-toggle-dialogue');

        // Send message on button click
        sendBtn.addEventListener('click', () => this.sendMessage());

        // Send message on Enter key
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Toggle panel
        toggleBtn.addEventListener('click', () => {
            const panel = document.getElementById('dialogue-panel');
            panel.classList.toggle('collapsed');
            toggleBtn.textContent = panel.classList.contains('collapsed') ? '+' : '−';
        });
    }

    async sendMessage() {
        const input = document.getElementById('dialogue-input');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to UI
        this.addMessage('user', message);
        input.value = '';

        // Disable input while waiting
        const sendBtn = document.getElementById('btn-send');
        sendBtn.disabled = true;
        input.disabled = true;

        // Send to backend
        const response = await this.apiClient.sendMessage(message);

        // Re-enable input
        sendBtn.disabled = false;
        input.disabled = false;
        input.focus();

        // Add Angela's response
        if (response.success) {
            this.addMessage('angela', response.response);
        } else {
            this.addSystemMessage(`Error: ${response.response}`);
        }
    }

    addMessage(sender, text) {
        const messagesContainer = document.getElementById('dialogue-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const time = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            <div class="message-text">${this.escapeHtml(text)}</div>
            <div class="message-time">${time}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        this.messages.push({ sender, text, time });
    }

    addSystemMessage(text) {
        const messagesContainer = document.getElementById('dialogue-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.textContent = text;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DialogueUI;
}
