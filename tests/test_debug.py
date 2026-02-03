"""
测试模块 - test_debug

自动生成的测试模块,用于验证系统功能。
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test code directly
code = '''
import spacy
from spacy.matcher import Matcher

# Load model
nlp = spacy.load("en_core_web_sm")
print("Loaded spaCy model")

# Create matcher
matcher = Matcher(nlp.vocab)

# Add pattern for "X is based in Y":
ased_in_pattern = [
    {"LEMMA": "be"},
    {"LOWER": "based"},
    {"LOWER": "in"}
]
matcher.add("BASED_IN", [based_in_pattern])

# Test text
text = "Microsoft is based in Redmond."
doc = nlp(text)

# Find matches
matches = matcher(doc)
print(f"Found {len(matches)} matches")

for match_id, start, end in matches:
    rule_id = nlp.vocab.strings[match_id]
    span = doc[start:end]
    print(f"Match: {rule_id} -> '{span.text}' [{start}:{end}]")

# Print entities
print("\\nEntities:")
for ent in doc.ents:
    print(f"  {ent.text} ({ent.label_}) [{ent.start}:{ent.end}]")

# Print tokens
print("\\nTokens:")
for i, token in enumerate(doc):
    print(f"  {i}: '{token.text}' (POS: {token.pos_}, LEMMA: {token.lemma_}, ENT_TYPE: {token.ent_type_})")
# exec(code)