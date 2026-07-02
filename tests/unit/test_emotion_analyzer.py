"""Tests for services.llm.emotion_analyzer"""


class TestEmotionAnalyzer:
    def test_import(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        assert EmotionAnalyzer is not None

    def test_default_config_initializes_keywords(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        assert "happy" in analyzer.emotion_keywords
        assert "sad" in analyzer.emotion_keywords
        assert "angry" in analyzer.emotion_keywords
        assert "fear" in analyzer.emotion_keywords
        assert "surprise" in analyzer.emotion_keywords

    def test_analyze_happy_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("我今天好开心！哈哈")
        assert result["emotion"] == "happy"
        assert result["confidence"] > 0.5

    def test_analyze_sad_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("我好难过，想哭")
        assert result["emotion"] == "sad"
        assert result["confidence"] > 0.5

    def test_analyze_angry_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("气死我了！真讨厌")
        assert result["emotion"] == "angry"

    def test_analyze_surprise_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("哇！真的吗？太意外了")
        assert result["emotion"] in ("surprise", "happy")

    def test_analyze_neutral_text_returns_calm(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("今天天气不错，适合散步。")
        assert result["emotion"] == "calm"
        assert result["confidence"] == 0.5

    def test_analyze_empty_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("")
        assert result["emotion"] == "calm"
        assert result["intensity"] == 0.3

    def test_analyze_response_emotion(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_response_emotion("我好开心啊 😊")
        assert result["emotion"] == "happy"

    def test_custom_config(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer(config={"custom_key": "value"})
        assert analyzer.config["custom_key"] == "value"

    def test_analyze_fear_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("我好害怕，很紧张")
        assert result["emotion"] == "fear"

    def test_analyze_curious_text(self):
        from services.llm.emotion_analyzer import EmotionAnalyzer

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_emotion("我很好奇，为什么天是蓝色的？")
        assert result["emotion"] == "curious"
