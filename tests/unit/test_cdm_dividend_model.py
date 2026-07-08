"""Smoke tests for core/cdm_dividend_model.py"""
from core.cdm_dividend_model import CDMCognitiveDividendModel


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

    def test_record_investment_method(self):
        instance = CDMCognitiveDividendModel()
        assert hasattr(instance, "record_investment")
