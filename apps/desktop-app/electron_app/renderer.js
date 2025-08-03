document.addEventListener("DOMContentLoaded", () => {
    const userInputField = document.getElementById("userInput");
    const nav = document.getElementById("nav");
    const inputContainer = document.getElementById("inputContainer");
    const gameContainer = document.getElementById("gameContainer");
    const hspServiceList = document.getElementById("hspServiceList").parentElement;
    const hspTaskForm = document.getElementById("hspTaskCapId").parentElement.parentElement;

    const CHANNELS = window.ipcChannels;

    // --- Create UI ---
    const chatViewButton = Button({ id: 'chatViewButton', text: 'Chat', onClick: () => window.store.updateState(window.store.actions.setActiveView, "chat") });
    const hspViewButton = Button({ id: 'hspViewButton', text: 'HSP', onClick: () => {
        window.store.updateState(window.store.actions.setActiveView, "hsp");
        loadHspServices();
    }});
    const gameViewButton = Button({ id: 'gameViewButton', text: 'Game', onClick: () => window.store.updateState(window.store.actions.setActiveView, "game") });
    nav.appendChild(chatViewButton);
    nav.appendChild(hspViewButton);
    nav.appendChild(gameViewButton);

    const sendButton = Button({ id: 'sendButton', text: 'Send', onClick: sendMessage });
    inputContainer.appendChild(sendButton);

    const startGameButton = Button({ id: 'startGameButton', text: 'Start Game', onClick: () => {
        if (window.electronAPI && window.electronAPI.invoke) {
            window.electronAPI.invoke(CHANNELS.GAME_START);
        }
    }});
    gameContainer.prepend(startGameButton);

    const refreshHspServicesButton = Button({ id: 'refreshHspServicesButton', text: 'Refresh', onClick: loadHspServices });
    hspServiceList.querySelector(".hsp-header").appendChild(refreshHspServicesButton);

    const sendHspTaskButton = Button({ id: 'sendHspTaskButton', text: 'Send Task', onClick: sendHspTaskIPC });
    hspTaskForm.appendChild(sendHspTaskButton);


    // --- Event Listeners ---

    userInputField.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    // --- Logic ---

    async function startNewSession() {
        try {
            window.store.updateState(window.store.actions.addChatMessage, {
                text: "Starting new session...",
                sender: "system",
            });
            const response = await window.electronAPI.invoke(CHANNELS.API_START_SESSION, {});
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            window.store.updateState(window.store.actions.setSessionId, data.session_id);
            window.store.updateState(window.store.actions.addChatMessage, {
                text: data.greeting,
                sender: "ai",
            });
            console.log("Session started:", data.session_id);
        } catch (error) {
            console.error("Error starting session:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error starting session: ${error.message}`);
        }
    }

    async function sendMessage() {
        const text = userInputField.value.trim();
        if (!text) return;

        const sessionId = window.store.getState().chat.sessionId;
        if (!sessionId) {
            window.store.updateState(window.store.actions.setErrorMessage, "Session not started. Please wait or try restarting.");
            return;
        }

        window.store.updateState(window.store.actions.addChatMessage, { text, sender: "user" });
        userInputField.value = ""; // Clear input field

        try {
            const response = await window.electronAPI.invoke(CHANNELS.API_SEND_MESSAGE, {
                text: text,
                session_id: sessionId,
            });
            if (!response.ok) {
                const errorData = await response.text(); // Try to get more error info
                throw new Error(
                    `HTTP error! status: ${response.status}, details: ${errorData}`,
                );
            }
            const data = await response.json();
            window.store.updateState(window.store.actions.addChatMessage, {
                text: data.response_text,
                sender: "ai",
            });
        } catch (error) {
            console.error("Error sending message:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error sending message: ${error.message}`);
        }
    }

    async function loadHspServices() {
        window.store.updateState(window.store.actions.setHspServices, []);
        window.store.updateState(window.store.actions.setLoading, true);
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const services = await window.electronAPI.invoke(
                    CHANNELS.HSP_GET_DISCOVERED_SERVICES,
                );
                window.store.updateState(window.store.actions.setHspServices, services);
            } else {
                throw new Error(
                    "electronAPI or invoke method not available on window. Make sure preload.js is correctly exposing it.",
                );
            }
        } catch (error) {
            console.error("Error loading HSP services:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error loading HSP services: ${error.message}`);
        } finally {
            window.store.updateState(window.store.actions.setLoading, false);
        }
    }

    async function sendHspTaskIPC() {
        const hspTaskCapIdInput = document.getElementById("hspTaskCapId");
        const hspTaskParamsTextarea = document.getElementById("hspTaskParams");
        const targetCapabilityId = hspTaskCapIdInput.value.trim();
        const paramsJsonStr = hspTaskParamsTextarea.value.trim();

        if (!targetCapabilityId) {
            window.store.updateState(window.store.actions.setErrorMessage, "Target Capability ID is required.");
            return;
        }

        let parameters;
        try {
            parameters = paramsJsonStr ? JSON.parse(paramsJsonStr) : {};
        } catch (e) {
            window.store.updateState(window.store.actions.setErrorMessage, `Invalid JSON parameters: ${e.message}`);
            return;
        }

        window.store.updateState(window.store.actions.setLoading, true);
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const response = await window.electronAPI.invoke(CHANNELS.HSP_REQUEST_TASK, {
                    targetCapabilityId,
                    parameters,
                });
                if (response.correlation_id && !response.error) {
                    const correlationId = response.correlation_id;
                    window.store.updateState(window.store.actions.setHspTaskStatus, {
                        correlationId,
                        statusData: {
                            correlation_id: correlationId,
                            status: "pending_initiation",
                            message: "Request sent, awaiting first status update...",
                        },
                    });
                    const intervalId = setInterval(() => {
                        pollTaskStatus(correlationId);
                    }, 3000);
                    window.store.updateState(window.store.actions.addHspActivePoll, { correlationId, intervalId });
                } else {
                    window.store.updateState(window.store.actions.setErrorMessage, response.error || "An unknown error occurred.");
                }
            } else {
                throw new Error(
                    "electronAPI or invoke method not available for 'hsp:request-task'.",
                );
            }
        } catch (error) {
            console.error("Error sending HSP task request via IPC:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `IPC Error: ${error.message}`);
        } finally {
            window.store.updateState(window.store.actions.setLoading, false);
        }
    }

    async function pollTaskStatus(correlationId) {
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const statusData = await window.electronAPI.invoke(
                    CHANNELS.HSP_GET_TASK_STATUS,
                    correlationId,
                );
                window.store.updateState(window.store.actions.setHspTaskStatus, { correlationId, statusData });

                if (
                    ["completed", "failed", "unknown_or_expired"].includes(statusData.status)
                ) {
                    const intervalId = window.store.getState().hsp.activePolls[correlationId];
                    if (intervalId) {
                        clearInterval(intervalId);
                        window.store.updateState(window.store.actions.removeHspActivePoll, correlationId);
                    }
                }
            } else {
                throw new Error(
                    "electronAPI or invoke method not available for 'hsp:get-task-status'.",
                );
            }
        } catch (error) {
            console.error(`Error polling status for task ${correlationId}:`, error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error polling status for task ${correlationId}: ${error.message}`);
            const intervalId = window.store.getState().hsp.activePolls[correlationId];
            if (intervalId) {
                clearInterval(intervalId);
                window.store.updateState(window.store.actions.removeHspActivePoll, correlationId);
            }
        }
    }

    // --- Initial Load ---
    startNewSession();
    window.store.updateState(window.store.actions.setActiveView, "chat");
});
