# InternalBus: In-Memory Publish-Subscribe Message System

## Overview

This document provides an overview of the `InternalBus` module (`src/hsp/internal/internal_bus.py`). This module implements an in-memory publish-subscribe message system designed for efficient inter-component communication within the AI's single process.

## Purpose

The `InternalBus` facilitates loose coupling and asynchronous communication between different components (modules, services, agents) running within the same AI process. It allows components to publish messages to specific channels and other components to subscribe to those channels, all without direct knowledge of each other. This promotes a highly modular and event-driven architecture.

## Key Responsibilities and Features

*   **Publish-Subscribe Pattern**: Implements a classic publish-subscribe (pub-sub) messaging pattern, where publishers send messages without knowing who the subscribers are, and subscribers receive messages without knowing who the publishers are.
*   **In-Memory Operation**: All message passing occurs directly within the application's memory. This design choice makes it extremely fast and efficient for intra-process communication, minimizing latency.
*   **Channel-Based Messaging**: Messages are organized into named channels (topics). Components can publish messages to or subscribe from specific channels, allowing for logical segregation of message flows.
*   **Asynchronous Callback Handling**: Supports both synchronous and asynchronous callback functions for subscriptions. If a registered callback is an `async` function, the `InternalBus` intelligently executes it as an `asyncio.Task`, ensuring non-blocking behavior for the main event loop.

## How it Works

Components that wish to receive messages register their interest in a specific `channel` by calling the `subscribe` method and providing a callback function. When another component calls the `publish` method on that same `channel`, the `InternalBus` iterates through all registered callbacks for that channel and invokes them, passing the message as an argument. This event-driven mechanism ensures that components can react to relevant events as they occur, without needing to poll or directly query other parts of the system.

## Integration with Other Modules

*   **`HSPConnector`**: The `InternalBus` is a crucial part of the `HSPConnector`'s message bridging mechanism. It acts as the internal conduit for messages that are either received from the external MQTT broker or are destined to be sent to it.
*   **Core AI Modules**: Any module within the AI system that needs to communicate with other internal modules in a decoupled, event-driven manner would utilize this `InternalBus`. This includes various agents, managers, and services that need to react to internal events or broadcast information.

## Code Location

`src/hsp/internal/internal_bus.py`