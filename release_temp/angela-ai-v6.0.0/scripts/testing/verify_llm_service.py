import asyncio
import logging

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Main function to verify the LLM service integration.
    """
    logging.info("--- Starting LLM Service Integration Verification ---")

    try:
        # This import triggers the creation of the singleton and the loading of providers.
        from apps.backend.src.services.llm_service import llm_manager
        logging.info("Successfully imported the shared llm_manager instance.")
    except Exception as e:
        logging.error(f"FAILED: Could not import llm_manager. Error: {e}", exc_info=True)
        return

    # --- Test Case 1: Hugging Face Local Provider ---
    # This model is small and should be quick to download and run.
    # It is mapped to 'huggingface_local' in model_manager.py.
    local_model = "distilgpt2"
    prompt = "Hello, world! This is a test of the local LLM service."
    
    logging.info(f"\n--- Attempting to generate text with local model: '{local_model}' ---")
    logging.info("This may take some time on the first run as the model needs to be downloaded.")

    try:
        response = await llm_manager.generate(model=local_model, prompt=prompt)
        
        if response and response.text:
            logging.info(f"SUCCESS: Generation complete.")
            logging.info(f"Prompt: '{prompt}'")
            logging.info(f"Response: '{response.text}'")
        else:
            logging.error(f"FAILED: The model returned an empty or invalid response: {response}")

    except Exception as e:
        logging.error(f"FAILED: An error occurred during generation with '{local_model}'. Error: {e}", exc_info=True)
        logging.error("This could be due to a network issue preventing the model download, or a runtime error.")

    # --- Test Case 2: Check for disabled provider ---
    # This model is mapped to the 'openai' provider, which should be disabled without an API key.
    openai_model = "gpt-3.5-turbo"
    logging.info(f"\n--- Verifying that disabled provider for '{openai_model}' fails gracefully ---")
    
    try:
        await llm_manager.generate(model=openai_model, prompt="This should fail.")
        # If this line is reached, it's a failure because an exception was expected.
        logging.error(f"FAILED: Request to disabled provider '{openai_model}' did not raise an exception as expected.")
    except ValueError as e:
        # A ValueError is expected because the provider was not loaded successfully.
        logging.info(f"SUCCESS: Request to disabled provider failed as expected with a ValueError: {e}")
    except Exception as e:
        logging.error(f"FAILED: An unexpected error occurred while testing disabled provider. Error: {e}", exc_info=True)


    logging.info("\n--- LLM Service Integration Verification Finished ---")


if __name__ == "__main__":
    asyncio.run(main())
