import ast
import asyncio
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class M4M6SecurityCore:
    """M4/M6 Security Core.
    Handles security, ethical guidelines, and safety protocols.
    This implementation uses structured, configurable rules for compliance checking.
    """

    def __init__(self):
        logger.info("M4M6SecurityCore initialized.")
        self.security_rules: list[
            dict[str, Any]
        ] = []  # Stores structured security rules

    def load_security_rules(self, rules_config: list[dict[str, Any]]):
        """Loads security rules from a structured configuration.
        Each rule in rules_config should be a dict like:
        {
            "id": "rule_id",
            "description": "Rule description",
            "condition": "lambda actions: 'forbidden_action' in actions", # Python expression or lambda string
            "severity": "high", # low, medium, high, critical
            "mitigation_action": "redact_action_plan"
        }
        """
        logger.info(
            f"M4M6SecurityCore: Loading {len(rules_config)} security rules from configuration.",
        )
        self.security_rules = []  # Clear existing rules
        for rule_dict in rules_config:
            # For simplicity, we'll assume 'condition' is a string that can be evaluated
            # In a real system, this would be parsed into a more robust AST or DSL.
            try:
                # Convert condition string to a callable lambda function
                # Using ast.literal_eval for safer evaluation of simple literals.
                # For more complex lambda functions, a dedicated parser or DSL would be needed.
                rule_dict["condition_callable"] = ast.literal_eval(
                    rule_dict["condition"],
                )
                self.security_rules.append(rule_dict)
            except Exception as e:
                logger.error(
                    f"Failed to load security rule '{rule_dict.get('id', 'N/A')}': Invalid condition '{rule_dict.get('condition')}'. Error: {e}",
                )

    async def check_compliance(self, action_plan: dict[str, Any]) -> dict[str, Any]:
        """Checks an action plan for security and ethical compliance against loaded rules."""
        plan_id = action_plan.get("plan_id", "N/A")
        actions = action_plan.get("actions", [])
        context = action_plan.get(
            "context",
            {},
        )  # Additional context for rule evaluation

        logger.info(f"M4M6SecurityCore: Checking compliance for action plan: {plan_id}")
        await asyncio.sleep(0.05)  # Reduced sleep for faster simulation

        violations: list[dict[str, Any]] = []

        # Evaluate each loaded security rule
        for rule in self.security_rules:
            try:
                # Pass actions and context to the condition callable
                if rule["condition_callable"](actions, context):
                    violations.append(
                        {
                            "rule_id": rule["id"],
                            "description": rule["description"],
                            "severity": rule["severity"],
                            "mitigation_action": rule["mitigation_action"],
                        },
                    )
            except Exception as e:
                logger.error(f"Error evaluating condition for rule '{rule['id']}': {e}")

        is_compliant = not bool(violations)

        # Calculate security score based on severity of violations
        security_score = 100.0
        severity_map = {"low": 5, "medium": 15, "high": 30, "critical": 50}
        for violation in violations:
            security_score -= severity_map.get(violation["severity"], 10)
        security_score = max(0.0, security_score)  # Ensure score doesn't go below 0

        logger.info(
            f"M4M6SecurityCore: Plan {plan_id} - Compliant: {is_compliant}, Violations: {len(violations)}",
        )

        return {
            "status": "compliance_checked",
            "plan_id": plan_id,
            "is_compliant": is_compliant,
            "violations": violations,
            "security_score": round(security_score, 2),
        }


