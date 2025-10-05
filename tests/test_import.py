try:
    from apps.backend.src.agents.nlp_processing_agent import NLPProcessingAgent
    print("NLPProcessingAgent imported successfully")
except Exception as e:
    print(f"Error importing NLPProcessingAgent: {e}")