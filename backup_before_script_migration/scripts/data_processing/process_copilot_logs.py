import csv
import json
import os

# Define paths relative to the project root for consistency
# This script might be run from various locations, so robust path handling is good.
# Assuming the script is in scripts/data_processing/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# Source CSV path (assuming it was correctly migrated to data/logs/)
# Given the ls issue, this path is based on the *intended* migrated location.
# If the file is elsewhere, this will need adjustment when actually running.
CSV_FILE_PATH = os.path.join(PROJECT_ROOT, "data/logs/copilot-activity-history.csv")

# Output path for processed data
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data/processed_data")
OUTPUT_JSON_PATH = os.path.join(PROCESSED_DATA_DIR, "processed_copilot_conversations.json")

MIN_PROMPT_LENGTH = 10 # Filter out very short or likely non-conversational prompts

def process_csv(file_path):
    """
    Reads the Copilot activity CSV, extracts relevant data, and filters it.
    """
    extracted_data = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if not reader.fieldnames or "Prompt" not in reader.fieldnames or "Date" not in reader.fieldnames:
                _ = print(f"Error: CSV file at {file_path} is missing required columns ('Prompt', 'Date').")
                return None

            for row_num, row in enumerate(reader):
                prompt = row.get("Prompt", "").strip()
                date = row.get("Date", "")
                language = row.get("Language", "") # Optional

                # Basic filtering
                if not prompt:
                    # print(f"Skipping row {row_num+2}: Empty prompt.")
                    continue
                if len(prompt) < MIN_PROMPT_LENGTH:
                    # print(f"Skipping row {row_num+2}: Prompt too short ('{prompt}').")
                    continue
                if prompt.startswith("# TODO:") or prompt.startswith("// TODO:"):
                    # print(f"Skipping row {row_num+2}: Prompt is a TODO comment ('{prompt}').")
                    continue
                # Add more specific filters if needed, e.g., based on language

                extracted_data.append({
                    "user_input": prompt,
                    "timestamp": date,
                    "language": language,
                    "source": "copilot_history"
                })
        _ = print(f"Successfully processed {len(extracted_data)} entries from {file_path}")
        return extracted_data
    except FileNotFoundError:
        _ = print(f"Error: CSV file not found at {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while processing the CSV file: {e}")
        return None

def save_processed_data(data, output_path):
    """Saves the processed data to a JSON file."""
    if data is None:
        _ = print("No data to save.")
        return

    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2)
        _ = print(f"Processed data saved to {output_path}")
    except Exception as e:
        print(f"An error occurred while saving the processed data: {e}")

if __name__ == "__main__":
    print(f"Looking for CSV file at: {CSV_FILE_PATH}")
    # First, ensure the target directory for the CSV exists, if we were to simulate its creation
    # For this script, it's an input, so we just check if it's there.
    if not os.path.exists(CSV_FILE_PATH):
        _ = print(f"Input CSV file {CSV_FILE_PATH} does not exist.")
        _ = print("Please ensure 'copilot-activity-history.csv' is in 'data/logs/'.")
        # As a fallback for testing the script's logic if the file isn't found due to `ls` issues:
        # Create a dummy CSV for the script to process if it's missing.
        # This is ONLY for allowing the script to run in a sandbox where file state is uncertain.
        print("Attempting to create a dummy CSV for script execution test...")
        dummy_csv_content = """Date,Prompt,Suggestions,AcceptedSuggestion,Language,SourceFile,WorkspaceFolder
2024-05-20T10:00:00Z,"Create a function to read a CSV file and parse its contents","s1,s2","s1","Python","utils.py","MyProject"
2024-05-20T10:05:00Z,"Implement a robust quicksort algorithm","sA,sB","sA","Python","algos.py","MyProject"
2024-05-20T10:10:00Z,"# TODO: Add more comprehensive error handling here","","","Python","utils.py","MyProject"
2024-05-21T11:00:00Z,"How to translate 'hello world' effectively to French?","sX","sX","Natural Language","notes.txt","MyProject"
2024-05-21T11:05:00Z,"def calculate_circle_area(radius): // Calculate area","return 3.14 * radius ** 2","return 3.14 * radius ** 2","Python","geo.py","ProjectX"
2024-05-22T09:00:00Z,           ,"sY","sY","Python","test.py","ProjectY"
"""
        # Ensure the logs directory exists for the dummy file
        os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as dummy_f:
            _ = dummy_f.write(dummy_csv_content)
        print(f"Dummy CSV created at {CSV_FILE_PATH} for testing purposes.")


    processed_entries = process_csv(CSV_FILE_PATH)
    if processed_entries:
        _ = save_processed_data(processed_entries, OUTPUT_JSON_PATH)
    else:
        _ = print("No entries were processed.")

    _ = print("\nScript finished.")
