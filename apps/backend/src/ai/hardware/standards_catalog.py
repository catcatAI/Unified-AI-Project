# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class HardwareStandard:
    standard_id: str
    name: str
    authority: str
    version: str
    scope: str
    status: str
    source_url: str
    access: str
    normative: bool
    verified_facts: Tuple[str, ...]
    derived_notes: Tuple[str, ...]
    tags: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_STANDARDS: Tuple[HardwareStandard, ...] = (
    HardwareStandard(
        standard_id="pcie_base_5.0",
        name="PCI Express Base Specification",
        authority="PCI-SIG",
        version="5.0",
        scope="PCIe protocol, link, configuration, and device behavior",
        status="official specification",
        source_url="https://pcisig.com/PCIExpress/Specs/Base/_5.0_1.0",
        access="public specification landing page; normative download may require membership",
        normative=True,
        verified_facts=(
            "PCI-SIG identifies PCIe 5.0 as 32.0 GT/s per lane.",
            "The base specification governs PCIe architecture and programming interface.",
        ),
        derived_notes=(
            "For x16, 32 GT/s per lane gives 512 Gbps raw signaling per direction before encoding.",
            "128b/130b payload calculations must be labeled separately from raw signaling.",
        ),
        tags=("pcie", "gen5", "x16", "host-link", "dma"),
    ),
    HardwareStandard(
        standard_id="pcie_cem_5.0",
        name="PCI Express Card Electromechanical Specification",
        authority="PCI-SIG",
        version="5.0",
        scope="Card mechanical, electrical, connector, and system-board implementation",
        status="official specification",
        source_url="https://pcisig.com/PCIExpress/Specs/CEM/CardElectromechanical_5.0",
        access="public specification landing page; normative download may require membership",
        normative=True,
        verified_facts=(
            "CEM 5.0 is the electromechanical companion to the PCIe Base 5.0 specification.",
            "CEM covers implementation constraints that the base protocol specification does not replace.",
        ),
        derived_notes=(
            "A PCIe link budget is not a card power, connector, routing, or signal-integrity sign-off.",
        ),
        tags=("pcie", "cem", "mechanical", "electrical", "connector", "power-integrity"),
    ),
    HardwareStandard(
        standard_id="amba_axi_latest",
        name="AMBA AXI and ACE Protocol Specification",
        authority="Arm",
        version="latest",
        scope="AXI4, AXI4-Lite, AXI4-Stream, and related AMBA interfaces",
        status="official current specification index",
        source_url="https://developer.arm.com/documentation/ihi0022/l/?lang=en",
        access="public specification index; PDF access may require an Arm account",
        normative=True,
        verified_facts=(
            "AXI4-Lite is a simplified control-register-style interface for peripheral communication.",
            "AXI data width is a bus contract and does not by itself define memory capacity.",
            "The specification defines address, data, response, and ordering channels and their handshake rules.",
        ),
        derived_notes=(
            "An AXI address map must state address width, data width, byte lanes, alignment, and response behavior.",
            "AXI protocol compliance does not prove a memory controller or card power design is compliant.",
        ),
        tags=("axi", "axi4-lite", "amba", "csr", "bus", "handshake"),
    ),
    HardwareStandard(
        standard_id="ieee_1800_2023",
        name="IEEE SystemVerilog Unified Hardware Design, Specification, and Verification Language",
        authority="IEEE",
        version="1800-2023",
        scope="Behavioral, RTL, gate-level modeling, testbenches, assertions, coverage, and verification",
        status="active standard",
        source_url="https://standards.ieee.org/ieee/1800/7743/",
        access="public standard metadata; full text access may require IEEE credentials",
        normative=True,
        verified_facts=(
            "IEEE 1800-2023 defines SystemVerilog syntax and semantics for hardware design and verification.",
            "The standard covers behavioral, RTL, gate-level, testbench, assertion, and coverage workflows.",
        ),
        derived_notes=(
            "A SystemVerilog testbench result is verification evidence, not physical silicon or timing sign-off.",
        ),
        tags=("systemverilog", "hdl", "rtl", "testbench", "assertion", "coverage", "verification"),
    ),
    HardwareStandard(
        standard_id="pcie_12v_2x6_ecn",
        name="12V-2x6 Connector Updates to PCIe Base 6.0",
        authority="PCI-SIG",
        version="ECN 2023-08-31",
        scope="PCIe connector type encoding and maximum/sustained power measurement",
        status="official ECN",
        source_url="https://pcisig.com/PCI%20Express/ECN/Base/12V-2x6ConnectorUpdatestoPCIeBase_6.0",
        access="public ECN landing page; normative download may require membership",
        normative=True,
        verified_facts=(
            "The ECN defines connector type encodings for the 12V-2x6 connector.",
            "The ECN states that 12V-2x6 is defined in CEM 5.1 and replaces 12VHPWR.",
            "The ECN updates maximum and sustained power measurement methodology to align with form-factor specifications.",
        ),
        derived_notes=(
            "A power-connector choice must be checked against the applicable CEM revision and ECN, not only a Base specification link budget.",
        ),
        tags=("pcie", "12v-2x6", "12vhpwr", "connector", "power", "thermal", "cem"),
    ),
)


def search_standards(query: Optional[str] = None) -> Dict[str, Any]:
    normalized = (query or "").strip().casefold()
    if not normalized:
        selected = list(_STANDARDS)
    else:
        query_terms = re.findall(r"[a-z0-9]+", normalized)
        selected = []
        for standard in _STANDARDS:
            searchable = " ".join(
                (
                    standard.standard_id,
                    standard.name,
                    standard.authority,
                    standard.version,
                    standard.scope,
                    " ".join(standard.tags),
                    " ".join(standard.verified_facts),
                    " ".join(standard.derived_notes),
                )
            ).casefold()
            if query_terms:
                matches = all(
                    re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", searchable)
                    for term in query_terms
                )
            else:
                matches = normalized in searchable
            if matches:
                selected.append(standard)
    return {
        "status": "ok",
        "catalog_version": 2,
        "role": "environment_support",
        "query": query or "",
        "count": len(selected),
        "standards": [standard.to_dict() for standard in selected],
        "research_guidance": [
            "Start from the normative or official standard source.",
            "Record specification version, revision date, and access restrictions.",
            "Separate protocol facts, derived arithmetic, and project design choices.",
            "Do not treat a standards reference as architecture selection or physical sign-off.",
        ],
    }


def get_standard(standard_id: str) -> Optional[Dict[str, Any]]:
    for standard in _STANDARDS:
        if standard.standard_id == standard_id:
            return standard.to_dict()
    return None


__all__ = ["HardwareStandard", "get_standard", "search_standards"]
