from src.services.main_api_server import app
import uvicorn
import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)