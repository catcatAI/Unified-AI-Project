def test_import():
    import core.bio.physiological_tactile


def test_classes_exist():
    from core.bio.physiological_tactile import (
        BodyPart,
        PhysiologicalTactileSystem,
        TactileResponse,
        TactileStimulus,
        TactileType,
    )
    assert TactileType.LIGHT_TOUCH is not None
    assert TactileType.PRESSURE is not None
    assert TactileType.TEMPERATURE is not None
    assert TactileType.VIBRATION is not None
    assert TactileType.PAIN is not None
    assert TactileType.ITCH is not None
    assert BodyPart.FACE is not None
    assert BodyPart.NECK is not None
    assert BodyPart.HANDS is not None
    assert BodyPart.FEET is not None


def test_tactile_system_has_expected_methods():
    from core.bio.physiological_tactile import PhysiologicalTactileSystem
    methods = [m for m in dir(PhysiologicalTactileSystem) if not m.startswith("_")]
    assert "initialize" in methods
    assert "process_stimulus" in methods
    assert "shutdown" in methods
