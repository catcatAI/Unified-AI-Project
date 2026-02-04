// ses is enabled via preload or not needed
// DOMPurify is now loaded via CDN in index.html

document.addEventListener("DOMContentLoaded", () => {
    const userInputField = document.getElementById("userInput");
    const nav = document.getElementById("nav");
    const inputContainer = document.getElementById("inputContainer");
    const gameContainer = document.getElementById("gameContainer");
    const hspServiceList = document.getElementById("hspServiceList").parentElement;
    const hspTaskForm = document.getElementById("hspTaskCapId").parentElement.parentElement;
    const themeSelect = document.getElementById("themeSelect");
    const defaultModelInput = document.getElementById("defaultModelInput");

    const CHANNELS = window.ipcChannels;
    
    // 使用通过CDN加载的DOMPurify
    const DOMPurify = window.DOMPurify;

    // --- Create UI ---
    const chatViewButton = Button({ id: 'chatViewButton', text: 'Chat', onClick: () => window.store.updateState(window.store.actions.setActiveView, "chat") });
    const hspViewButton = Button({ id: 'hspViewButton', text: 'HSP', onClick: () => {
        window.store.updateState(window.store.actions.setActiveView, "hsp");
        loadHspServices();
    }});
    const gameViewButton = Button({ id: 'gameViewButton', text: 'Game', onClick: () => window.store.updateState(window.store.actions.setActiveView, "game") });
    const settingsViewButton = Button({ id: 'settingsViewButton', text: 'Settings', onClick: () => window.store.updateState(window.store.actions.setActiveView, "settings") });
    // 添加Atlassian集成视图按钮
    const atlassianViewButton = Button({ id: 'atlassianViewButton', text: 'Atlassian', onClick: () => {
        window.store.updateState(window.store.actions.setActiveView, "atlassian");
        // 重新加载Atlassian数据
        loadAtlassianStatus();
        loadJiraProjects();
        loadConfluenceSpaces();
        loadRovoAgents();
        loadRovoTasks();
    }});
    
    nav.appendChild(chatViewButton);
    nav.appendChild(hspViewButton);
    nav.appendChild(gameViewButton);
    nav.appendChild(atlassianViewButton);
    nav.appendChild(settingsViewButton);

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

    themeSelect.addEventListener("change", (event) => {
        window.store.updateState(window.store.actions.setTheme, event.target.value);
    });

    defaultModelInput.addEventListener("change", (event) => {
        window.store.updateState(window.store.actions.setDefaultModel, event.target.value);
    });

    // --- Logic ---

    async function sendMessage() {
        // 确保DOMPurify可用
        const sanitizedText = DOMPurify ? DOMPurify.sanitize(userInputField.value.trim()) : userInputField.value.trim();
        const text = sanitizedText;
        if (!text) return;

        // Add user message to display
        addMessageToChat("user", text);
        userInputField.value = "";

        // Send to Angela API
        try {
            const response = await window.electronAPI.invoke(CHANNELS.API_SEND_MESSAGE, {
                text: text,
                message: text,
                user_name: "用户"
            });
            
            if (response && response.response_text) {
                addMessageToChat("angela", response.response_text);
            } else {
                addMessageToChat("angela", "抱歉，我现在有点忙，请稍后再试~");
            }
        } catch (error) {
            console.error("Error sending message:", error);
            addMessageToChat("angela", "连接遇到了一点问题，请确保后端正在运行！");
        }
    }

    function addMessageToChat(sender, text) {
        const chatDisplay = document.getElementById("chatDisplay");
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement("div");
        avatar.className = "avatar";
        if (sender === "user") {
            avatar.textContent = "👤";
        } else if (sender === "angela") {
            avatar.textContent = "🌟";
        }
        
        const content = document.createElement("div");
        content.className = "message-content";
        content.textContent = text;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        chatDisplay.appendChild(messageDiv);
        
        // Scroll to bottom
        chatDisplay.scrollTop = chatDisplay.scrollHeight;
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

    // --- Atlassian Integration Functions ---

    async function loadAtlassianStatus() {
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const status = await window.electronAPI.invoke("api:atlassian-status");
                window.store.updateState(window.store.actions.setAtlassianStatus, status);
            }
        } catch (error) {
            console.error("Error loading Atlassian status:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error loading Atlassian status: ${error.message}`);
        }
    }

    async function loadJiraProjects() {
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const projects = await window.electronAPI.invoke("api:jira-projects");
                window.store.updateState(window.store.actions.setJiraProjects, projects.projects || []);
            }
        } catch (error) {
            console.error("Error loading Jira projects:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error loading Jira projects: ${error.message}`);
        }
    }

    async function loadConfluenceSpaces() {
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const spaces = await window.electronAPI.invoke("api:confluence-spaces");
                window.store.updateState(window.store.actions.setConfluenceSpaces, spaces.spaces || []);
            }
        } catch (error) {
            console.error("Error loading Confluence spaces:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error loading Confluence spaces: ${error.message}`);
        }
    }

    async function loadRovoAgents() {
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const agents = await window.electronAPI.invoke("api:rovo-agents");
                window.store.updateState(window.store.actions.setRovoAgents, agents.agents || []);
            }
        } catch (error) {
            console.error("Error loading Rovo agents:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error loading Rovo agents: ${error.message}`);
        }
    }

    async function loadRovoTasks() {
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const tasks = await window.electronAPI.invoke("api:rovo-tasks");
                window.store.updateState(window.store.actions.setRovoTasks, tasks.tasks || []);
            }
        } catch (error) {
            console.error("Error loading Rovo tasks:", error);
            window.store.updateState(window.store.actions.setErrorMessage, `Error loading Rovo tasks: ${error.message}`);
        }
    }

    // --- Initial Load ---
    window.store.updateState(window.store.actions.setActiveView, "chat");
    
    // Load Atlassian integration data
    loadAtlassianStatus();
    loadJiraProjects();
    loadConfluenceSpaces();
    loadRovoAgents();
    loadRovoTasks();
});