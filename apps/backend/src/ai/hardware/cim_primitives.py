# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Verified layout primitives for sky130 CIM cells.

Everything here is a building block whose extracted behaviour was checked by
DRC and SPICE. This module does not try to design a whole array, a whole
group, or a whole sense chain: those attempts existed and were removed
because they were laid out before the cell spec (2T select+weight) was
understood and before the routing could be verified end to end.

What is kept
------------
* ``nmos`` / ``pfet``: one verified diffusion patch per device. A pfet
  needs an ``nwell`` island and an ``mcon`` cut under every diffusion
  contact. Without those the device either does not extract at all or its
  drain is not a node.
* ``inverter``: one shared poly gate and one joined metal1 output.
  Verified to extract as one nfet + one pfet with W=0.42/0.84 and L=0.15.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# DOT4L-derived cell geometry, in 0.01 um units.
#
# The nmos tile's x extent is the gate length L and its y extent is the device
# width W, because the word line runs along x and the fingers stack along y.
# DOT4L draws "rect 713 724 728 766": x = 15 units = 0.15 um = L, y = 42
# units = 0.42 um = W.
GATE_L = 15
DEV_W = 42
NDIFF_W = 150
CONTACT = 17
CONTACT_INSET_Y = 12
BUS_W = 17
LI_EXT = 8
M1_EXT = 7
LI_TIE_H = 33
NWELL_LEFT = 70
POLY_EXT_Y = 200
OUT_JOIN_Y = 53

LAYERS = (
    "nwell",
    "locali",
    "ndiff",
    "nmos",
    "ndiffc",
    "pdiff",
    "pmos",
    "pdc",
    "nsc",
    "nsubdiff",
    "poly",
    "polycont",
    "mcon",
    "metal1",
)


