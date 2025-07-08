document.addEventListener('DOMContentLoaded', () => {
    const userInputField = document.getElementById('userInput');
    const userInputField = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatDisplay = document.getElementById('chatDisplay');

    // View switching
    const chatViewButton = document.getElementById('chatViewButton');
    const hspViewButton = document.getElementById('hspViewButton');
    const chatView = document.getElementById('chatView');
    const hspServicesView = document.getElementById('hspServicesView');

    // HSP Services elements
    const refreshHspServicesButton = document.getElementById('refreshHspServicesButton');
    const hspServiceListDiv = document.getElementById('hspServiceList');
    const hspTaskCapIdInput = document.getElementById('hspTaskCapId');
    const hspTaskParamsTextarea = document.getElementById('hspTaskParams');
    const sendHspTaskButton = document.getElementById('sendHspTaskButton');
    const hspTaskResponseDisplay = document.getElementById('hspTaskResponseDisplay');

    let currentSessionId = null;
    const apiBaseUrl = 'http://localhost:8000/api/v1';

    function showView(viewId) {
        chatView.style.display = 'none';
        hspServicesView.style.display = 'none';
        document.getElementById(viewId).style.display = 'flex'; // Assuming views are flex containers
        if (viewId === 'hspServicesView') { // Auto-refresh if switching to HSP view and list is empty
            if (hspServiceListDiv.children.length <= 1 && hspServiceListDiv.children[0]?.tagName === 'P') {
                 loadHspServices();
            }
        }
    }

    chatViewButton.addEventListener('click', () => showView('chatView'));
    hspViewButton.addEventListener('click', () => showView('hspServicesView'));


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

    // --- HSP Services Logic ---
    async function loadHspServices() {
        hspServiceListDiv.innerHTML = '<p>Loading HSP services...</p>';
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const services = await window.electronAPI.invoke('hsp:get-discovered-services');
                hspServiceListDiv.innerHTML = ''; // Clear loading message
                if (services && services.length > 0) {
                    const ul = document.createElement('ul');
                    services.forEach(service => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <strong>${service.name} (v${service.version})</strong> [ID: ${service.capability_id}]<br>
                            Provider AI: ${service.ai_id}<br>
                            Description: ${service.description || 'N/A'}<br>
                            Status: ${service.availability_status} <br>
                            Tags: ${(service.tags || []).join(', ')}
                        `;

                        const useServiceButton = document.createElement('button');
                        useServiceButton.textContent = 'Use Service';
                        useServiceButton.setAttribute('data-capability-id', service.capability_id);
                        useServiceButton.style.marginLeft = '10px'; // Basic styling

                        useServiceButton.addEventListener('click', (event) => {
                            const capId = event.target.getAttribute('data-capability-id');
                            const hspTaskCapIdInputElement = document.getElementById('hspTaskCapId');
                            const hspTaskParamsTextareaElement = document.getElementById('hspTaskParams');

                            if (hspTaskCapIdInputElement && capId) {
                                hspTaskCapIdInputElement.value = capId;
                                if (hspTaskParamsTextareaElement) {
                                    hspTaskParamsTextareaElement.value = ''; // Clear previous params
                                }
                                console.log(`Capability ID '${capId}' populated into task form.`);
                                // Optionally, focus the parameters textarea or scroll to the form
                                // hspTaskParamsTextareaElement?.focus();
                                hspTaskCapIdInputElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

                            } else {
                                if (!hspTaskCapIdInputElement) {
                                    console.error('HSP Task Capability ID input field (#hspTaskCapId) not found.');
                                }
                                if (!capId) {
                                    console.error('Capability ID not found on the clicked button.');
                                }
                            }
                        });

                        li.appendChild(document.createElement('br')); // Add a line break before the button
                        li.appendChild(useServiceButton);
                        ul.appendChild(li);
                    });
                    hspServiceListDiv.appendChild(ul);
                } else {
                    hspServiceListDiv.innerHTML = '<p>No HSP services discovered.</p>';
                }
            } else {
                throw new Error("electronAPI or invoke method not available on window. Make sure preload.js is correctly exposing it.");
            }
        } catch (error) {
            console.error('Error loading HSP services:', error);
            hspServiceListDiv.innerHTML = `<p>Error loading HSP services: ${error.message}</p>`;
        }
    }

    refreshHspServicesButton.addEventListener('click', loadHspServices);

    // Initial view setup
    showView('chatView'); // Default to chat view
    // Start a session when the renderer is ready for chat
    startNewSession();

    async function sendHspTaskIPC() {
        const targetCapabilityId = hspTaskCapIdInput.value.trim();
        const paramsJsonStr = hspTaskParamsTextarea.value.trim();

        if (!targetCapabilityId) {
            hspTaskResponseDisplay.innerHTML = '<p style="color: red;">Error: Target Capability ID is required.</p>';
            return;
        }

        let parameters;
        try {
            parameters = paramsJsonStr ? JSON.parse(paramsJsonStr) : {};
        } catch (e) {
            hspTaskResponseDisplay.innerHTML = `<p style="color: red;">Error: Parameters are not valid JSON: ${e.message}</p>`;
            return;
        }

        hspTaskResponseDisplay.innerHTML = '<p>Sending HSP task request...</p>';
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const response = await window.electronAPI.invoke('hsp:request-task', { targetCapabilityId, parameters });
                let responseHtml = `<strong>Status:</strong> ${response.status_message}<br>`;
                if (response.correlation_id) {
                    responseHtml += `<strong>Correlation ID:</strong> ${response.correlation_id}<br>`;
                }
                if (response.error) {
                    responseHtml += `<strong style="color: red;">Error:</strong> ${response.error}<br>`;
                }
                hspTaskResponseDisplay.innerHTML = responseHtml;
            } else {
                throw new Error("electronAPI or invoke method not available for 'hsp:request-task'.");
            }
        } catch (error) {
            console.error('Error sending HSP task request via IPC:', error);
            hspTaskResponseDisplay.innerHTML = `<p style="color: red;">IPC Error: ${error.message}</p>`;
        }
    }

    sendHspTaskButton.addEventListener('click', sendHspTaskIPC);

    // --- Polling for HSP Task Results ---
    const activePolls = {}; // Store active polling intervals: { correlationId: intervalId }

    function updateTaskStatusDisplay(correlationId, statusData) {
        // Find or create a display area for this correlationId's status
        let statusDiv = document.getElementById(`hsp-task-status-${correlationId}`);
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = `hsp-task-status-${correlationId}`;
            // Prepend to hspTaskResponseDisplay so new statuses appear at the top
            hspTaskResponseDisplay.insertBefore(statusDiv, hspTaskResponseDisplay.firstChild);
        }

        let statusHtml = `<strong>Task ${correlationId}:</strong> ${statusData.status}<br>`;
        if (statusData.message) {
            statusHtml += `<em>${statusData.message}</em><br>`;
        }
        if (statusData.status === "completed" && statusData.result_payload) {
            statusHtml += `Result: <pre>${JSON.stringify(statusData.result_payload, null, 2)}</pre>`;
        }
        if (statusData.status === "failed" && statusData.error_details) {
            statusHtml += `Error: <pre>${JSON.stringify(statusData.error_details, null, 2)}</pre>`;
        }
        statusDiv.innerHTML = statusHtml;

        if (["completed", "failed", "unknown_or_expired"].includes(statusData.status)) {
            if (activePolls[correlationId]) {
                clearInterval(activePolls[correlationId]);
                delete activePolls[correlationId];
                console.log(`Polling stopped for task ${correlationId}. Status: ${statusData.status}`);
            }
        }
    }

    async function pollTaskStatus(correlationId) {
        console.log(`Polling status for task ${correlationId}...`);
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const statusData = await window.electronAPI.invoke('hsp:get-task-status', correlationId);
                updateTaskStatusDisplay(correlationId, statusData);
            } else {
                throw new Error("electronAPI or invoke method not available for 'hsp:get-task-status'.");
            }
        } catch (error) {
            console.error(`Error polling status for task ${correlationId}:`, error);
            // Update UI to show polling error for this task
            updateTaskStatusDisplay(correlationId, {
                correlation_id: correlationId,
                status: "unknown_or_expired", // Treat polling error as unknown
                message: `Error polling status: ${error.message}`
            });
            // Stop polling on error
            if (activePolls[correlationId]) {
                clearInterval(activePolls[correlationId]);
                delete activePolls[correlationId];
            }
        }
    }

    // Modify sendHspTaskIPC to start polling
    async function sendHspTaskIPC() {
        const targetCapabilityId = hspTaskCapIdInput.value.trim();
        const paramsJsonStr = hspTaskParamsTextarea.value.trim();

        if (!targetCapabilityId) {
            hspTaskResponseDisplay.innerHTML = '<p style="color: red;">Error: Target Capability ID is required.</p>';
            return;
        }
        let parameters;
        try {
            parameters = paramsJsonStr ? JSON.parse(paramsJsonStr) : {};
        } catch (e) {
            hspTaskResponseDisplay.innerHTML = `<p style="color: red;">Error: Parameters are not valid JSON: ${e.message}</p>`;
            return;
        }

        hspTaskResponseDisplay.innerHTML = '<p>Sending HSP task request...</p>'; // Initial feedback
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const response = await window.electronAPI.invoke('hsp:request-task', { targetCapabilityId, parameters });
                // Display initial response from POST /tasks
                let initialResponseHtml = `<strong>Initial API Response:</strong> ${response.status_message}<br>`;
                if (response.correlation_id) {
                    initialResponseHtml += `<strong>Correlation ID:</strong> ${response.correlation_id}<br><i>Polling for final status...</i>`;
                    hspTaskResponseDisplay.innerHTML = initialResponseHtml; // Show this first

                    // Start polling if we got a correlation ID and success message
                    if (response.correlation_id && !response.error) {
                        if (activePolls[response.correlation_id]) { // Clear any old poll for this ID
                            clearInterval(activePolls[response.correlation_id]);
                        }
                        // Initial display for the specific task status
                        updateTaskStatusDisplay(response.correlation_id, {
                            correlation_id: response.correlation_id,
                            status: "pending_initiation", // Custom status before first poll
                            message: "Request sent, awaiting first status update..."
                        });
                        activePolls[response.correlation_id] = setInterval(() => {
                            pollTaskStatus(response.correlation_id);
                        }, 3000); // Poll every 3 seconds
                    }
                } else if (response.error) {
                     initialResponseHtml += `<strong style="color: red;">Error:</strong> ${response.error}<br>`;
                     hspTaskResponseDisplay.innerHTML = initialResponseHtml;
                } else {
                    hspTaskResponseDisplay.innerHTML = initialResponseHtml; // Should contain error message
                }
            } else {
                throw new Error("electronAPI or invoke method not available for 'hsp:request-task'.");
            }
        } catch (error) {
            console.error('Error sending HSP task request via IPC:', error);
            hspTaskResponseDisplay.innerHTML = `<p style="color: red;">IPC Error: ${error.message}</p>`;
        }
    }
});
