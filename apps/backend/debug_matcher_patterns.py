import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import spacy
from spacy.matcher import Matcher
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_matcher_patterns():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debugging Matcher Patterns ===")
    
    # Test the PERSON_IS_TITLE_OF_ORG pattern
    print("\n1. Testing PERSON_IS_TITLE_OF_ORG pattern")
    text = "Steve Jobs was a founder of Apple."
    print(f"Text: {text}")
    
    # Process the text with spaCy
    doc = analyzer.nlp(text) if analyzer.nlp else None
    if doc is None:
        print("Failed to process text with spaCy")
        return
    
    # Print tokens and their properties
    print("\nTokens:")
    for i, token in enumerate(doc):
        print(f"  {i}: '{token.text}' - POS: {token.pos_}, LEMMA: {token.lemma_}, ENT_TYPE: {token.ent_type_}")
    
    # Print entities
    print("\nEntities:")
    for ent in doc.ents:
        print(f"  '{ent.text}' - TYPE: {ent.label_}, START: {ent.start}, END: {ent.end}")
    
    # Apply matcher patterns
    matches = analyzer.matcher(doc)
    print(f"\nMatches found: {len(matches)}")
    for match_id, start, end in matches:
        rule_id = analyzer.nlp.vocab.strings[match_id] if analyzer.nlp else "unknown"
        span = doc[start:end]
        print(f"  Rule: {rule_id}, Span: '{span.text}', Start: {start}, End: {end}")
        
        # Print tokens in the match
        print(f"    Match tokens:")
        for i in range(start, end):
            print(f"      {i}: '{doc[i].text}' - POS: {doc[i].pos_}, LEMMA: {doc[i].lemma_}, ENT_TYPE: {doc[i].ent_type_}")
    
    # Test the WORKS_FOR pattern
    print("\n\n2. Testing WORKS_FOR pattern")
    text2 = "John Doe works for Acme Corp."
    print(f"Text: {text2}")
    
    # Process the text with spaCy
    doc2 = analyzer.nlp(text2) if analyzer.nlp else None
    if doc2 is None:
        print("Failed to process text with spaCy")
        return
    
    # Print tokens and their properties
    print("\nTokens:")
    for i, token in enumerate(doc2):
        print(f"  {i}: '{token.text}' - POS: {token.pos_}, LEMMA: {token.lemma_}, ENT_TYPE: {token.ent_type_}")
    
    # Print entities
    print("\nEntities:")
    for ent in doc2.ents:
        print(f"  '{ent.text}' - TYPE: {ent.label_}, START: {ent.start}, END: {ent.end}")
    
    # Apply matcher patterns
    matches2 = analyzer.matcher(doc2)
    print(f"\nMatches found: {len(matches2)}")
    for match_id, start, end in matches2:
        rule_id = analyzer.nlp.vocab.strings[match_id] if analyzer.nlp else "unknown"
        span = doc2[start:end]
        print(f"  Rule: {rule_id}, Span: '{span.text}', Start: {start}, End: {end}")
        
        # Print tokens in the match
        print(f"    Match tokens:")
        for i in range(start, end):
            print(f"      {i}: '{doc2[i].text}' - POS: {doc2[i].pos_}, LEMMA: {doc2[i].lemma_}, ENT_TYPE: {doc2[i].ent_type_}")

if __name__ == "__main__":
    debug_matcher_patterns()