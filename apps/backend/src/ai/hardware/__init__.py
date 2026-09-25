# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from .ai_card_reference import AiCardReferenceConfig, AiCardReferenceModel
from .mvu_reference import (
    AxiLiteRegisterMap,
    MvuReferenceConfig,
    MvuReferenceModel,
    PeArray16x16,
    PlasticityEngine,
    Sram32KbDualPort,
    WavefrontController,
)
from .rtl_generator import (
    generate_mvu_header_projection,
    generate_mvu_header_projection_testbench,
)
from .standards_catalog import HardwareStandard, get_standard, search_standards

__all__ = [
    "AiCardReferenceConfig",
    "AiCardReferenceModel",
    "AxiLiteRegisterMap",
    "HardwareStandard",
    "MvuReferenceConfig",
    "MvuReferenceModel",
    "PeArray16x16",
    "PlasticityEngine",
    "generate_mvu_header_projection",
    "generate_mvu_header_projection_testbench",
    "get_standard",
    "search_standards",
    "Sram32KbDualPort",
    "WavefrontController",
]