class Canvas:
    """Accumulate rectangles per layer, then emit a magic cell."""

    def __init__(self) -> None:
        self.layers: Dict[str, List[str]] = {name: [] for name in LAYERS}

    def rect(self, layer: str, x1: int, y1: int, x2: int, y2: int) -> None:
        if x2 > x1 and y2 > y1:
            self.layers[layer].append(f"rect {x1} {y1} {x2} {y2}")

    def nmos(self, x: int, y: int, gate_l: int = GATE_L, dev_w: int = DEV_W) -> None:
        """Place a verified 1T nfet with contacts on both sides."""
        self.rect("ndiff", x, y, x + NDIFF_W, y + dev_w)
        gate_x = x + (NDIFF_W - gate_l) // 2
        self.rect("nmos", gate_x, y, gate_x + gate_l, y + dev_w)
        self.rect("poly", gate_x, y - POLY_EXT_Y, gate_x + gate_l, y + dev_w + POLY_EXT_Y)
        for cx in (x + 10, x + NDIFF_W - CONTACT - 10):
            cy = y + CONTACT_INSET_Y
            self.rect("ndiffc", cx, cy, cx + CONTACT, cy + CONTACT)
            self.rect(
                "locali",
                cx - LI_EXT,
                cy - LI_EXT,
                cx + CONTACT + LI_EXT,
                cy + CONTACT + LI_EXT,
            )
            self.rect("mcon", cx, cy, cx + CONTACT, cy + CONTACT)
            self.rect(
                "metal1",
                cx - M1_EXT,
                cy - M1_EXT,
                cx + CONTACT + M1_EXT,
                cy + CONTACT + M1_EXT,
            )

    def pfet(
        self,
        x: int,
        y: int,
        gate_l: int = GATE_L,
        dev_w: int = DEV_W,
        island_left: int = 400,
    ) -> None:
        """Place a verified pfet inside its own n-well island."""
        island_x = 400
        island_y = 120
        self.rect(
            "nwell", x - island_left, y - island_y, x + NDIFF_W + island_x, y + dev_w + island_y
        )
        self.rect("pdiff", x, y, x + NDIFF_W, y + dev_w)
        gate_x = x + (NDIFF_W - gate_l) // 2
        self.rect("pmos", gate_x, y, gate_x + gate_l, y + dev_w)
        self.rect("poly", gate_x, y - 200, gate_x + gate_l, y + dev_w + 200)
        for cx in (x + 10, x + NDIFF_W - CONTACT - 10):
            cy = y + CONTACT_INSET_Y
            self.rect("pdc", cx, cy, cx + CONTACT, cy + CONTACT)
            self.rect(
                "locali",
                cx - LI_EXT,
                cy - LI_EXT,
                cx + CONTACT + LI_EXT,
                cy + CONTACT + LI_EXT,
            )
            self.rect("mcon", cx, cy, cx + CONTACT, cy + CONTACT)
            self.rect(
                "metal1",
                cx - M1_EXT,
                cy - M1_EXT,
                cx + CONTACT + M1_EXT,
                cy + CONTACT + M1_EXT,
            )
        tap_x = x + NDIFF_W + 200
        self.rect("nsubdiff", tap_x, y, tap_x + 150, y + dev_w)
        self.rect(
            "nsc",
            tap_x + 40,
            y + CONTACT_INSET_Y,
            tap_x + 40 + CONTACT,
            y + CONTACT_INSET_Y + CONTACT,
        )
        self.rect(
            "locali",
            tap_x + 40 - LI_EXT,
            y + CONTACT_INSET_Y - LI_EXT,
            tap_x + 40 + CONTACT + LI_EXT,
            y + CONTACT_INSET_Y + CONTACT + LI_EXT,
        )

    def inverter(
        self,
        x: int,
        y: int,
        nfet_w: int = DEV_W,
        pfet_w: int = 84,
    ) -> Dict[str, int]:
        """Place a verified CMOS inverter: one shared gate, one joined output."""
        self.nmos(x, y, GATE_L, nfet_w)
        self.pfet(x + 260, y, GATE_L, pfet_w, island_left=NWELL_LEFT)
        gate_x = x + (NDIFF_W - GATE_L) // 2
        pfet_gate_x = x + 260 + (NDIFF_W - GATE_L) // 2
        tie_y = y - 100
        for gx, gw in ((gate_x, nfet_w), (pfet_gate_x, pfet_w)):
            self.rect("poly", gx, y - 200, gx + GATE_L, y + gw + 200)
            pcx = gx - 1
            self.rect(
                "poly",
                pcx - LI_EXT,
                tie_y - LI_EXT,
                pcx + CONTACT + LI_EXT,
                tie_y + CONTACT + LI_EXT,
            )
            self.rect("polycont", pcx, tie_y, pcx + CONTACT, tie_y + CONTACT)
            self.rect("mcon", pcx, tie_y, pcx + CONTACT, tie_y + CONTACT)
            self.rect(
                "metal1",
                pcx - LI_EXT,
                tie_y - LI_EXT,
                pcx + CONTACT + LI_EXT,
                tie_y + CONTACT + LI_EXT,
            )
        self.rect(
            "locali",
            gate_x - 1 - LI_EXT,
            tie_y - LI_EXT,
            pfet_gate_x - 1 + CONTACT + LI_EXT,
            tie_y + CONTACT + LI_EXT,
        )
        out_x = x + NDIFF_W - CONTACT - 10
        pfet_out_x = x + 260 + NDIFF_W - CONTACT - 10
        self.rect("metal1", out_x, y - 30, out_x + BUS_W, y + nfet_w + 60)
        self.rect("metal1", pfet_out_x, y - 30, pfet_out_x + BUS_W, y + pfet_w + 60)
        self.rect("metal1", out_x, y + OUT_JOIN_Y, pfet_out_x + BUS_W, y + OUT_JOIN_Y + BUS_W)
        return {
            "in_x": gate_x,
            "in_y": y - 200,
            "out_x": out_x,
            "out_y": y,
            "height": max(nfet_w, pfet_w),
            "span": 260 + NDIFF_W + 400,
        }

    def to_mag(self) -> str:
        body = "\n".join("\n".join([f"<< {name} >>", *self.layers[name]]) for name in LAYERS)
        return f"magic\ntech sky130A\n{body}\n<< end >>\n"


__all__ = [
    "DEV_W",
    "GATE_L",
    "Canvas",
]
