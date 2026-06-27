"""End-to-end tests for CLIP chicken pecking rice pipeline.

Tests the full flow: image → CLIP classify → dict lookup → Chinese response.
Uses real CLIP (not mocked).
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'apps', 'backend', 'src'))
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

import numpy as np
from ai.ed3n.ed3n_engine import ED3NEngine
from ai.multimodal.concept_library import ConceptLibrary
from ai.multimodal.semantic_key_mapper import SemanticKeyMapper
from ai.multimodal.semantic_visual import SemanticVisualEncoder
from ai.multimodal.vision_response_generator import VisionResponseGenerator
from PIL import Image, ImageDraw


@pytest.fixture(scope="module")
def encoder():
    enc = SemanticVisualEncoder()
    if not enc.is_available:
        pytest.skip("CLIP not available")
    return enc


@pytest.fixture(scope="module")
def ed3n():
    engine = ED3NEngine.get_shared()
    if len(engine.dictionary.entries) < 100:
        engine.load_external_dictionaries()
    return engine


@pytest.fixture(scope="module")
def library(encoder, ed3n):
    mapper = SemanticKeyMapper(max_entries=1000)
    lib = ConceptLibrary(
        semantic_encoder=encoder,
        dictionary=ed3n.dictionary,
        key_mapper=mapper,
    )
    lib.build()
    return lib


@pytest.fixture(scope="module")
def generator(ed3n):
    gen = VisionResponseGenerator(dictionary=ed3n.dictionary)
    return gen


def make_img(draw_func):
    img = Image.new('RGB', (224, 224), (240, 240, 240))
    d = ImageDraw.Draw(img)
    draw_func(d)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def draw_chicken(d):
    d.ellipse([50, 90, 150, 190], fill=(255, 200, 50))
    d.ellipse([100, 50, 140, 90], fill=(255, 200, 50))
    d.polygon([(140, 65), (160, 72), (140, 80)], fill=(255, 140, 0))
    d.ellipse([115, 60, 125, 70], fill=(0, 0, 0))
    d.polygon([(110, 50), (115, 35), (120, 50)], fill=(255, 0, 0))


def draw_cat(d):
    d.ellipse([60, 60, 160, 160], fill=(200, 150, 100))
    d.polygon([(70, 60), (50, 20), (90, 60)], fill=(200, 150, 100))
    d.polygon([(130, 60), (150, 20), (110, 60)], fill=(200, 150, 100))
    d.ellipse([90, 85, 100, 95], fill=(100, 200, 100))
    d.ellipse([120, 85, 130, 95], fill=(100, 200, 100))


def draw_dog(d):
    d.ellipse([60, 60, 160, 160], fill=(160, 100, 50))
    d.polygon([(60, 60), (30, 20), (80, 50)], fill=(140, 80, 40))
    d.polygon([(140, 60), (170, 20), (120, 50)], fill=(140, 80, 40))
    d.ellipse([90, 90, 105, 100], fill=(50, 50, 50))
    d.ellipse([115, 90, 130, 100], fill=(50, 50, 50))


class TestConceptLibraryBuild:
    def test_builds_with_concepts(self, library):
        assert len(library._concepts) >= 4

    def test_concepts_have_embeddings(self, library):
        for name, info in library._concepts.items():
            assert info["text_embedding"] is not None
            assert info["text_embedding"].shape == (512,)

    def test_concepts_registered_in_dictionary(self, ed3n):
        for key in ["concept_chicken", "concept_cat", "concept_dog", "concept_bird"]:
            assert key in ed3n.dictionary.entries


class TestCLIPClassification:
    def test_chicken_classified(self, library):
        img_data = make_img(draw_chicken)
        results = library.classify(img_data, top_k=1)
        assert len(results) >= 1
        assert results[0]["concept_name"] == "chicken"
        assert results[0]["confidence"] > 0.15

    def test_dog_classified(self, library):
        img_data = make_img(draw_dog)
        results = library.classify(img_data, top_k=1)
        assert len(results) >= 1
        assert results[0]["concept_name"] in ["dog", "rabbit", "cat"]
        assert results[0]["confidence"] > 0.15

    def test_cat_classified(self, library):
        img_data = make_img(draw_cat)
        results = library.classify(img_data, top_k=1)
        assert len(results) >= 1
        assert results[0]["concept_name"] in ["cat", "chicken", "rabbit"]
        assert results[0]["confidence"] > 0.10


class TestResponseGeneration:
    def test_chicken_response_chinese(self, library, generator):
        for cname, info in library._concepts.items():
            generator.register_concept(cname, info["dict_key"], info["labels"])
        img_data = make_img(draw_chicken)
        results = library.classify(img_data, top_k=1)
        response = generator.generate_response(results, language="zh", action="在吃米")
        assert "鸡" in response
        assert "在吃米" in response

    def test_dog_response_chinese(self, library, generator):
        for cname, info in library._concepts.items():
            generator.register_concept(cname, info["dict_key"], info["labels"])
        img_data = make_img(draw_dog)
        results = library.classify(img_data, top_k=1)
        response = generator.generate_response(results, language="zh", action="在跑")
        assert any(zh in response for zh in ["狗", "兔", "猫"])
        assert "在跑" in response


class TestFullPipeline:
    def test_pipeline_returns_string(self, library, generator):
        for cname, info in library._concepts.items():
            generator.register_concept(cname, info["dict_key"], info["labels"])
        img_data = make_img(draw_chicken)
        results = library.classify(img_data, top_k=1)
        assert len(results) >= 1
        response = generator.generate_response(results, language="zh")
        assert isinstance(response, str)
        assert len(response) > 0
