import sys
import json
import time
from src.capabilities import OSCapabilities

def main():
    os_cap = OSCapabilities()
    
    if len(sys.argv) < 2:
        print("Usage: python bridge.py <command>")
        return

    command = sys.argv[1]

    if command == "snapshot":
        path = os_cap.take_screenshot()
        print(json.dumps({"status": "success", "action": "screenshot", "path": path}))
    
    elif command == "clipboard":
        content = os_cap.get_clipboard()
        print(json.dumps({"status": "success", "action": "clipboard", "content": content}))

    elif command == "open":
        if len(sys.argv) < 3:
            print(json.dumps({"status": "error", "message": "Missing app name"}))
        else:
            res = os_cap.open_app(sys.argv[2])
            print(json.dumps({"status": "success", "action": "open", "result": res}))

    elif command == "type":
        if len(sys.argv) < 3:
            print(json.dumps({"status": "error", "message": "Missing text"}))
        else:
            os_cap.backup_clipboard()
            text = " ".join(sys.argv[2:])
            res = os_cap.type_text(text)
            os_cap.restore_clipboard()
            print(json.dumps({"status": "success", "action": "type"}))

    elif command == "press":
        if len(sys.argv) < 3:
            print(json.dumps({"status": "error", "message": "Missing key name"}))
        else:
            res = os_cap.press_key(sys.argv[2])
            print(json.dumps({"status": "success", "action": "press"}))

    elif command == "scroll":
        amount = int(sys.argv[2]) if len(sys.argv) > 2 else -300
        os_cap.scroll(amount)
        print(json.dumps({"status": "success", "action": "scroll", "amount": amount}))

    elif command == "click":
        x, y = int(sys.argv[2]), int(sys.argv[3])
        os_cap.click(x, y)
        print(json.dumps({"status": "success", "action": "click", "x": x, "y": y}))

    elif command == "ocr":
        text = os_cap.ocr_screenshot()
        print(json.dumps({"status": "success", "action": "ocr", "text": text[:500]}))

    elif command == "cleanup_tabs":
        # python bridge.py cleanup_tabs <browser> <keywords_json>
        browser = sys.argv[2]
        keywords = json.loads(sys.argv[3])
        res = os_cap.cleanup_redundant_tabs(browser, keywords)
        print(json.dumps({"status": "success", "action": "cleanup_tabs", "result": res}))

    elif command == "list_windows":
        titles = os_cap.get_all_window_titles()
        print(json.dumps({"status": "success", "titles": titles}))

    elif command == "task":
        try:
            actions = json.loads(sys.argv[2])
            results = []
            with os_cap as session:
                for act in actions:
                    name = act.get("name")
                    args = act.get("args", [])
                    method = getattr(session, name, None)
                    if method:
                        res = method(*args)
                        results.append({"action": name, "result": res})
                        time.sleep(1)
            print(json.dumps({"status": "success", "results": results}))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))

    elif command == "summary":
        titles = os_cap.get_all_window_titles()
        clipboard = os_cap.get_clipboard()
        print(json.dumps({
            "status": "success", 
            "active_windows_count": len(titles),
            "window_preview": titles[:5],
            "clipboard_preview": clipboard[:100]
        }))
    
    else:
        print(json.dumps({"status": "error", "message": "Unknown command"}))

if __name__ == "__main__":
    main()
f __name__ == "__main__":
    main()
