# -*- coding: utf-8 -*-
"""pytest bootstrap: make apps/game-rpg modules importable by absolute name."""
import os
import sys

_GAME_RPG_DIR = os.path.dirname(os.path.abspath(__file__))
if _GAME_RPG_DIR not in sys.path:
    sys.path.insert(0, _GAME_RPG_DIR)