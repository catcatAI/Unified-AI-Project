document.addEventListener('DOMContentLoaded', () => {
    const userInputField = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatDisplay = document.getElementById('chatDisplay');

    // View switching
    const chatViewButton = document.getElementById('chatViewButton');
    const hspViewButton = document.getElementById('hspViewButton');
    const gameViewButton = document.getElementById('gameViewButton');
    const chatView = document.getElementById('chatView');
    const hspServicesView = document.getElementById('hspServicesView');
    const gameView = document.getElementById('gameView');
    const startGameButton = document.getElementById('startGameButton');

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
        // Remove active class from all main views and nav buttons
        document.querySelectorAll('#mainContent > div').forEach(view => view.classList.remove('active-view'));
        document.querySelectorAll('#nav button').forEach(button => button.classList.remove('active'));

        // Add active class to the selected view and its corresponding button
        const viewToShow = document.getElementById(viewId);
        const buttonToActivate = document.getElementById(viewId + 'Button');
        
        if (viewToShow) {
            viewToShow.classList.add('active-view');
        }
        if (buttonToActivate) {
            buttonToActivate.classList.add('active');
        }

        // Special logic for HSP view
        if (viewId === 'hspServicesView' && hspServiceListDiv.children.length === 0) {
            loadHspServices();
        }
    }

    chatViewButton.addEventListener('click', () => showView('chatView'));
    hspViewButton.addEventListener('click', () => showView('hspServicesView'));
    gameViewButton.addEventListener('click', () => showView('gameView'));

    startGameButton.addEventListener('click', () => {
        if (window.electronAPI && window.electronAPI.invoke) {
            window.electronAPI.invoke('game:start');
        }
    });


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
        hspServiceListDiv.innerHTML = '<p class="loading-message"><i>Loading HSP services...</i></p>';
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const services = await window.electronAPI.invoke('hsp:get-discovered-services');
                hspServiceListDiv.innerHTML = ''; // Clear loading message
                
                if (services && services.length > 0) {
                    const ul = document.createElement('ul');
                    ul.className = 'service-list';
                    
                    services.forEach(service => {
                        const li = document.createElement('li');
                        li.className = 'service-item';
                        
                        // Create service header with name and version
                        const serviceHeader = document.createElement('div');
                        serviceHeader.className = 'service-header';
                        serviceHeader.innerHTML = `
                            <h4>${service.name} <span class="service-version">v${service.version}</span></h4>
                            <span class="service-status ${service.availability_status === 'available' ? 'status-available' : 'status-unavailable'}">
                                ${service.availability_status}
                            </span>
                        `;
                        
                        // Create service details
                        const serviceDetails = document.createElement('div');
                        serviceDetails.className = 'service-details';
                        serviceDetails.innerHTML = `
                            <div class="detail-row"><strong>ID:</strong> <span class="service-id">${service.capability_id}</span></div>
                            <div class="detail-row"><strong>Provider:</strong> ${service.ai_id}</div>
                            <div class="detail-row"><strong>Description:</strong> ${service.description || 'N/A'}</div>
                            <div class="detail-row"><strong>Tags:</strong> ${(service.tags || []).join(', ') || 'None'}</div>
                        `;
                        
                        // Create action button
                        const actionContainer = document.createElement('div');
                        actionContainer.className = 'service-actions';
                        
                        const useServiceButton = document.createElement('button');
                        useServiceButton.className = 'action-button';
                        useServiceButton.textContent = 'Use Service';
                        useServiceButton.setAttribute('data-capability-id', service.capability_id);

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
                                
                                // Scroll to the form section
                                document.querySelector('.hsp-section:nth-child(2)').scrollIntoView({ 
                                    behavior: 'smooth', 
                                    block: 'start' 
                                });
                                
                                // Focus on the parameters textarea
                                setTimeout(() => {
                                    hspTaskParamsTextareaElement?.focus();
                                }, 500);
                            } else {
                                if (!hspTaskCapIdInputElement) {
                                    console.error('HSP Task Capability ID input field (#hspTaskCapId) not found.');
                                }
                                if (!capId) {
                                    console.error('Capability ID not found on the clicked button.');
                                }
                            }
                        });

                        actionContainer.appendChild(useServiceButton);
                        
                        // Assemble the service item
                        li.appendChild(serviceHeader);
                        li.appendChild(serviceDetails);
                        li.appendChild(actionContainer);
                        ul.appendChild(li);
                    });
                    
                    hspServiceListDiv.appendChild(ul);
                } else {
                    hspServiceListDiv.innerHTML = '<p class="empty-message">No HSP services discovered.</p>';
                }
            } else {
                throw new Error("electronAPI or invoke method not available on window. Make sure preload.js is correctly exposing it.");
            }
        } catch (error) {
            console.error('Error loading HSP services:', error);
            hspServiceListDiv.innerHTML = `<p class="error-message">Error loading HSP services: ${error.message}</p>`;
        }
    }

    refreshHspServicesButton.addEventListener('click', loadHspServices);

    // Initial view setup
    chatViewButton.classList.add('active'); // Set initial active state
    showView('chatView'); // Default to chat view
    // Start a session when the renderer is ready for chat
    startNewSession();

    async function sendHspTaskIPC() {
        const targetCapabilityId = hspTaskCapIdInput.value.trim();
        const paramsJsonStr = hspTaskParamsTextarea.value.trim();

        if (!targetCapabilityId) {
            // Create error response container for missing capability ID
            hspTaskResponseDisplay.innerHTML = '';
            const errorContainer = document.createElement('div');
            errorContainer.className = 'task-status-container';
            errorContainer.innerHTML = `
                <div class="task-header">
                    <div>
                        <strong>Parameter Error</strong>
                    </div>
                    <span class="status-badge status-badge-error">error</span>
                </div>
                <div class="task-error">
                    <div class="error-header">Error:</div>
                    <div>Target Capability ID is required.</div>
                </div>
            `;
            hspTaskResponseDisplay.appendChild(errorContainer);
            return;
        }

        let parameters;
        try {
            parameters = paramsJsonStr ? JSON.parse(paramsJsonStr) : {};
        } catch (e) {
            // Create error response container for JSON parsing error
            hspTaskResponseDisplay.innerHTML = '';
            const errorContainer = document.createElement('div');
            errorContainer.className = 'task-status-container';
            errorContainer.innerHTML = `
                <div class="task-header">
                    <div>
                        <strong>Parameter Error</strong>
                    </div>
                    <span class="status-badge status-badge-error">error</span>
                </div>
                <div class="task-error">
                    <div class="error-header">Invalid JSON parameters:</div>
                    <div>${e.message}</div>
                </div>
            `;
            hspTaskResponseDisplay.appendChild(errorContainer);
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
            statusDiv.className = 'task-status-container';
            // Prepend to hspTaskResponseDisplay so new statuses appear at the top
            hspTaskResponseDisplay.insertBefore(statusDiv, hspTaskResponseDisplay.firstChild);
        }

        // Create status badge with appropriate color
        const getStatusBadgeClass = (status) => {
            switch(status) {
                case 'completed': return 'status-badge-success';
                case 'failed': return 'status-badge-error';
                case 'pending': return 'status-badge-pending';
                case 'in_progress': return 'status-badge-progress';
                case 'unknown_or_expired': return 'status-badge-unknown';
                default: return 'status-badge-default';
            }
        };

        const timestamp = new Date().toLocaleTimeString();
        
        let statusHtml = `
            <div class="task-header">
                <div>
                    <strong>Task ID:</strong> <span class="task-id">${correlationId}</span>
                    <span class="task-timestamp">${timestamp}</span>
                </div>
                <span class="status-badge ${getStatusBadgeClass(statusData.status)}">${statusData.status}</span>
            </div>
        `;
        
        if (statusData.message) {
            statusHtml += `<div class="task-message"><em>${statusData.message}</em></div>`;
        }
        
        if (statusData.status === "completed" && statusData.result_payload) {
            statusHtml += `
                <div class="task-result">
                    <div class="result-header">Result:</div>
                    <pre>${JSON.stringify(statusData.result_payload, null, 2)}</pre>
                </div>
            `;
        }
        
        if (statusData.status === "failed" && statusData.error_details) {
            statusHtml += `
                <div class="task-error">
                    <div class="error-header">Error:</div>
                    <pre>${JSON.stringify(statusData.error_details, null, 2)}</pre>
                </div>
            `;
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
            // Create error response container for missing capability ID
            hspTaskResponseDisplay.innerHTML = '';
            const errorContainer = document.createElement('div');
            errorContainer.className = 'task-status-container';
            errorContainer.innerHTML = `
                <div class="task-header">
                    <div>
                        <strong>Parameter Error</strong>
                    </div>
                    <span class="status-badge status-badge-error">error</span>
                </div>
                <div class="task-error">
                    <div class="error-header">Error:</div>
                    <div>Target Capability ID is required.</div>
                </div>
            `;
            hspTaskResponseDisplay.appendChild(errorContainer);
            return;
        }
        let parameters;
        try {
            parameters = paramsJsonStr ? JSON.parse(paramsJsonStr) : {};
        } catch (e) {
            // Create error response container for JSON parsing error
            hspTaskResponseDisplay.innerHTML = '';
            const errorContainer = document.createElement('div');
            errorContainer.className = 'task-status-container';
            errorContainer.innerHTML = `
                <div class="task-header">
                    <div>
                        <strong>Parameter Error</strong>
                    </div>
                    <span class="status-badge status-badge-error">error</span>
                </div>
                <div class="task-error">
                    <div class="error-header">Invalid JSON parameters:</div>
                    <div>${e.message}</div>
                </div>
            `;
            hspTaskResponseDisplay.appendChild(errorContainer);
            return;
        }

        // Create a loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Sending HSP task request...</p>
        `;
        hspTaskResponseDisplay.innerHTML = '';
        hspTaskResponseDisplay.appendChild(loadingDiv);
        try {
            if (window.electronAPI && window.electronAPI.invoke) {
                const response = await window.electronAPI.invoke('hsp:request-task', { targetCapabilityId, parameters });
                // Remove loading indicator
                hspTaskResponseDisplay.innerHTML = '';
                
                // Create initial response container
                const responseContainer = document.createElement('div');
                responseContainer.className = 'initial-response';
                
                if (response.correlation_id) {
                    responseContainer.innerHTML = `
                        <div class="response-header">
                            <h4>Task Request Sent</h4>
                            <span class="status-badge status-badge-pending">pending</span>
                        </div>
                        <div class="response-details">
                            <div><strong>Status:</strong> ${response.status_message}</div>
                            <div><strong>Correlation ID:</strong> <span class="task-id">${response.correlation_id}</span></div>
                            <div class="polling-message"><i>Polling for final status...</i></div>
                        </div>
                    `;
                    hspTaskResponseDisplay.appendChild(responseContainer);

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
                    // Create error response container
                    const errorContainer = document.createElement('div');
                    errorContainer.className = 'task-status-container';
                    errorContainer.innerHTML = `
                        <div class="task-header">
                            <div>
                                <strong>Task Request Failed</strong>
                            </div>
                            <span class="status-badge status-badge-error">error</span>
                        </div>
                        <div class="task-error">
                            <div class="error-header">Error:</div>
                            <div>${response.error}</div>
                        </div>
                    `;
                    hspTaskResponseDisplay.appendChild(errorContainer);
                } else {
                    // Create generic response container
                    const genericContainer = document.createElement('div');
                    genericContainer.className = 'task-status-container';
                    genericContainer.innerHTML = `
                        <div class="task-header">
                            <div>
                                <strong>Task Request Status</strong>
                            </div>
                        </div>
                        <div>
                            <div>${response.status_message || 'No status message provided'}</div>
                        </div>
                    `;
                    hspTaskResponseDisplay.appendChild(genericContainer);
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
