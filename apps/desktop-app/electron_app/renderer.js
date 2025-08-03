document.addEventListener("DOMContentLoaded", () => {
    const userInputField = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatViewButton = document.getElementById("chatViewButton");
    const hspViewButton = document.getElementById("hspViewButton");
    const gameViewButton = document.getElementById("gameViewButton");
    const startGameButton = document.getElementById("startGameButton");
    const refreshHspServicesButton = document.getElementById(
        "refreshHspServicesButton",
    );
    const sendHspTaskButton = document.getElementById("sendHspTaskButton");

    // --- Event Listeners ---

    chatViewButton.addEventListener("click", () => {
        window.store.updateState(window.store.actions.setActiveView, "chat");
    });

    hspViewButton.addEventListener("click", () => {
        window.store.updateState(window.store.actions.setActiveView, "hsp");
        loadHspServices();
    });

    gameViewButton.addEventListener("click", () => {
        window.store.updateState(window.store.actions.setActiveView, "game");
    });

    startGameButton.addEventListener("click", () => {
        if (window.electronAPI && window.electronAPI.invoke) {
            window.electronAPI.invoke("game:start");
        }
    });

    sendButton.addEventListener("click", sendMessage);
    userInputField.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    refreshHspServicesButton.addEventListener("click", loadHspServices);
    sendHspTaskButton.addEventListener("click", sendHspTaskIPC);

    // --- Logic ---

    async function startNewSession() {
        try {
            window.store.updateState(window.store.actions.addChatMessage, {
                text: "Starting new session...",
                sender: "system",
            });
            const response = await window.electronAPI.invoke("api:start-session", {});
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
            window.store.updateState(window.store.actions.addChatMessage, {
                text: `Error starting session: ${error.message}`,
                sender: "system-error",
            });
        }
    }

    async function sendMessage() {
        const text = userInputField.value.trim();
        if (!text) return;

        const sessionId = window.store.getState().chat.sessionId;
        if (!sessionId) {
            window.store.updateState(window.store.actions.addChatMessage, {
                text: "Session not started. Please wait or try restarting.",
                sender: "system-error",
            });
            return;
        }

        window.store.updateState(window.store.actions.addChatMessage, { text, sender: "user" });
        userInputField.value = ""; // Clear input field

        try {
            const response = await window.electronAPI.invoke("api:send-message", {
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
            window.store.updateState(window.store.actions.addChatMessage, {
                text: `Error sending message: ${error.message}`,
                sender: "system-error",
            });
        }
    }

    async function loadHspServices() {
        window.store.updateState(window.store.actions.setHspServices, []);
        window.store.updateState(window.store.actions.setLoading, true);
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const services = await window.electronAPI.invoke(
                    "hsp:get-discovered-services",
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
                const response = await window.electronAPI.invoke("hsp:request-task", {
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
                    "hsp:get-task-status",
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
            window.store.updateState(window.store.actions.setHspTaskStatus, {
                correlationId,
                statusData: {
                    correlation_id: correlationId,
                    status: "unknown_or_expired",
                    message: `Error polling status: ${error.message}`,
                },
            });
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
