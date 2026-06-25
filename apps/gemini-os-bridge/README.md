# Gemini OS Bridge

OS automation microservice for desktop interaction tasks — file operations, search, browser control, image capture.

## Structure

| Path | Description |
|------|-------------|
| `bridge.py` | Main service entry point |
| `src/` | Source modules |
| `requirements.txt` | Python dependencies |
| `SPECIFICATION.md` | Full API specification |
| `task_*.py` | Task-specific automation scripts (search, image capture, browser control) |

## Usage

Run the bridge service:

```bash
python apps/gemini-os-bridge/bridge.py
```

## Dependencies

- `pyautogui` — desktop automation
- `pyperclip` — clipboard access
- `requests` — HTTP API calls
