"""Tests for ai.response.learning_loop"""
import pytest


class TestFragmentExtractor:
    def test_import(self):
        from ai.response.learning_loop import FragmentExtractor, LearningLoop

        assert FragmentExtractor is not None
        assert LearningLoop is not None

    def test_extract_sentences(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        text = "今天天气真好。我们去散步吧！你开心吗？"
        sentences = extractor.extract_sentences(text)
        assert len(sentences) >= 2
        assert "今天天气真好" in sentences[0]
        assert all(len(s) > 2 for s in sentences)

    def test_extract_sentences_short_omitted(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        text = "好。行。可以的。今天天气真好。"
        sentences = extractor.extract_sentences(text)
        assert all(len(s) > 2 for s in sentences)
        assert "好" not in sentences
        assert "行" not in sentences

    def test_extract_emoji(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        text = "今天好开心 😊 哇哈哈 ≧∇≦"
        emoji = extractor.extract_emoji(text)
        assert len(emoji) > 0
        assert any("😊" in e or "≧∇≦" in e for e in emoji)

    def test_extract_emoji_no_matches(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        text = "今天天气真好没有表情"
        emoji = extractor.extract_emoji(text)
        assert emoji == []

    def test_extract_collocations_quoted(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        text = "我最喜欢「人工智能」和「深度学习」"
        phrases = extractor.extract_collocations(text)
        assert "人工智能" in phrases
        assert "深度学习" in phrases

    def test_extract_collocations_double_quoted(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        text = '他说"机器学习"很重要'
        phrases = extractor.extract_collocations(text)
        assert "机器学习" in phrases

    def test_is_novel(self):
        from ai.response.learning_loop import FragmentExtractor

        extractor = FragmentExtractor()
        assert extractor.is_novel("hello") is True
        assert extractor.is_novel("hello") is False
        assert extractor.is_novel("world") is True


class TestLearningLoop:
    def test_instantiation(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        assert loop.extraction_count == 0
        assert loop.learning_rate == 0.05

    def test_process_llm_response_empty(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        count = loop.process_llm_response("")
        assert count == 0

    def test_process_llm_response_with_text(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        count = loop.process_llm_response("今天很开心 😊 我们一起「学习」吧")
        assert count > 0

    def test_process_llm_response_dedup(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        loop.process_llm_response("你好世界")
        count2 = loop.process_llm_response("你好世界")
        assert count2 == 0

    def test_record_user_engagement_positive(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        loop.record_user_engagement(positive=True)
        assert loop.learning_rate == pytest.approx(0.06, rel=1e-3)

    def test_record_user_engagement_negative(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        loop.record_user_engagement(positive=False)
        assert loop.learning_rate == pytest.approx(0.045, rel=1e-3)

    def test_bind_vocabulary(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        mock_vocab = object()
        loop.bind_vocabulary(mock_vocab)
        assert loop._neuro_vocabulary is mock_vocab

    def test_get_learning_loop_singleton(self):
        from ai.response.learning_loop import get_learning_loop

        loop1 = get_learning_loop()
        loop2 = get_learning_loop()
        assert loop1 is loop2

    def test_extraction_count_accumulates(self):
        from ai.response.learning_loop import LearningLoop

        loop = LearningLoop()
        c1 = loop.process_llm_response("今天很开心 😊")
        c2 = loop.process_llm_response("我们一起去「散步」吧")
        assert loop.extraction_count == c1 + c2
