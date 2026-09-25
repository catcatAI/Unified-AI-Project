from ai.core.eda_episode import build_eda_episode, evaluate_eda_result


def _artifact(digest: str) -> dict:
    return {
        "type": "gerber",
        "path": "/absolute/should-not-leak.gbr",
        "relative_path": "output/should-not-leak.gbr",
        "sha256": digest,
        "bytes": 12,
    }


def test_pcb_episode_is_sanitized_and_eligible() -> None:
    episode = build_eda_episode(
        workflow="pcb",
        parameters={
            "width_mm": 40.0,
            "height_mm": 30.0,
            "account": "must-not-leak",
            "source_path": "/tmp/design.kicad_pcb",
        },
        tools={"kicad": {"version": "10.0.6", "mode": "cli"}},
        results={
            "kicad": {
                "status": "success",
                "metrics": {
                    "drc_parsed": True,
                    "violation_count": 0,
                    "unconnected_count": 0,
                    "gerber_count": 4,
                    "component_count": 2,
                    "track_count": 2,
                    "template_only": False,
                },
            },
            "easyeda": {"status": "ready_for_client"},
            "jlcone": {"status": "ready_for_client"},
        },
        artifacts=[_artifact("a" * 64)],
    )

    assert episode["schema_version"] == "eda-episode/1"
    assert episode["outcome"]["eligible"] is True
    assert episode["outcome"]["quality"] == 1.0
    assert episode["parameters"] == {"width_mm": 40.0, "height_mm": 30.0}
    assert episode["artifacts"] == [{"type": "gerber", "sha256": "a" * 64, "bytes": 12}]
    assert episode["governance"]["order_placement"] is False
    assert "account" not in episode["parameters"]
    assert "should-not-leak" not in str(episode)


def test_pcb_template_is_not_treated_as_engineering_evidence() -> None:
    verdict = evaluate_eda_result(
        "pcb",
        {
            "kicad": {
                "status": "success",
                "metrics": {
                    "drc_parsed": True,
                    "violation_count": 0,
                    "unconnected_count": 0,
                    "gerber_count": 4,
                    "component_count": 0,
                    "track_count": 0,
                    "template_only": True,
                },
            }
        },
    )

    assert verdict["eligible"] is False
    assert "pcb_template_only" in verdict["reasons"]


def test_pcb_episode_quarantines_drc_failure() -> None:
    verdict = evaluate_eda_result(
        "pcb",
        {
            "kicad": {
                "status": "success",
                "metrics": {
                    "drc_parsed": True,
                    "violation_count": 2,
                    "unconnected_count": 0,
                    "gerber_count": 4,
                },
            }
        },
    )

    assert verdict["eligible"] is False
    assert "kicad_has_violations" in verdict["reasons"]


def test_ai_card_reference_episode_is_eligible_for_replay() -> None:
    from ai.hardware.ai_card_reference import AiCardReferenceModel

    verdict = evaluate_eda_result(
        "ai_card_reference",
        {"ai_card_reference": AiCardReferenceModel().run()},
    )

    assert verdict["eligible"] is True
    assert verdict["quality"] == 1.0
    assert verdict["deferred"] == ["cost_verified"]


def test_rtl_projection_episode_is_replayable_but_defers_simulation() -> None:
    verdict = evaluate_eda_result(
        "rtl",
        {
            "rtl": {
                "status": "generated_structural_projection",
                "validation_level": "L1",
                "professional_hdl_simulation": False,
                "physical_hardware": False,
                "architecture_frozen": False,
                "header_recalculation": {
                    "scope": "one_configured_mvu_sram_instance",
                    "checks_pass": True,
                },
                "rtl_artifact": {"type": "systemverilog"},
                "testbench_artifact": {"type": "systemverilog"},
            }
        },
    )

    assert verdict["eligible"] is True
    assert verdict["deferred"] == [
        "hdl_simulation",
        "synthesis",
        "architecture_freeze",
        "physical_hardware",
    ]


def test_coordinator_domain_does_not_own_eda_episode() -> None:
    import asyncio

    from ai.core.training_coordinator import TrainingCoordinator

    async def run() -> None:
        coordinator = TrainingCoordinator()
        assert await coordinator.assign_domain("eda_episode") is None
        await coordinator.record_training(
            "eda_episode", "ed3n", 1, 1.0, [{"input": "must-not-enter"}]
        )
        assert "eda_episode" not in coordinator._domain_map

    asyncio.run(run())
