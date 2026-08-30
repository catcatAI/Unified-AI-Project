#!/usr/bin/env python3
"""
ai-player-client.py — External AI Player for Crystal Cards

Connects to the running game via WebSocket, reads game state,
and sends actions. Can use:
1. Angela AI Vision API (if available) — screenshot → vision analysis
2. Rule-based AI (fallback) — state-based decision making

Usage:
  1. Start the game: cd apps/crystal-cards && pnpm start
  2. Run this script: python3 apps/crystal-cards/ai-player-client.py
"""

import json
import time
import sys
import os
import base64
import urllib.request
import urllib.error
from pathlib import Path

try:
    import websocket
    HAS_WS = True
except ImportError:
    HAS_WS = False
    print("⚠️  websocket-client not installed. Using HTTP fallback.")
    print("   Install: pip install websocket-client")

try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ═══════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════
GAME_WS_URL = "ws://127.0.0.1:8765"
GAME_HTTP_URL = "http://127.0.0.1:8765"
ANGELA_HTTP_URL = "http://127.0.0.1:8000"
MAX_DAYS = 30
DECISION_DELAY = 0.5  # seconds between decisions


# ═══════════════════════════════════════════════════════
# Game Client
# ═══════════════════════════════════════════════════════
class GameClient:
    """Communicates with the Crystal Cards game."""

    def __init__(self):
        self.ws = None
        self.connected = False

    def connect_ws(self):
        if not HAS_WS:
            return False
        try:
            self.ws = websocket.create_connection(GAME_WS_URL, timeout=5)
            self.connected = True
            print(f"✅ Connected to game at {GAME_WS_URL}")
            return True
        except Exception as e:
            print(f"❌ WebSocket failed: {e}")
            return False

    def get_state_http(self):
        try:
            req = urllib.request.Request(f"{GAME_HTTP_URL}/state")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e)}

    def send_action_http(self, action):
        try:
            data = json.dumps(action).encode()
            req = urllib.request.Request(
                f"{GAME_HTTP_URL}/action",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_state(self):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps({"type": "get_state"}))
                resp = json.loads(self.ws.recv())
                return resp.get("state", {})
            except Exception:
                self.connected = False
        return self.get_state_http()

    def send_action(self, action):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps({"type": "action", **action}))
                resp = json.loads(self.ws.recv())
                return resp
            except Exception:
                self.connected = False
        return self.send_action_http(action)

    def get_screenshot(self):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps({"type": "screenshot"}))
                resp = json.loads(self.ws.recv())
                return resp.get("data")
            except Exception:
                pass
        return None


