from ai.hardware.standards_catalog import get_standard, search_standards


def test_hardware_standards_catalog_contains_official_sources() -> None:
    result = search_standards()

    assert result["status"] == "ok"
    assert result["count"] == 5
    ids = {item["standard_id"] for item in result["standards"]}
    assert ids == {
        "pcie_base_5.0",
        "pcie_cem_5.0",
        "amba_axi_latest",
        "ieee_1800_2023",
        "pcie_12v_2x6_ecn",
    }
    assert all(item["source_url"].startswith("https://") for item in result["standards"])
    assert all(item["role"] == "environment_support" for item in [result])


def test_hardware_standards_catalog_filters_by_query() -> None:
    result = search_standards("AXI")

    assert result["query"] == "AXI"
    assert result["count"] == 1
    assert result["standards"][0]["standard_id"] == "amba_axi_latest"
    connector_result = search_standards("12V-2x6")
    assert connector_result["count"] == 1
    assert connector_result["standards"][0]["standard_id"] == "pcie_12v_2x6_ecn"
    assert get_standard("ieee_1800_2023")["status"] == "active standard"
    assert get_standard("missing") is None
