# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Where the external tools and models the CIM layout work needs live.

One place, so tests can skip cleanly when magic, ngspice or the flattened sky130
model library is absent rather than failing on an import.

It is also the one place that resolves the overrides ``.env.example``
documents, so a knob that is written down is actually read: a documented setting
nothing consumes is worse than no setting at all, because it makes an operator
believe the tooling honours a path it ignores.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

MAGIC = shutil.which("magic")
NGSPICE = shutil.which("ngspice")

# Built by the flattener from the volare PDK. Overridable so
# a CI machine can point at its own copy.
MODEL_LIBRARY = Path(
    os.environ.get(
        "ANGELA_SKY130_FLAT_SPICE",
        os.path.join(tempfile.gettempdir(), "opencode", "sensemod", "mixed_sky130.spice"),
    )
)

MAGIC_TECH_ENV = "ANGELA_SKY130_MAGIC_TECH"
VOLARE_ROOT_ENV = "VOLARE_ROOT"
DEFAULT_VOLARE_VERSIONS = Path.home() / ".volare/volare/sky130/versions"


def find_magic_tech() -> Optional[Path]:
    """Locate the sky130A magic technology file the layout tools load.

    ``ANGELA_SKY130_MAGIC_TECH`` names the file directly, which is how a machine
    with a hand-installed PDK enables DRC and extraction. Otherwise the volare
    install is searched, from ``VOLARE_ROOT`` when it is set and from the default
    versions directory when it is not. Resolution happens per call rather than at
    import so a caller can point at another install without reloading the module.
    """
    configured = os.environ.get(MAGIC_TECH_ENV)
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return candidate
    roots = []
    if os.environ.get(VOLARE_ROOT_ENV):
        roots.append(Path(os.environ[VOLARE_ROOT_ENV]).expanduser())
    roots.append(DEFAULT_VOLARE_VERSIONS)
    for root in roots:
        for pattern in (
            "*/sky130A/libs.tech/magic/sky130A.tech",
            "sky130A/libs.tech/magic/sky130A.tech",
        ):
            for candidate in sorted(root.glob(pattern)):
                return candidate
    return None
