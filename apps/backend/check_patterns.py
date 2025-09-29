import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def check_patterns():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Checking Matcher Patterns ===")
    
    # Check if nlp model is loaded
    if analyzer.nlp is None:
        print("ERROR: spaCy model not loaded")
        return
    
    # Check matcher patterns
    print("Matcher patterns:")
    try:
        stats = analyzer.matcher.get_stats()
        print(f"Stats: {stats}")
        if "patterns" in stats:
            for pattern_id in stats["patterns"]:
                try:
                    rule_name = analyzer.nlp.vocab.strings[pattern_id]
                    print(f"  {rule_name}")
                except Exception as e:
                    print(f"  Pattern ID {pattern_id} (Error: {e})")
        else:
            print("  No patterns found in stats")
    except Exception as e:
        print(f"Error getting matcher stats: {e}")
    
    # Test with a simple text
    text = "Microsoft is based in Redmond."
    print(f"\nTesting text: {text}")
    
    doc = analyzer.nlp(text)
    matches = analyzer.matcher(doc)
    
    print(f"Matches found: {len(matches)}")
    for match_id, start, end in matches:
        try:
            rule_id = analyzer.nlp.vocab.strings[match_id]
            span = doc[start:end]
            print(f"  Rule: {rule_id}, Span: '{span.text}', Start: {start}, End: {end}")
        except Exception as e:
            print(f"  Match ID: {match_id}, Span: '{doc[start:end].text}', Start: {start}, End: {end} (Error: {e})")

if __name__ == "__main__":
    check_patterns()