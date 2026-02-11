#!/usr/bin/env python3
"""
Cognitive-Economy Bridge
Bridges the CDM (Cognitive Dividend Model) and the Economy System.
Treats AGI cognitive output as a form of labor/value generation.
"""

import logging
from typing import Dict, Any, Optional
from .cdm_dividend_model import CDMCognitiveDividendModel, LifeSenseOutput
from economy.economy_manager import EconomyManager

logger = logging.getLogger(__name__)

class CognitiveEconomyBridge:
    """
    Bridges AI cognitive efforts to the economic system.
    Listens for 'Life Sense' output from CDM and rewards the user/system.
    """
    
    def __init__(self, cdm: CDMCognitiveDividendModel, economy: EconomyManager, user_id: str = "default_user"):
        self.cdm = cdm
        self.economy = economy
        self.user_id = user_id
        
        # Register callback with CDM
        self.cdm.register_output_callback(self._on_life_sense_generated)
        logger.info(f"CognitiveEconomyBridge initialized for user: {self.user_id}")
        
    def _on_life_sense_generated(self, output: LifeSenseOutput):
        """Callback triggered whenever Angela generates Life Sense output."""
        try:
            # Award coins via EconomyManager
            dividend = self.economy.process_cognitive_dividend(
                user_id=self.user_id,
                life_sense_amount=output.output_amount,
                quality_score=output.quality_score
            )
            
            if dividend > 0:
                logger.info(f"[Bridge] Converted {output.output_amount:.2f} Life Sense ({output.life_sense_type}) to {dividend:.2f} Coins")
        except Exception as e:
            logger.error(f"Bridge failed to process dividend: {e}")

def initialize_cognitive_bridge(cdm: CDMCognitiveDividendModel, economy: EconomyManager) -> CognitiveEconomyBridge:
    """Helper to create and link the bridge."""
    return CognitiveEconomyBridge(cdm, economy)
