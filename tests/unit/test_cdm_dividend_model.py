"""Smoke tests for core/cdm_dividend_model.py"""
from core.cdm_dividend_model import CDMCognitiveDividendModel, CognitiveActivity


class TestCDMCognitiveDividendModel:
    """Basic smoke tests for CDMCognitiveDividendModel"""

    def test_import(self):
        assert CDMCognitiveDividendModel is not None

    def test_instantiation(self):
        instance = CDMCognitiveDividendModel()
        assert instance is not None

    def test_instantiation_with_config(self):
        instance = CDMCognitiveDividendModel(config={"base_conversion_rate": 0.8})
        assert instance is not None
        assert instance.base_conversion_rate == 0.8

    def test_record_investment_and_summary(self):
        instance = CDMCognitiveDividendModel()
        inv = instance.record_investment(
            activity_type=CognitiveActivity.REFLECTING,
            duration_seconds=60.0,
            intensity=0.5,
        )
        assert inv is not None
        summary = instance.get_dividend_summary()
        assert isinstance(summary, dict)
        assert summary["investment_count"] > 0

    def test_calculate_life_sense_output(self):
        instance = CDMCognitiveDividendModel()
        inv = instance.record_investment(
            activity_type=CognitiveActivity.REFLECTING,
            duration_seconds=30.0,
            intensity=0.8,
        )
        output = instance.calculate_life_sense_output(investment=inv)
        assert output is not None
