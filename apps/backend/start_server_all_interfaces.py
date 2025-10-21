from src.services.main_api_server import app
import uvicorn
import sys

if __name"__main__":::
    try,
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt,::
        print("Server stopped by user")
        sys.exit(0)
    except Exception as e,::
        print(f"Server error, {e}")
        sys.exit(1)