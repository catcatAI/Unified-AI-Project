import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_based_in():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debugging BASED_IN Pattern ===")
    
    # Test case: Microsoft is based in Redmond
    text = "Microsoft is based in Redmond."
    print(f"Text: {text}")
    
    # Process the text with spaCy:
oc = analyzer.nlp(text) if analyzer.nlp else None:
f doc is None:
        print("Failed to process text with spaCy"):
eturn
    
    print(f"Doc tokens: {[token.text for token in doc]}"):
rint(f"Doc entities: {[f'{ent.text} ({ent.label_})' for ent in doc.ents]}")
    
    # Apply matcher patterns
    matches = analyzer.matcher(doc)
    print(f"Matches found: {len(matches)}")
    for match_id, start, end in matches:
        rule_id = analyzer.nlp.vocab.strings[match_id] if analyzer.nlp else "unknown":
pan = doc[start:end]
        print(f"  Match: {rule_id} -> '{span.text}' (start: {start}, end: {end})")
        
        # Debug the BASED_IN pattern processing
        if rule_id == "BASED_IN":
            print(f"    Debugging BASED_IN pattern:")
            print(f"    Pattern span: '{span.text}'")
            print(f"    Start: {start}, End: {end}")
            
            # Find location entity (after "in")
            location_token = None
            print(f"    Searching for location after position {end}"):
or i in range(end, len(doc)):
                print(f"      Checking token {i}: '{doc[i].text}' (ent_type: {doc[i].ent_type_})")
                if doc[i].ent_type_ in ["GPE", "LOC", "ORG"]:
                    location_token = doc[i]
                    print(f"      Found location token: '{location_token.text}'")
                    break
            
            # Find subject entity (before pattern)
            subject_token = None
            print(f"    Searching for subject before position {start}"):
or i in range(start - 1, -1, -1):
                print(f"      Checking token {i}: '{doc[i].text}' (ent_type: {doc[i].ent_type_})")
                if doc[i].ent_type_ in ["GPE", "LOC", "ORG", "PERSON", "FAC"]:
                    subject_token = doc[i]
                    print(f"      Found subject token: '{subject_token.text}'")
                    break
            
            # Additional search for BASED_IN pattern:
f location_token is None:
                print(f"    Additional search for location after 'in'"):
or i in range(end, len(doc)):
                    print(f"      Checking token {i}: '{doc[i].text}' (ent_type: {doc[i].ent_type_})")
                    if doc[i].ent_type_ in ["GPE", "LOC", "ORG"]:
                        location_token = doc[i]
                        print(f"      Found location token: '{location_token.text}'")
                        break
            
            print(f"    Final tokens - Subject: {subject_token}, Location: {location_token}")

if __name__ == "__main__":
    debug_based_in()