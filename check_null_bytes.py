with open('apps/backend/src/agents/nlp_processing_agent.py', 'rb') as f:
    content = f.read()
    print('Null bytes:', content.count(b'\x00'))
    print('Length:', len(content))