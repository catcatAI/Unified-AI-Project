"""Launch the text adventure game TUI."""
import sys
from pathlib import Path

# Ensure src is on the path
src = Path(__file__).resolve().parent / "apps" / "backend" / "src"
sys.path.insert(0, str(src))

from game.app import run_game

if __name__ == "__main__":
    run_game()
