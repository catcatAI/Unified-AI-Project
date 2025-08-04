# UI Package

This package contains shared UI components and design system for the Unified AI Project frontend applications.

## Overview

The UI package provides reusable React components built with TypeScript, following modern design patterns and accessibility standards.

## Components

This package includes the following UI components:

- **Alert**: Display important messages and notifications
- **Badge**: Show status indicators and labels
- **Button**: Interactive buttons with various styles
- **Card**: Container components for content organization
- **Dialog**: Modal dialogs and overlays
- **Input**: Form input fields
- **Label**: Form labels and text elements
- **Progress**: Progress indicators and loading states
- **ScrollArea**: Custom scrollable areas
- **Select**: Dropdown selection components
- **Separator**: Visual dividers and separators
- **Tabs**: Tabbed navigation components
- **Textarea**: Multi-line text input fields

## Development

### Testing
```bash
# Run tests
pnpm test

# Run tests in watch mode
pnpm test:watch
```

### Building
```bash
# Build the package
pnpm build
```

## Usage

This package is designed to be used by the frontend applications in the monorepo:
- `apps/frontend-dashboard`
- `apps/desktop-app`

Components are exported from the main index file and can be imported as needed by the consuming applications.