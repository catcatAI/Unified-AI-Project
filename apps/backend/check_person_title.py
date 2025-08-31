import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def check_person_title_pattern():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Checking PERSON_IS_TITLE_OF_ORG Pattern ===")
    
    # Test the specific pattern that's failing
    text = "Steve Jobs was a founder of Apple."
    print(f"Text: {text}")
    
    # Process the text
    doc = analyzer.nlp(text)
    
    # Print all entities
    print("\nEntities:")
    for ent in doc.ents:
        print(f"  {ent.text} ({ent.label_}) [{ent.start}:{ent.end}]")
    
    # Print all tokens with their entity types
    print("\nTokens:")
    for i, token in enumerate(doc):
        print(f"  {i}: '{token.text}' (POS: {token.pos_}, ENT_TYPE: {token.ent_type_})")
    
    # Check matcher patterns
    print("\nMatcher patterns:")
    matches = analyzer.matcher(doc)
    for match_id, start, end in matches:
        rule_id = analyzer.nlp.vocab.strings[match_id]
        span = doc[start:end]
        print(f"  {rule_id}: '{span.text}' [{start}:{end}]")
        
        # For PERSON_IS_TITLE_OF_ORG, let's debug the entity finding logic
        if rule_id == "PERSON_IS_TITLE_OF_ORG":
            print(f"    Debugging PERSON_IS_TITLE_OF_ORG:")
            print(f"    Pattern start: {start}, end: {end}")
            
            # Try to find person entity (before pattern)
            person_entity = None
            for ent in doc.ents:
                if ent.label_ == "PERSON" and ent.end <= start:
                    person_entity = ent
                    print(f"    Found person entity before pattern: '{ent.text}' [{ent.start}:{ent.end}]")
                    break
            
            if person_entity is None:
                for i in range(start - 1, -1, -1):
                    if doc[i].ent_type_ == "PERSON":
                        person_entity = doc[i]
                        print(f"    Found person token before pattern: '{doc[i].text}' [{i}]")
                        break
            
            # Try to find org entity (after pattern)
            org_entity = None
            for ent in doc.ents:
                if ent.label_ in ["ORG", "COMPANY"] and ent.start >= end:
                    org_entity = ent
                    print(f"    Found org entity after pattern: '{ent.text}' [{ent.start}:{ent.end}]")
                    break
            
            if org_entity is None:
                for i in range(end, len(doc)):
                    if doc[i].ent_type_ in ["ORG", "COMPANY"]:
                        org_entity = doc[i]
                        print(f"    Found org token after pattern: '{doc[i].text}' [{i}]")
                        break
            
            print(f"    Person entity: {person_entity}")
            print(f"    Org entity: {org_entity}")

if __name__ == "__main__":
    check_person_title_pattern()