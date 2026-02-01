"""
Test script for Ollama streaming support in CognitiveOrchestrator
Tests if responses are now longer and more complete with streaming enabled
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend" / "src"))

from dotenv import load_dotenv
load_dotenv()

# Configure logging to see Ollama streaming debug messages
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_ollama_streaming():
    """Test Ollama streaming support with 3 questions"""
    print("\n" + "=" * 80)
    print("🧪 TESTING OLLAMA STREAMING SUPPORT")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        from core.orchestrator import CognitiveOrchestrator
        
        print("🔄 Initializing Angela (CognitiveOrchestrator)...")
        orchestrator = CognitiveOrchestrator()
        
        # Check available models
        print(f"✅ Orchestrator initialized")
        print(f"   LLM Available: {orchestrator.llm_available}")
        print(f"   Available Models: {orchestrator.available_models}")
        print(f"   Ollama detected: {any('llama' in m.lower() or 'phi' in m.lower() for m in orchestrator.available_models)}\n")
        
        # Define test questions
        questions = [
            "What are you curious about right now?",
            "If you could explore any topic or learn something new, what would it be?",
            "Tell me about your thoughts on artificial consciousness and what it means to you."
        ]
        
        results = []
        
        print("=" * 80)
        print("📋 RUNNING CONVERSATION TESTS")
        print("=" * 80)
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'─' * 80}")
            print(f"📝 Question {i}/{len(questions)}: {question}")
            print('─' * 80)
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Process the question
                response_data = await orchestrator.process_user_input(question)
                
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                
                # Extract the response
                if isinstance(response_data, dict):
                    response = response_data.get('response', response_data.get('message', str(response_data)))
                else:
                    response = str(response_data)
                
                # Store result
                result = {
                    'question': question,
                    'response': response,
                    'length': len(response),
                    'time': response_time,
                    'question_num': i
                }
                results.append(result)
                
                # Display response
                print(f"\n🤖 Angela's Response:")
                print(f"{'─' * 80}")
                print(response)
                print(f"{'─' * 80}")
                print(f"📊 Metrics:")
                print(f"   Response Length: {len(response)} characters")
                print(f"   Response Time: {response_time:.2f} seconds")
                print(f"   Words (approx): {len(response.split())}")
                
                # Check if response seems complete
                if len(response) < 50:
                    print(f"   ⚠️  WARNING: Response seems short (less than 50 chars)")
                elif len(response) < 100:
                    print(f"   ⚠️  Response is moderate length")
                else:
                    print(f"   ✅ Response is substantial length")
                    
            except Exception as e:
                print(f"\n❌ Error processing question {i}: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'question': question,
                    'response': f"ERROR: {str(e)}",
                    'length': 0,
                    'time': 0,
                    'question_num': i
                })
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_chars = sum(r['length'] for r in results)
        avg_length = total_chars / len(results) if results else 0
        
        print(f"\nTotal Questions: {len(results)}")
        print(f"Total Response Characters: {total_chars}")
        print(f"Average Response Length: {avg_length:.1f} characters")
        print(f"\nDetailed Results:")
        
        for result in results:
            status = "✅" if result['length'] > 100 else "⚠️" if result['length'] > 50 else "❌"
            print(f"   Q{result['question_num']}: {result['length']:4d} chars ({result['time']:.2f}s) {status}")
        
        # Analysis
        print("\n🔍 ANALYSIS:")
        if avg_length > 200:
            print("   ✅ Responses are LONGER and MORE COMPLETE (streaming is working!)")
        elif avg_length > 100:
            print("   ⚠️  Responses are MODERATE in length (streaming may be working partially)")
        else:
            print("   ❌ Responses are SHORT (streaming may not be working correctly)")
            
        print(f"\n   Expected: With streaming enabled, responses should be 150+ characters")
        print(f"   with complete sentences and more expressive content.")
        
        # Check for streaming indicators in logs
        print("\n💡 NOTES:")
        print("   - Check the log output above for 'Ollama streaming response successful'")
        print("   - Look for 'Ollama full response length' messages")
        print("   - Streaming responses should be collected from multiple chunks")
        
        print("\n✨ Test Complete!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = asyncio.run(test_ollama_streaming())
    
    # Exit code based on results
    if results:
        avg_length = sum(r['length'] for r in results) / len(results)
        if avg_length > 100:
            print("\n✅ Test PASSED: Responses are substantial")
            exit(0)
        else:
            print("\n⚠️ Test WARNING: Responses may be too short")
            exit(1)
    else:
        print("\n❌ Test FAILED")
        exit(2)
