function showView(viewId) {
    // Remove active class from all main views and nav buttons
    document
        .querySelectorAll("#mainContent > div")
        .forEach((view) => view.classList.remove("active-view"));
    document
        .querySelectorAll("#nav button")
        .forEach((button) => button.classList.remove("active"));

    // Add active class to the selected view and its corresponding button
    const viewToShow = document.getElementById(viewId);
    const buttonToActivate = document.getElementById(viewId + "Button");

    if (viewToShow) {
        viewToShow.classList.add("active-view");
    }
    if (buttonToActivate) {
        buttonToActivate.classList.add("active");
    }
}

function renderChatMessages(messages) {
    const chatDisplay = document.getElementById("chatDisplay");
    chatDisplay.innerHTML = "";
    messages.forEach(message => {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message");
        messageDiv.classList.add(message.sender === "user" ? "user-message" : "ai-message");

        const strong = document.createElement("strong");
        strong.textContent = message.sender === "user" ? "You: " : "AI: ";

        messageDiv.appendChild(strong);
        messageDiv.appendChild(document.createTextNode(message.text));

        chatDisplay.appendChild(messageDiv);
    });
    chatDisplay.scrollTop = chatDisplay.scrollHeight; // Auto-scroll to bottom
}

function renderHspServices(services) {
    const hspServiceListDiv = document.getElementById("hspServiceList");
    hspServiceListDiv.innerHTML = ""; // Clear loading message

    if (services && services.length > 0) {
        const ul = document.createElement("ul");
        ul.className = "service-list";

        services.forEach((service) => {
            const li = document.createElement("li");
            li.className = "service-item";

            // Create service header with name and version
            const serviceHeader = document.createElement("div");
            serviceHeader.className = "service-header";
            serviceHeader.innerHTML = `
                            <h4>${service.name} <span class="service-version">v${service.version}</span></h4>
                            <span class="service-status ${service.availability_status === "available" ? "status-available" : "status-unavailable"}">
                                ${service.availability_status}
                            </span>
                        `;

            // Create service details
            const serviceDetails = document.createElement("div");
            serviceDetails.className = "service-details";
            serviceDetails.innerHTML = `
                            <div class="detail-row"><strong>ID:</strong> <span class="service-id">${service.capability_id}</span></div>
                            <div class="detail-row"><strong>Provider:</strong> ${service.ai_id}</div>
                            <div class="detail-row"><strong>Description:</strong> ${service.description || "N/A"}</div>
                            <div class="detail-row"><strong>Tags:</strong> ${(service.tags || []).join(", ") || "None"}</div>
                        `;

            // Create action button
            const actionContainer = document.createElement("div");
            actionContainer.className = "service-actions";

            const useServiceButton = document.createElement("button");
            useServiceButton.className = "action-button";
            useServiceButton.textContent = "Use Service";
            useServiceButton.setAttribute(
                "data-capability-id",
                service.capability_id,
            );

            useServiceButton.addEventListener("click", (event) => {
                const capId = event.target.getAttribute("data-capability-id");
                const hspTaskCapIdInputElement =
                    document.getElementById("hspTaskCapId");
                const hspTaskParamsTextareaElement =
                    document.getElementById("hspTaskParams");

                if (hspTaskCapIdInputElement && capId) {
                    hspTaskCapIdInputElement.value = capId;
                    if (hspTaskParamsTextareaElement) {
                        hspTaskParamsTextareaElement.value = ""; // Clear previous params
                    }
                    console.log(
                        `Capability ID '${capId}' populated into task form.`,
                    );

                    // Scroll to the form section
                    document
                        .querySelector(".hsp-section:nth-child(2)")
                        .scrollIntoView({
                            behavior: "smooth",
                            block: "start",
                        });

                    // Focus on the parameters textarea
                    setTimeout(() => {
                        hspTaskParamsTextareaElement?.focus();
                    }, 500);
                } else {
                    if (!hspTaskCapIdInputElement) {
                        console.error(
                            "HSP Task Capability ID input field (#hspTaskCapId) not found.",
                        );
                    }
                    if (!capId) {
                        console.error(
                            "Capability ID not found on the clicked button.",
                        );
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
        hspServiceListDiv.innerHTML =
            '<p class="empty-message">No HSP services discovered.</p>';
    }
}

function renderHspTaskStatus(taskStatus) {
    const hspTaskResponseDisplay = document.getElementById("hspTaskResponseDisplay");
    hspTaskResponseDisplay.innerHTML = "";
    for (const correlationId in taskStatus) {
        const statusData = taskStatus[correlationId];
        let statusDiv = document.getElementById(`hsp-task-status-${correlationId}`);
        if (!statusDiv) {
            statusDiv = document.createElement("div");
            statusDiv.id = `hsp-task-status-${correlationId}`;
            statusDiv.className = "task-status-container";
            // Prepend to hspTaskResponseDisplay so new statuses appear at the top
            hspTaskResponseDisplay.insertBefore(
                statusDiv,
                hspTaskResponseDisplay.firstChild,
            );
        }

        // Create status badge with appropriate color
        const getStatusBadgeClass = (status) => {
            switch (status) {
                case "completed":
                    return "status-badge-success";
                case "failed":
                    return "status-badge-error";
                case "pending":
                    return "status-badge-pending";
                case "in_progress":
                    return "status-badge-progress";
                case "unknown_or_expired":
                    return "status-badge-unknown";
                default:
                    return "status-badge-default";
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
    }
}

function showNotification(type, message) {
    const notificationCenter = document.getElementById('notificationCenter');
    const notification = Notification({ type, message });
    notificationCenter.appendChild(notification);

    // Automatically remove the notification after a few seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function renderSettings(settings) {
    const themeSelect = document.getElementById("themeSelect");
    const defaultModelInput = document.getElementById("defaultModelInput");

    themeSelect.value = settings.theme;
    defaultModelInput.value = settings.defaultModel;

    document.body.className = `theme-${settings.theme}`;
}

// 新增函数：渲染Atlassian集成状态
function renderAtlassianStatus(status) {
    const atlassianStatusDiv = document.getElementById("atlassianStatus");
    if (!atlassianStatusDiv) return;

    if (!status || !status.services) {
        atlassianStatusDiv.innerHTML = '<p class="empty-message">No Atlassian services connected.</p>';
        return;
    }

    let statusHtml = '<div class="atlassian-services">';
    status.services.forEach(service => {
        const statusClass = service.status === 'connected' ? 'status-available' : 
                           service.status === 'error' ? 'status-error' : 'status-unavailable';
        
        statusHtml += `
            <div class="service-item">
                <div class="service-header">
                    <h4>${service.name}</h4>
                    <span class="service-status ${statusClass}">${service.status}</span>
                </div>
                <div class="service-details">
                    <div class="detail-row"><strong>Last Sync:</strong> ${service.lastSync}</div>
                    <div class="detail-row"><strong>Health:</strong> ${service.health}%</div>
                </div>
            </div>
        `;
    });
    statusHtml += '</div>';

    atlassianStatusDiv.innerHTML = statusHtml;
}

// 新增函数：渲染Jira项目列表
function renderJiraProjects(projects) {
    const jiraProjectsDiv = document.getElementById("jiraProjects");
    if (!jiraProjectsDiv) return;

    if (!projects || projects.length === 0) {
        jiraProjectsDiv.innerHTML = '<p class="empty-message">No Jira projects found.</p>';
        return;
    }

    let projectsHtml = '<div class="project-list">';
    projects.forEach(project => {
        projectsHtml += `
            <div class="project-item">
                <div class="project-header">
                    <h4>${project.name} (${project.key})</h4>
                </div>
                <div class="project-details">
                    <p>${project.description || 'No description'}</p>
                </div>
            </div>
        `;
    });
    projectsHtml += '</div>';

    jiraProjectsDiv.innerHTML = projectsHtml;
}

// 新增函数：渲染Confluence空间列表
function renderConfluenceSpaces(spaces) {
    const confluenceSpacesDiv = document.getElementById("confluenceSpaces");
    if (!confluenceSpacesDiv) return;

    if (!spaces || spaces.length === 0) {
        confluenceSpacesDiv.innerHTML = '<p class="empty-message">No Confluence spaces found.</p>';
        return;
    }

    let spacesHtml = '<div class="space-list">';
    spaces.forEach(space => {
        spacesHtml += `
            <div class="space-item">
                <div class="space-header">
                    <h4>${space.name} (${space.key})</h4>
                </div>
                <div class="space-details">
                    <p>${space.description || 'No description'}</p>
                </div>
            </div>
        `;
    });
    spacesHtml += '</div>';

    confluenceSpacesDiv.innerHTML = spacesHtml;
}

// 新增函数：渲染Rovo Dev Agents
function renderRovoAgents(agents) {
    const rovoAgentsDiv = document.getElementById("rovoAgents");
    if (!rovoAgentsDiv) return;

    if (!agents || agents.length === 0) {
        rovoAgentsDiv.innerHTML = '<p class="empty-message">No Rovo Dev agents found.</p>';
        return;
    }

    let agentsHtml = '<div class="agent-list">';
    agents.forEach(agent => {
        const statusClass = agent.status === 'active' ? 'status-available' : 
                           agent.status === 'busy' ? 'status-progress' : 'status-unavailable';
        
        agentsHtml += `
            <div class="agent-item">
                <div class="agent-header">
                    <h4>${agent.name}</h4>
                    <span class="service-status ${statusClass}">${agent.status}</span>
                </div>
                <div class="agent-details">
                    <div class="detail-row"><strong>ID:</strong> ${agent.id}</div>
                    <div class="detail-row"><strong>Capabilities:</strong> ${agent.capabilities.join(', ')}</div>
                </div>
            </div>
        `;
    });
    agentsHtml += '</div>';

    rovoAgentsDiv.innerHTML = agentsHtml;
}

// 新增函数：渲染Rovo Dev Tasks
function renderRovoTasks(tasks) {
    const rovoTasksDiv = document.getElementById("rovoTasks");
    if (!rovoTasksDiv) return;

    if (!tasks || tasks.length === 0) {
        rovoTasksDiv.innerHTML = '<p class="empty-message">No Rovo Dev tasks found.</p>';
        return;
    }

    let tasksHtml = '<div class="task-list">';
    tasks.forEach(task => {
        const statusClass = task.status === 'completed' ? 'status-available' : 
                           task.status === 'in_progress' ? 'status-progress' : 
                           task.status === 'pending' ? 'status-pending' : 'status-unavailable';
        
        tasksHtml += `
            <div class="task-item">
                <div class="task-header">
                    <h4>${task.title}</h4>
                    <span class="service-status ${statusClass}">${task.status}</span>
                </div>
                <div class="task-details">
                    <div class="detail-row"><strong>ID:</strong> ${task.id}</div>
                    <div class="detail-row"><strong>Agent:</strong> ${task.agentId}</div>
                    <div class="detail-row"><strong>Created:</strong> ${new Date(task.createdAt).toLocaleString()}</div>
                    <div class="detail-row"><strong>Updated:</strong> ${new Date(task.updatedAt).toLocaleString()}</div>
                </div>
            </div>
        `;
    });
    tasksHtml += '</div>';

    rovoTasksDiv.innerHTML = tasksHtml;
}

function render() {
    const state = window.store.getState();
    showView(state.activeView);
    renderChatMessages(state.chat.messages);
    renderHspServices(state.hsp.services);
    renderHspTaskStatus(state.hsp.taskStatus);
    renderSettings(state.settings);

    // 渲染Atlassian集成相关状态
    if (state.atlassian) {
        renderAtlassianStatus(state.atlassian.status);
        renderJiraProjects(state.atlassian.projects);
        renderConfluenceSpaces(state.atlassian.spaces);
        renderRovoAgents(state.atlassian.agents);
        renderRovoTasks(state.atlassian.tasks);
    }

    if (state.ui.errorMessage) {
        showNotification('error', state.ui.errorMessage);
        window.store.updateState(window.store.actions.setErrorMessage, null);
    }
}