# ═══════════════════════════════════════════════════════
# Angela AI Vision Client
# ═══════════════════════════════════════════════════════
class AngelaVisionClient:
    """Uses Angela AI's multimodal capabilities for game analysis."""

    def __init__(self):
        self.connected = False
        self._check_connection()

    def _check_connection(self):
        try:
            req = urllib.request.Request(f"{ANGELA_HTTP_URL}/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.connected = resp.status == 200
        except Exception:
            self.connected = False

    def analyze_screenshot(self, screenshot_data_url):
        """Send screenshot to Angela for analysis."""
        if not self.connected:
            return None

        try:
            # Extract base64 data
            if screenshot_data_url.startswith("data:"):
                b64_data = screenshot_data_url.split(",", 1)[1]
            else:
                b64_data = screenshot_data_url

            prompt = (
                "This is a screenshot of a card game (Stacklands-style). "
                "Analyze the game state and tell me what action to take. "
                "Consider: card positions, health bars, available resources, "
                "and the current game situation. "
                "Respond with a JSON object: "
                '{"action": "click|drag|draw|dialog|rest", '
                '"target": "card_name or description", '
                '"reason": "brief explanation"}'
            )

            data = json.dumps({
                "message": prompt,
                "context": {"source": "crystal-cards-vision", "screenshot": b64_data[:1000]},
            }).encode()

            req = urllib.request.Request(
                f"{ANGELA_HTTP_URL}/chat/unified",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                text = result.get("response", result.get("response_text", ""))
                # Try to parse JSON from response
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"action": "rest", "reason": text[:100]}
        except Exception as e:
            return None

    def generate_dialogue_choice(self, speaker, text, choices):
        """Ask Angela which dialogue choice to pick."""
        if not self.connected:
            return 0

        try:
            prompt = (
                f"In a game, NPC '{speaker}' says: {text}\n"
                f"Available choices: {json.dumps(choices, ensure_ascii=False)}\n"
                "Pick the best choice index (0-based) that advances the story. "
                "Respond with just the index number."
            )

            data = json.dumps({
                "message": prompt,
                "context": {"source": "crystal-cards-dialogue"},
            }).encode()

            req = urllib.request.Request(
                f"{ANGELA_HTTP_URL}/chat/unified",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                text = result.get("response", "").strip()
                # Extract number from response
                for word in text.split():
                    if word.isdigit():
                        return int(word)
                return 0
        except Exception:
            return 0


# ═══════════════════════════════════════════════════════
# Rule-Based AI (Fallback)
# ═══════════════════════════════════════════════════════
class RuleBasedAI:
    """Makes decisions based on game state without vision."""

    def decide(self, state):
        """Return an action dict based on current state."""
        if not state or "error" in state:
            return {"action": "rest", "reason": "No state available"}

        hp = state.get("hp", 100)
        sanity = state.get("sanity", 100)
        gold = state.get("gold", 0)
        day = state.get("day", 1)
        board = state.get("boardCards", [])
        sidebar = state.get("sidebarCards", [])
        inventory = state.get("inventory", [])

        # Priority 1: Survival
        if hp < 30:
            return {"action": "rest", "reason": "HP low, resting"}

        if sanity < 20:
            return {"action": "rest", "reason": "Sanity low, resting"}

        # Priority 2: Check for dialog overlay
        # (would need DOM check, skip for now)

        # Priority 3: Fight enemies if we have characters
        chars = [c for c in board if c.get("type") == "character"]
        enemies = [c for c in board if c.get("type") == "enemy"]
        if chars and enemies:
            return {
                "action": "stack_cards",
                "cardA": chars[0]["id"],
                "cardB": enemies[0]["id"],
                "reason": f"Fight {enemies[0].get('name', 'enemy')}",
            }

        # Priority 4: Talk to characters at their locations
        locs = {c["templateId"]: c for c in board if c.get("type") == "location"}
        for char in chars:
            char_loc = self._get_char_location(char["templateId"])
            if char_loc and char_loc in locs:
                return {
                    "action": "stack_cards",
                    "cardA": char["id"],
                    "cardB": locs[char_loc]["id"],
                    "reason": f"Talk to {char.get('name', 'NPC')}",
                }

        # Priority 5: Draw cards if we have gold
        draw_cost = 3 + (day // 3)
        if gold >= draw_cost:
            return {"action": "draw_card", "reason": f"Draw card ({draw_cost} gold)"}

        # Priority 6: Place resources from sidebar
        resources = [s for s in sidebar if s.get("type") == "resource"]
        if resources and len(board) < 15:
            idx = sidebar.index(resources[0])
            return {
                "action": "sidebar_click",
                "index": idx,
                "reason": f"Place {resources[0].get('name', 'resource')}",
            }

        # Default: rest
        return {"action": "rest", "reason": "Nothing urgent to do"}

    def _get_char_location(self, template_id):
        """Map character template ID to their home location."""
        location_map = {
            "char_hikuraya": "loc_library",
            "char_red": "loc_market",
            "char_watchman": "loc_mirror_lake",
            "char_wings": "loc_library",
            "char_old_man": "loc_market",
        }
        return location_map.get(template_id)


# ═══════════════════════════════════════════════════════
# Main Game Loop
# ═══════════════════════════════════════════════════════
def run_ai_player():
    print("🎮 Crystal Cards — AI Visual Player")
    print("=" * 50)

    # Connect to game
    game = GameClient()
    if not game.connect_ws():
        print("Trying HTTP fallback...")
        state = game.get_state_http()
        if "error" in state:
            print(f"❌ Cannot connect to game: {state['error']}")
            print("   Make sure the game is running: pnpm start")
            sys.exit(1)

    # Connect to Angela AI
    angela = AngelaVisionClient()
    if angela.connected:
        print("🤖 Angela AI Vision: ✅ Connected")
    else:
        print("🤖 Angela AI Vision: ❌ Offline (using rule-based AI)")

    # AI engines
    rule_ai = RuleBasedAI()

    print(f"\n═══ AI Player Starting (max {MAX_DAYS} days) ═══\n")

    for day in range(1, MAX_DAYS + 1):
        print(f"📅 Day {day}")

        # Run multiple decisions per day
        for tick in range(12):
            state = game.get_state()
            if not state or "error" in state:
                print(f"  ⚠️  Tick {tick}: No state, retrying...")
                time.sleep(1)
                continue

            # Check for dialog
            dialog_state = _check_dialog(game)
            if dialog_state:
                choice = _handle_dialog(game, angela, dialog_state)
                if choice is not None:
                    print(f"  💬 Dialog: chose option {choice}")

            # Get AI decision
            decision = rule_ai.decide(state)

            # Try vision analysis if Angela is connected and we have a screenshot
            if angela.connected and tick % 4 == 0:
                screenshot = game.get_screenshot()
                if screenshot and HAS_PIL:
                    vision_decision = angela.analyze_screenshot(screenshot)
                    if vision_decision and vision_decision.get("action"):
                        decision = vision_decision

            # Execute action
            if decision.get("action") != "rest":
                result = game.send_action(decision)
                success = result.get("success", False) if isinstance(result, dict) else False
                if success:
                    print(f"  ✅ {decision.get('reason', decision.get('action'))}")
                else:
                    err = result.get("error", "unknown") if isinstance(result, dict) else "unknown"
                    # Don't print every failed rest
                    if decision.get("action") != "rest":
                        print(f"  ❌ {decision.get('action')}: {err}")

            time.sleep(DECISION_DELAY)

        # Day summary
        state = game.get_state()
        if state and "error" not in state:
            print(f"  📊 HP={state.get('hp', '?')} SAN={state.get('sanity', '?')} "
                  f"Gold={state.get('gold', '?')} Knowledge={state.get('knowledge', '?')} "
                  f"Board={len(state.get('boardCards', []))} "
                  f"Sidebar={len(state.get('sidebarCards', []))}")

    print("\n═══ AI Player Finished ═══")


def _check_dialog(game):
    """Check if dialog overlay is visible."""
    # Would need DOM inspection via WebSocket
    # For now, return None (no dialog)
    return None


def _handle_dialog(game, angela, dialog_state):
    """Handle dialogue choices."""
    # Would need DOM inspection for choices
    return None


if __name__ == "__main__":
    run_ai_player()
