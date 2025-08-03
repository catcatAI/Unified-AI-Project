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

function render() {
    const state = window.store.getState();
    showView(state.activeView);
    renderChatMessages(state.chat.messages);
    renderHspServices(state.hsp.services);
    renderHspTaskStatus(state.hsp.taskStatus);
    renderSettings(state.settings);

    if (state.ui.errorMessage) {
        showNotification('error', state.ui.errorMessage);
        window.store.updateState(window.store.actions.setErrorMessage, null);
    }
}
