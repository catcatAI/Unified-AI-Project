# -*- coding: utf-8 -*-
"""
Tests for MSBA LinguisticBlock.
"""

import pytest
from ai.msba.linguistic_block import LinguisticBlock


class TestLinguisticBlock:
    def test_creation_rule_based(self):
        block = LinguisticBlock(use_spacy=False)
        assert block._nlp is None
        assert len(block.hit_sources) > 0

    def test_rule_activations_question(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("What is MSBA?")
        assert result["discourse_question"] > 0.0

    def test_rule_activations_exclamation(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("This is great!")
        assert result["discourse_exclamation"] > 0.0

    def test_rule_activations_future(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("I will go tomorrow")
        assert result["tense_future"] > 0.0

    def test_rule_activations_modal(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("You should do this")
        assert result["modality_modal"] > 0.0

    def test_rule_activations_progressive(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("I am running")
        assert result["aspect_progressive"] > 0.0

    def test_rule_activations_past(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("I went home")
        assert result["tense_past"] > 0.0

    def test_rule_activations_empty(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("")
        assert all(v == 0.0 for v in result.values())

    def test_spacy_fallback(self):
        # spaCy not available, should fallback to rule-based
        block = LinguisticBlock(use_spacy=True)
        # Should still work via fallback
        result = block.get_hit_activations("What is this?")
        assert "discourse_question" in result

    def test_all_hit_sources_have_values(self):
        block = LinguisticBlock(use_spacy=False)
        result = block.get_hit_activations("test input")
        for hs in block.hit_sources:
            assert hs.source_id in result
