# Data Archive Usage Guide

## Overview

The Data Archive feature in the AI Unified Dashboard allows you to store, manage, and review your AI interaction history. This includes chat conversations, generated images, web searches, and code analysis results.

## Features

1. **Automatic Archiving**: AI interactions are automatically saved to the archive
2. **Manual Archiving**: Save specific interactions manually
3. **Search and Filter**: Find specific entries by type or content
4. **Export**: Export your archive data as JSON
5. **Delete**: Remove individual entries or clear the entire archive

## Using the Archive Manager

### Accessing the Archive

1. Open the AI Unified Dashboard
2. Click on "Archive Manager" in the sidebar navigation

### Archive Manager Interface

The Archive Manager interface consists of:

- **Tab Navigation**: Switch between different types of archives (All, Chat, Images, Search, Code)
- **Search Bar**: Search through your archive entries
- **Export Button**: Export all archive data as JSON
- **Clear All Button**: Delete all archive entries
- **Archive List**: View your archived entries with input, output, and metadata

### Filtering Archives

You can filter your archives by type using the tab navigation:
- **All**: View all archive entries
- **Chat**: View only chat conversations
- **Images**: View only image generation records
- **Search**: View only web search records
- **Code**: View only code analysis records

### Searching Archives

Use the search bar to find specific entries by searching through both input and output content.

### Exporting Archives

Click the "Export" button to download all archive entries as a JSON file. The file will be named with the current date (e.g., `archive-export-2023-12-01.json`).

### Deleting Archives

#### Individual Entries
1. Find the entry you want to delete
2. Click the trash can icon next to the entry
3. Confirm deletion in the dialog

#### All Entries
1. Click the "Clear All" button
2. Confirm deletion in the dialog

## Automatic Archiving

The system automatically archives the following interactions:

- **Chat Messages**: After receiving an AI response, the user input and AI output are saved
- **Image Generation**: After generating an image, the prompt and image URL are saved
- **Web Search**: After performing a search, the query and results are saved
- **Code Analysis**: After analyzing code, the input code and analysis results are saved

## Manual Archiving

You can manually save specific interactions to the archive:

### Chat Messages
1. Find the AI response you want to save
2. Click the archive icon (box with arrow) in the message actions
3. The conversation (user input and AI output) will be saved to the archive

### Images
1. Find the generated image you want to save
2. Hover over the image to reveal the action buttons
3. Click the archive icon (box with arrow)
4. The image prompt and URL will be saved to the archive

## Data Structure

Each archive entry contains the following information:

- **ID**: Unique identifier for the entry
- **Type**: Type of interaction (chat, image, search, code)
- **Input**: User input that triggered the interaction
- **Output**: AI response or result
- **Metadata**: Additional information (e.g., image size, code language)
- **Created At**: Timestamp when the entry was created

## Privacy and Security

- Archive data is stored locally in your browser's database
- No archive data is sent to external servers
- You can delete your archive data at any time
- Exported archive files contain sensitive information and should be handled securely

## Best Practices

1. **Regular Export**: Periodically export your archive to prevent data loss
2. **Secure Storage**: Store exported archive files in a secure location
3. **Selective Archiving**: Use manual archiving for important interactions
4. **Regular Cleanup**: Delete unnecessary entries to keep your archive organized

## Troubleshooting

### Archive Not Loading
- Refresh the page
- Check browser console for errors
- Ensure database permissions are granted

### Export Not Working
- Check browser download permissions
- Ensure sufficient disk space is available
- Try using a different browser

### Data Not Archiving
- Check browser console for errors
- Ensure you're using the latest version of the dashboard
- Verify database connectivity