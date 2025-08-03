import requests
import time
import logging
import yaml
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API endpoint from config
CONFIG_PATH = "D:\Projects\Unified-AI-Project\configs\system_config.yaml"

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

API_HOST = config['system']['api_server']['host']
API_PORT = config['system']['api_server']['port']
API_ENDPOINT = f"http://{API_HOST}:{API_PORT}/api/v1/health"

def check_api_health():
    """Checks the health of the main API server."""
    try:
        start_time = time.time()
        response = requests.get(API_ENDPOINT, timeout=5)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # in milliseconds

        if response.status_code == 200:
            logging.info(f"API is HEALTHY. Status: {response.status_code}. Response time: {response_time:.2f}ms")
            # Optionally, check response content
            # data = response.json()
            # if data.get("status") == "ok":
            #     logging.info("API status is 'ok'.")
            # else:
            #     logging.warning(f"API status is not 'ok'. Response: {data}")
        else:
            logging.error(f"API is UNHEALTHY. Status: {response.status_code}. Response time: {response_time:.2f}ms")
            logging.error(f"Response content: {response.text}")

    except requests.exceptions.RequestException as e:
        logging.error(f"API is UNREACHABLE. Error: {e}")

def check_firebase_credentials():
    """Checks if Firebase credentials path is set and the file exists."""
    firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not firebase_credentials_path:
        logging.warning("FIREBASE_CREDENTIALS_PATH environment variable is not set.")
        return False

    credentials_file = Path(firebase_credentials_path)
    if credentials_file.is_file():
        logging.info(f"Firebase credentials file found at: {firebase_credentials_path}")
        return True
    else:
        logging.error(f"Firebase credentials file NOT FOUND at: {firebase_credentials_path}")
        return False

def check_mqtt_broker():
    """Placeholder for checking MQTT broker health."""
    logging.info("Checking MQTT broker health (placeholder)...")
    # Example check: try to connect to the broker
    # try:
    #     # mqtt_client = mqtt.Client()
    #     # mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    #     # mqtt_client.disconnect()
    #     logging.info("MQTT broker is HEALTHY (simulated).")
    #     return True
    # except Exception as e:
    #     logging.error(f"MQTT broker is UNHEALTHY. Error: {e}")
    #     return False
    pass

def check_database():
    """Placeholder for checking database health."""
    logging.info("Checking database health (placeholder)...")
    # Example check: try to connect to the database and run a simple query
    # try:
    #     # db_connection = connect_to_database()
    #     # cursor = db_connection.cursor()
    #     # cursor.execute("SELECT 1")
    #     # cursor.fetchone()
    #     # db_connection.close()
    #     logging.info("Database is HEALTHY (simulated).")
    #     return True
    # except Exception as e:
    #     logging.error(f"Database is UNHEALTHY. Error: {e}")
    #     return False
    pass

def main():
    """Main function to run health checks."""
    logging.info("--- Starting Health Checks ---")
    check_api_health()
    check_firebase_credentials()
    check_mqtt_broker()
    check_database()
    logging.info("--- Health Checks Complete ---")

if __name__ == "__main__":
    main()
