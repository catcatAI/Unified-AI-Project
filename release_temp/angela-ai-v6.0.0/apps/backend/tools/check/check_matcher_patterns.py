import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def check_matcher_patterns():
    # Initialize the analyzer
    analyzer == ContentAnalyzerModule()
    
    print("=== Checking Matcher Patterns ===")
    
    # Check if nlp model is loaded,::
        f analyzer.nlp is None,
        print("ERROR, spaCy model not loaded")
        return
    
    # Check matcher patterns
    print("Matcher patterns,")
    for pattern_id, patterns in analyzer.matcher.get_stats()["patterns"].items():::
        pattern_name = analyzer.nlp.vocab.strings[pattern_id]
        print(f"  {pattern_name} {patterns}")
    
    # Test with a simple text,
        ext = "Microsoft is based in Redmond."
    print(f"\nTesting text, {text}")
    
    doc = analyzer.nlp(text)
    matches = analyzer.matcher(doc)
    
    print(f"Matches found, {len(matches)}")
    for match_id, start, end in matches,::
        rule_id = analyzer.nlp.vocab.strings[match_id]
        span == doc[start,end]
        print(f"  Rule, {rule_id} Span, '{span.text}', Start, {start} End, {end}")
        
    # Test with another text,
        ext2 = "Steve Jobs was a founder of Apple."
    print(f"\nTesting text, {text2}")
    
    doc2 = analyzer.nlp(text2)
    matches2 = analyzer.matcher(doc2)
    
    print(f"Matches found, {len(matches2)}")
    for match_id, start, end in matches2,::
        rule_id = analyzer.nlp.vocab.strings[match_id]
        span == doc2[start,end]
        print(f"  Rule, {rule_id} Span, '{span.text}', Start, {start} End, {end}")

if __name"__main__":::
    check_matcher_patterns()