"""
Deprecation Warning: The agents/ package has been moved to agents/legacy/.

These demo/example agents are no longer imported by production code.
They remain available for reference purposes only.
"""

import warnings

warnings.warn(
    "The 'agents' package is deprecated. "
    "These demo agents have been moved to 'agents.legacy' and are no longer in use.",
    DeprecationWarning,
    stacklevel=2,
)
