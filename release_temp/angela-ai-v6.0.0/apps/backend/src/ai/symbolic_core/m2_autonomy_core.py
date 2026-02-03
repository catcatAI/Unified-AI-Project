import asyncio
import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class M2AutonomyCore:
    """M2 Autonomy Core.
    Focuses on enabling self-direction, goal-setting, and independent decision-making.
    This implementation uses a rule-based system for goal-oriented decision-making.
    """

    def __init__(self):
        logger.info("M2AutonomyCore initialized.")
        self.available_actions = [
            "explore",
            "exploit",
            "wait",
            "seek_help",
            "recharge",
            "defend",
        ]

        # Define decision rules with conditions and actions, ordered by priority (higher in list = higher priority)
        # Conditions are functions that take context and return True/False
        self.decision_rules: list[dict[str, Any]] = [
            {
                "name": "Emergency_Defense",
                "condition": lambda ctx: ctx.get("situation") == "imminent threat",
                "action": "defend",
                "priority": 100,
                "confidence_base": 0.95,
            },
            {
                "name": "Urgent_Goal_Pursuit",
                "condition": lambda ctx: ctx.get("current_goal_urgency") == "high"
                and ctx.get("situation") != "imminent threat"
                and ctx.get("situation") != "path blocked",
                "action": "exploit",  # Focus on direct progress
                "priority": 90,
                "confidence_base": 0.90,
            },
            {
                "name": "Resource_Low_Recharge",
                "condition": lambda ctx: ctx.get("resource_level") == "low",
                "action": "recharge",
                "priority": 80,
                "confidence_base": 0.85,
            },
            {
                "name": "Path_Blocked_Seek_Help",
                "condition": lambda ctx: ctx.get("situation") == "path blocked"
                and ctx.get("decision_strategy") != "greedy",
                "action": "seek_help",
                "priority": 70,
                "confidence_base": 0.80,
            },
            {
                "name": "Greedy_Exploit",
                "condition": lambda ctx: ctx.get("decision_strategy") == "greedy"
                and ctx.get("situation") != "imminent threat",
                "action": "exploit",
                "priority": 60,
                "confidence_base": 0.75,
            },
            {
                "name": "Cautious_Explore",
                "condition": lambda ctx: ctx.get("decision_strategy") == "cautious"
                and ctx.get("situation") != "imminent threat",
                "action": "explore",
                "priority": 50,
                "confidence_base": 0.70,
            },
            {
                "name": "Balanced_Explore_or_Wait",
                "condition": lambda ctx: ctx.get("decision_strategy") == "balanced"
                and ctx.get("situation") != "imminent threat",
                "action": random.choice(
                    ["explore", "wait"],
                ),  # Still some non-determinism for balanced
                "priority": 40,
                "confidence_base": 0.65,
            },
            {
                "name": "Default_Wait",
                "condition": lambda ctx: True,  # Always true, lowest priority default
                "action": "wait",
                "priority": 10,
                "confidence_base": 0.50,
            },
        ]
        # Sort rules by priority (descending)
        self.decision_rules.sort(key=lambda x: x["priority"], reverse=True)

    async def make_decision(self, context: dict[str, Any]) -> dict[str, Any]:
        """Makes an autonomous decision based on current context, goal hierarchy, and predefined rules.
        Context can include: 'situation', 'current_goal', 'decision_strategy', 'resource_level', 'current_goal_urgency'.
        """
        situation = context.get("situation", "unknown")
        current_goal = context.get("current_goal", "survive")
        decision_strategy = context.get("decision_strategy", "balanced")

        logger.info(
            f"M2AutonomyCore: Making decision for situation: '{situation}', goal: '{current_goal}', strategy: '{decision_strategy}'",
        )
        await asyncio.sleep(0.05)  # Simulate processing time

        chosen_action = "wait"  # Default action if no rule matches
        confidence = 0.0

        for rule in self.decision_rules:
            try:
                if rule["condition"](context):
                    chosen_action = rule["action"]
                    confidence = rule["confidence_base"] + random.uniform(
                        -0.05,
                        0.05,
                    )  # Small random variance
                    logger.debug(
                        f"Rule '{rule['name']}' matched. Chosen action: {chosen_action}",
                    )
                    break  # Take the highest priority matching rule
            except Exception as e:
                logger.error(f"Error evaluating rule '{rule['name']}': {e}")
                continue

        confidence = min(0.99, max(0.01, confidence))  # Cap confidence

        logger.info(
            f"M2AutonomyCore: Decision made: '{chosen_action}' with confidence: {confidence:.2f}",
        )

        return {
            "status": "decision_made",
            "decision": chosen_action,
            "confidence": round(confidence, 2),
            "context_used": context,
        }


if __name__ == "__main__":

    async def main():
        # Set PYTHONPATH to include the project root for module resolution
        import os
        import sys

        sys.path.insert(
            0,
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."),
            ),
        )

        core = M2AutonomyCore()

        print("\n--- Test Case 1: Imminent Threat (Emergency Defense) ---")
        context1 = {
            "situation": "imminent threat",
            "current_goal": "survive",
            "decision_strategy": "any",
        }
        result1 = await core.make_decision(context1)
        print(f"Decision Result 1: {result1}")
        assert result1["decision"] == "defend"

        print("\n--- Test Case 2: Urgent Goal, Path Blocked (Seek Help) ---")
        context2 = {
            "situation": "path blocked",
            "current_goal": "reach destination",
            "current_goal_urgency": "high",
            "decision_strategy": "cautious",
        }
        result2 = await core.make_decision(context2)
        print(f"Decision Result 2: {result2}")
        assert result2["decision"] == "seek_help"

        print("\n--- Test Case 3: Low Resource (Recharge) ---")
        context3 = {
            "situation": "safe",
            "current_goal": "explore",
            "resource_level": "low",
            "decision_strategy": "balanced",
        }
        result3 = await core.make_decision(context3)
        print(f"Decision Result 3: {result3}")
        assert result3["decision"] == "recharge"

        print("\n--- Test Case 4: Greedy Strategy, No Immediate Threat ---")
        context4 = {
            "situation": "routine",
            "current_goal": "maximize gain",
            "decision_strategy": "greedy",
        }
        result4 = await core.make_decision(context4)
        print(f"Decision Result 4: {result4}")
        assert result4["decision"] == "exploit"

        print("\n--- Test Case 5: Cautious Strategy, No Immediate Threat ---")
        context5 = {
            "situation": "unknown area",
            "current_goal": "gather info",
            "decision_strategy": "cautious",
        }
        result5 = await core.make_decision(context5)
        print(f"Decision Result 5: {result5}")
        assert result5["decision"] == "explore"

        print(
            "\n--- Test Case 6: Balanced Strategy, No Specific Rule Match (should be explore/wait) ---",
        )
        context6 = {
            "situation": "idle",
            "current_goal": "maintain system",
            "decision_strategy": "balanced",
        }
        result6 = await core.make_decision(context6)
        print(f"Decision Result 6: {result6}")
        assert result6["decision"] in [
            "explore",
            "wait",
        ]  # Balanced still has some non-determinism

        print("\n--- Test Case 7: Default Rule (Wait) ---")
        context7 = {
            "situation": "all clear",
            "current_goal": "none",
            "decision_strategy": "passive",
        }
        result7 = await core.make_decision(context7)
        print(f"Decision Result 7: {result7}")
        assert result7["decision"] == "wait"

    asyncio.run(main())
