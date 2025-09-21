import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_person_title_pattern():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debugging PERSON_IS_TITLE_OF_ORG Pattern ===")
    
    # Check if the pattern is registered
    print("Matcher patterns:")
    if hasattr(analyzer, 'matcher') and analyzer.matcher is not None:
        try:
            stats = analyzer.matcher.get_stats()
            if "patterns" in stats:
                for pattern_id in stats["patterns"]:
                    if hasattr(analyzer.nlp, 'vocab'):
                        try:
                            rule_name = analyzer.nlp.vocab.strings[pattern_id]
                            print(f"  Pattern ID: {pattern_id}, Name: {rule_name}")
                        except Exception as e:
                            print(f"  Pattern ID: {pattern_id} (Error getting name: {e})")
            else:
                print("  No pattern stats available")
        except Exception as e:
            print(f"  Error getting matcher stats: {e}")
    else:
        print("  Matcher not initialized")
    
    # Test the specific pattern
    text = "Steve Jobs was a founder of Apple."
    print(f"\nTesting text: {text}")
    
    # Process with spaCy directly to see what entities are recognized
    if analyzer.nlp is not None:
        doc = analyzer.nlp(text)
        print(f"\nspaCy entities found:")
        for ent in doc.ents:
            print(f"  '{ent.text}' - {ent.label_} (start: {ent.start_char}, end: {ent.end_char})")
        
        print(f"\nToken analysis:")
        for i, token in enumerate(doc):
            print(f"  {i}: '{token.text}' - POS: {token.pos_}, LEMMA: {token.lemma_}, ENT_TYPE: {token.ent_type_}")
        
        # Test matcher
        matches = analyzer.matcher(doc) if hasattr(analyzer, 'matcher') and analyzer.matcher is not None else []
        print(f"\nMatcher matches found: {len(matches)}")
        for match_id, start, end in matches:
            if hasattr(analyzer.nlp, 'vocab'):
                try:
                    rule_id = analyzer.nlp.vocab.strings[match_id]
                    span = doc[start:end]
                    print(f"  Rule: {rule_id}, Span: '{span.text}', Start: {start}, End: {end}")
                except Exception as e:
                    print(f"  Match ID: {match_id}, Span: '{doc[start:end].text}', Start: {start}, End: {end} (Error getting rule name: {e})")
            else:
                print(f"  Match ID: {match_id}, Span: '{doc[start:end].text}', Start: {start}, End: {end}")
    
    # Now test the full analysis
    print(f"\n=== Full Analysis ===")
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Print entities
    print(f"Entities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"Relationships found: {len(kg_data['relationships'])}")
    for i, rel in enumerate(kg_data["relationships"]):
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")

if __name__ == "__main__":
    debug_person_title_pattern()