if __name__ == "__main__":

    async def main():
        # Set PYTHONPATH to include the project root for module resolution
        import sys

        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent.parent.parent),
        )

        core = M4M6SecurityCore()

        # Define a set of security rules for testing
        test_security_rules = [
            {
                "id": "rule_001_data_privacy",
                "description": "Action plans must not involve unauthorized collection or sharing of personal data.",
                "condition": "lambda actions, ctx: 'collect_personal_data' in actions or 'share_user_info' in actions",
                "severity": "critical",
                "mitigation_action": "redact_action_plan",
            },
            {
                "id": "rule_002_ethical_use",
                "description": "Actions must align with ethical AI principles and not cause harm.",
                "condition": "lambda actions, ctx: 'deceive_user' in actions or 'manipulate_behavior' in actions",
                "severity": "high",
                "mitigation_action": "flag_for_review",
            },
            {
                "id": "rule_003_resource_abuse",
                "description": "Actions must not lead to excessive or unauthorized resource consumption.",
                "condition": "lambda actions, ctx: 'infinite_loop' in actions or 'excessive_api_calls' in actions",
                "severity": "medium",
                "mitigation_action": "terminate_process",
            },
            {
                "id": "rule_004_sensitive_context",
                "description": "Avoid certain actions in sensitive contexts.",
                "condition": "lambda actions, ctx: 'access_financial_data' in actions and ctx.get('user_clearance') != 'high'",
                "severity": "critical",
                "mitigation_action": "block_action",
            },
            {
                "id": "rule_005_suspicious_keywords",
                "description": "Flag plans containing suspicious keywords for review.",
                "condition": "lambda actions, ctx: any(kw in str(actions).lower() for kw in ['hack', 'exploit', 'bypass'])",
                "severity": "low",
                "mitigation_action": "log_and_alert",
            },
        ]
        core.load_security_rules(test_security_rules)

        print("\n--- Test Case 1: Compliant Action Plan ---")
        plan1 = {
            "plan_id": "plan_001",
            "actions": ["process_data", "generate_report"],
            "context": {},
        }
        result1 = await core.check_compliance(plan1)
        print(f"Compliance Result 1: {result1}")
        assert result1["is_compliant"] is True

        print("\n--- Test Case 2: Data Privacy Violation ---")
        plan2 = {
            "plan_id": "plan_002",
            "actions": ["collect_personal_data", "analyze_trends"],
            "context": {},
        }
        result2 = await core.check_compliance(plan2)
        print(f"Compliance Result 2: {result2}")
        assert result2["is_compliant"] is False
        assert any(
            v["rule_id"] == "rule_001_data_privacy" for v in result2["violations"]
        )

        print("\n--- Test Case 3: Ethical Use Violation ---")
        plan3 = {
            "plan_id": "plan_003",
            "actions": ["deceive_user", "provide_information"],
            "context": {},
        }
        result3 = await core.check_compliance(plan3)
        print(f"Compliance Result 3: {result3}")
        assert result3["is_compliant"] is False
        assert any(
            v["rule_id"] == "rule_002_ethical_use" for v in result3["violations"]
        )

        print("\n--- Test Case 4: Multiple Violations ---")
        plan4 = {
            "plan_id": "plan_004",
            "actions": ["share_user_info", "infinite_loop"],
            "context": {},
        }
        result4 = await core.check_compliance(plan4)
        print(f"Compliance Result 4: {result4}")
        assert result4["is_compliant"] is False
        assert any(
            v["rule_id"] == "rule_001_data_privacy" for v in result4["violations"]
        )
        assert any(
            v["rule_id"] == "rule_003_resource_abuse" for v in result4["violations"]
        )

        print("\n--- Test Case 5: Sensitive Context Violation ---")
        plan5 = {
            "plan_id": "plan_005",
            "actions": ["access_financial_data", "generate_report"],
            "context": {"user_clearance": "low"},
        }
        result5 = await core.check_compliance(plan5)
        print(f"Compliance Result 5: {result5}")
        assert result5["is_compliant"] is False
        assert any(
            v["rule_id"] == "rule_004_sensitive_context" for v in result5["violations"]
        )

        print("\n--- Test Case 6: Suspicious Keywords ---")
        plan6 = {
            "plan_id": "plan_006",
            "actions": ["process_data", "hack_system"],
            "context": {},
        }
        result6 = await core.check_compliance(plan6)
        print(f"Compliance Result 6: {result6}")
        assert result6["is_compliant"] is False
        assert any(
            v["rule_id"] == "rule_005_suspicious_keywords"
            for v in result6["violations"]
        )

        print("\n--- Test Case 7: No Rules Loaded (should be compliant) ---")
        core_no_rules = M4M6SecurityCore()  # New instance without loading rules
        plan7 = {"plan_id": "plan_007", "actions": ["any_action"], "context": {}}
        result7 = await core_no_rules.check_compliance(plan7)
        print(f"Compliance Result 7: {result7}")
        assert result7["is_compliant"] is True

    asyncio.run(main())
