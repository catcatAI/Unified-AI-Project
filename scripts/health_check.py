import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TODO: Replace with the actual API endpoint from config
API_ENDPOINT = "http://127.0.0.1:8000/api/v1/health"

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

def main():
    """Main function to run health checks."""
    logging.info("--- Starting Health Checks ---")
    check_api_health()
    # TODO: Add checks for other critical services (e.g., MQTT broker, database)
    logging.info("--- Health Checks Complete ---")

if __name__ == "__main__":
    main()
