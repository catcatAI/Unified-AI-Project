"""
Tests for spaCy pattern matching to extract capital city relationships.
"""

import pytest
import spacy
from spacy.matcher import Matcher


@pytest.fixture(scope="module")
def nlp_en():
    """Load the spaCy English model once per module."""
    return spacy.load("en_core_web_sm")


def test_capital_of_pattern(nlp_en):
    """Tests the 'X is the capital of Y' pattern matching logic."""
    matcher = Matcher(nlp_en.vocab)
    
    # Pattern for "... is the capital of ..."
    capital_of_pattern = [
        {"LEMMA": "be"},
        {"LOWER": "the"},
        {"LOWER": "capital"},
        {"LOWER": "of"}
    ]
    matcher.add("CAPITAL_OF", [capital_of_pattern])
    
    text = "Paris is the capital of France."
    doc = nlp_en(text)
    
    matches = matcher(doc)
    
    assert len(matches) > 0, "Pattern 'CAPITAL_OF' should be found."

    found_relationship = False
    for match_id, start, end in matches:
        rule_id = nlp_en.vocab.strings[match_id]
        if rule_id == "CAPITAL_OF":
            # Find capital entity (GPE before the match)
            capital_entity = None
            for ent in reversed(doc.ents):
                if ent.label_ == "GPE" and ent.end <= start:
                    capital_entity = ent
                    break
            
            # Find country entity (GPE after the match)
            country_entity = None
            for ent in doc.ents:
                if ent.label_ == "GPE" and ent.start >= end:
                    country_entity = ent
                    break
            
            if capital_entity and country_entity:
                assert capital_entity.text == "Paris"
                assert country_entity.text == "France"
                found_relationship = True
                break
                
    assert found_relationship, "Could not correctly identify both capital and country entities."
