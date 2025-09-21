import spacy
import networkx as nx
from spacy.matcher import Matcher
import uuid

def test_capital_of_pattern():
    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")
    
    # Create matcher
    matcher = Matcher(nlp.vocab)
    
    # Add pattern for "X is the capital of Y"
    capital_of_pattern = [
        {"LEMMA": "be"},
        {"LOWER": "the"},
        {"LOWER": "capital"},
        {"LOWER": "of"}
    ]
    matcher.add("CAPITAL_OF", [capital_of_pattern])
    
    # Test text
    text = "Paris is the capital of France."
    doc = nlp(text)
    
    print(f"Processing text: {text}")
    
    # Extract entities
    entities = {}
    for ent in doc.ents:
        print(f"Found entity: {ent.text} ({ent.label_})")
        entities[ent.text] = ent
    
    # Apply matcher
    matches = matcher(doc)
    print(f"Found {len(matches)} matches")
    
    for match_id, start, end in matches:
        rule_id = nlp.vocab.strings[match_id]
        span = doc[start:end]
        print(f"Match: {rule_id} -> '{span.text}' (start: {start}, end: {end})")
        
        if rule_id == "CAPITAL_OF":
            # Find capital entity (before "is")
            capital_entity = None
            for ent in reversed([e for e in doc.ents if e.label_ == "GPE" and e.end <= start]):
                capital_entity = ent
                print(f"Found capital entity: '{ent.text}' at position {ent.start}")
                break
            
            # Find country entity (after "of")
            country_entity = None
            for ent in doc.ents:
                if ent.label_ == "GPE" and ent.start >= end:
                    country_entity = ent
                    print(f"Found country entity: '{ent.text}' at position {ent.start}")
                    break
            
            if capital_entity and country_entity:
                print(f"✓ Successfully identified relationship: {country_entity.text} has capital {capital_entity.text}")
            else:
                print("✗ Could not identify both entities")
    
    print("\nToken analysis:")
    for i, token in enumerate(doc):
        print(f"  {i}: '{token.text}' (lemma: '{token.lemma_}', pos: {token.pos_}, ent_type: {token.ent_type_})")

if __name__ == "__main__":
    test_capital_of_pattern()