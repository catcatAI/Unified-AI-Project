"""
No shadowed methods in the shared renderer classes.

WHY: a method defined twice in a class body silently loses the first definition
— nothing errors, the file still parses, and the surface behaves as if a whole
feature were missing. Two live instances of this bug:

  * ``AngelaApp._handleClick/_handleDrag/_handleHover`` were defined at :218 and
    again at :965. InputHandler calls onClick(MouseEvent) / onDrag(dragState) /
    onHover(region, position), but the winning definitions read
    ``data?.bodyPart`` — always undefined. Clicking, dragging and hovering Angela
    did nothing.
  * ``UnifiedDisplayMatrix.handleTouch`` was the 192-line real implementation
    (coordinate transform → body-part detection → haptics → expression →
    StateMatrix4D) and then re-declared as a 10-line "add to queue" stub. The stub
    won, so ``handleClick()`` received ``{queued: true}`` with no ``bodyPart`` and
    every touch/click feature downstream was dead.

The vendored copies under libs/shared-js and js/shared-js are generated, so the
source of truth checked here is packages/shared-js/js only.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "packages" / "shared-js" / "js"

# Methods that legitimately appear more than once *within a file*: none today,
# but the class-boundary check below is what decides, not this list.
_METHOD = re.compile(r"^  (?:async\s+)?([A-Za-z_$][\w$]*)\s*\(", re.M)
_CLASS = re.compile(r"^class\s+([A-Za-z_$][\w$]*)", re.M)


def _class_sections(text: str) -> List[Tuple[str, int, int]]:
    """Return (class_name, start_line, end_line) for each top-level class."""
    starts = [(m.group(1), m.start()) for m in _CLASS.finditer(text)]
    sections: List[Tuple[str, int, int]] = []
    for index, (name, pos) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(text)
        sections.append((name, pos, end))
    return sections


def _methods_in(text: str, start: int, end: int) -> Dict[str, List[int]]:
    body = text[start:end]
    line_offset = text[:start].count("\n")
    found: Dict[str, List[int]] = {}
    for match in _METHOD.finditer(body):
        found.setdefault(match.group(1), []).append(line_offset + body[: match.start()].count("\n") + 1)
    return found


@pytest.mark.parametrize("module", sorted(SHARED.glob("*.js")), ids=lambda p: p.name)
def test_no_duplicate_methods_within_a_class(module: Path):
    text = module.read_text(encoding="utf-8", errors="ignore")
    offenders: List[str] = []
    for class_name, start, end in _class_sections(text):
        for method, lines in _methods_in(text, start, end).items():
            if len(lines) > 1:
                offenders.append(
                    f"{module.name}: {class_name}.{method} defined at lines {lines}"
                )
    assert not offenders, "shadowed methods (the later definition silently wins):\n" + "\n".join(
        offenders
    )


def test_touch_pipeline_methods_are_present_once():
    """Pin the two methods the interaction pipeline depends on."""
    text = (SHARED / "unified-display-matrix.js").read_text(encoding="utf-8")
    assert text.count("  handleTouch(") == 1
    assert text.count("  enqueueTouch(") == 1
    # The real implementation must be the one that survives, i.e. it must be
    # defined before the batching entry point and must do the work.
    handle_pos = text.index("  handleTouch(")
    queue_pos = text.index("  enqueueTouch(")
    assert handle_pos < queue_pos
    real_body = text[handle_pos:text.index("\n  }", handle_pos)]
    for marker in ("screenToCanvas", "bodyPart", "haptic", "expression"):
        assert marker.lower() in real_body.lower(), f"handleTouch lost {marker!r}"


def test_app_interaction_handlers_match_the_input_handler_contract():
    """InputHandler's callbacks define the contract; AngelaApp must match it.

    input-handler.js:157  this.onClick(event)               → MouseEvent
    input-handler.js:105  this.onDrag(this.currentDrag)     → drag state
    input-handler.js:86   this.onHover(region, position)    → region + position
    """
    app = (SHARED / "app.js").read_text(encoding="utf-8")
    for method in ("_handleClick", "_handleDrag", "_handleHover"):
        assert app.count(f"  {method}(") == 1, f"{method} must be defined exactly once"

    click = app[app.index("  _handleClick("): app.index("  _handleDrag(")]
    assert "udm.handleClick" in click, "click must run the UDM hit test"
    assert "bodyPart" in click

    drag = app[app.index("  _handleDrag("): app.index("  _handleHover(")]
    assert "handleTouch" in drag, "drag must go through the touch pipeline"

    hover = app[app.index("  _handleHover("):]
    hover = hover[: hover.index("\n  }\n") + 4]
    assert "handleInteraction" in hover, "hover must reach the state matrix"
