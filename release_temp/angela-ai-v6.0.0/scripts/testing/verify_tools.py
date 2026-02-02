import asyncio
import logging
from apps.backend.src.tools.tool_registry import get_tool, get_all_schemas

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Main function to verify the tool system.
    """
    logging.info("--- Starting Tool System Verification ---")

    # 1. Verify tool loading and retrieval
    logging.info("Attempting to retrieve 'calculator' tool from the registry...")
    calculator_tool = get_tool("calculator")

    if not calculator_tool:
        logging.error("FAILED: Could not retrieve 'calculator' tool. Verification stopped.")
        return

    logging.info("SUCCESS: 'calculator' tool retrieved successfully.")
    logging.info(f"Tool Name: {calculator_tool.name}")
    logging.info(f"Tool Description: {calculator_tool.description}")

    # 2. Verify tool schema generation
    logging.info("\n--- Verifying Tool Schema ---")
    schemas = get_all_schemas()
    calc_schema = next((s for s in schemas if s['name'] == 'calculator'), None)
    if not calc_schema:
        logging.error("FAILED: Could not find schema for 'calculator' tool.")
    else:
        logging.info(f"SUCCESS: Found schema for 'calculator': {calc_schema}")

    # 3. Verify successful execution
    logging.info("\n--- Verifying Successful Execution (5 * 3) ---")
    try:
        result = await calculator_tool.execute(a=5, b=3, operator="*")
        logging.info(f"Execution Result: {result}")
        if "15" in result:
            logging.info("SUCCESS: Calculation result is correct.")
        else:
            logging.error(f"FAILED: Incorrect calculation result: {result}")
    except Exception as e:
        logging.error(f"FAILED: An unexpected error occurred during valid execution: {e}", exc_info=True)

    # 4. Verify error handling (division by zero)
    logging.info("\n--- Verifying Error Handling (10 / 0) ---")
    try:
        error_result = await calculator_tool.execute(a=10, b=0, operator="/")
        logging.info(f"Execution Result: {error_result}")
        if "error" in error_result.lower() and "zero" in error_result.lower():
            logging.info("SUCCESS: Division by zero error was handled correctly.")
        else:
            logging.error(f"FAILED: Incorrect error handling result: {error_result}")
    except Exception as e:
        logging.error(f"FAILED: An unexpected error occurred during error handling test: {e}", exc_info=True)
        
    # 5. Verify validation error (wrong argument type)
    logging.info("\n--- Verifying Validation Handling (wrong arg type) ---")
    try:
        validation_error_result = await calculator_tool.execute(a="five", b=3, operator="+ ")
        logging.info(f"Execution Result: {validation_error_result}")
        if "error" in validation_error_result.lower():
            logging.info("SUCCESS: Pydantic validation error was handled correctly.")
        else:
            logging.error(f"FAILED: Incorrect validation handling result: {validation_error_result}")
    except Exception as e:
        logging.error(f"FAILED: An unexpected error occurred during validation test: {e}", exc_info=True)

    logging.info("\n--- Tool System Verification Finished ---")

if __name__ == "__main__":
    # Setting the python path is not needed if running from the project root
    # but it's good practice for clarity if the script were elsewhere.
    # import sys
    # import os
    # sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    asyncio.run(main())
