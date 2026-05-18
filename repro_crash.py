
import sys
import os
import asyncio
import logging

# Setup path
sys.path.insert(0, os.path.join(os.getcwd(), 'apps/backend/src'))

# Disable logging to keep output clean
logging.basicConfig(level=logging.ERROR)

async def reproduce():
    try:
        from services.chat_service import get_angela_chat_service
        service = get_angela_chat_service()
        
        # This should trigger the crash if _handle_general_intent is missing
        print("Testing general intent...")
        response = await service.generate_response("你好", user_name="TestUser")
        print(f"Response: {response}")
    except AttributeError as e:
        print(f"Caught expected AttributeError: {e}")
    except Exception as e:
        print(f"Caught unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
