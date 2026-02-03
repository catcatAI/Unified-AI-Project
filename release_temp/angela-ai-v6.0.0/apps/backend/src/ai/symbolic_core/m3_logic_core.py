import asyncio
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class M3LogicCore:
    """M3 Logic Core.
    Handles formal logic, reasoning, and consistency checking.
    Enhanced to support conjunctions in rules, more robust consistency checks,
    and loading rules from a structured configuration.
    """

    def __init__(self):
        logger.info("M3LogicCore initialized.")
        self.known_facts: list[str] = []  # Store known facts
        self.rules: list[dict[str, Any]] = []  # Store parsed rules

    def load_rules(self, rules_config: list[dict[str, Any]]):
        """Loads rules from a structured configuration.
        Each rule in rules_config should be a dict like:
        {"name": "rule_name", "if": "antecedent_string", "then": "consequent_string"}
        """
        logger.info(
            f"M3LogicCore: Loading {len(rules_config)} rules from configuration.",
        )
        self.rules = []  # Clear existing rules
        for rule_dict in rules_config:
            rule_str = f"If {rule_dict['if']} then {rule_dict['then']}"
            parsed_rule = self._parse_rule(rule_str)
            if parsed_rule:
                parsed_rule["name"] = rule_dict.get("name", "unnamed_rule")
                self.rules.append(parsed_rule)
            else:
                logger.warning(
                    f"M3LogicCore: Failed to parse rule from config: {rule_str}",
                )

    async def apply_logic_rules(
        self,
        facts: list[str],
        rules_to_apply: list[str] | None = None,
    ) -> dict[str, Any]:
        """Applies logic rules to a set of facts, performs inference, and checks consistency.
        If rules_to_apply is provided, it uses those rules. Otherwise, it uses rules loaded via load_rules.
        """
        rules_to_use = (
            rules_to_apply
            if rules_to_apply is not None
            else [self._format_parsed_rule(r) for r in self.rules]
        )

        logger.info(
            f"M3LogicCore: Applying {len(rules_to_use)} rules to {len(facts)} facts.",
        )
        await asyncio.sleep(0.05)  # Reduced sleep for faster simulation

        # Update known facts
        self.known_facts.extend(facts)
        current_facts = list(set(self.known_facts))  # Remove duplicates

        # Perform inference
        inferred_facts = self._infer_facts(current_facts, rules_to_use)

        # Update known_facts with all inferred facts
        self.known_facts = list(
            set(inferred_facts),
        )  # Ensure known_facts contains all inferred facts

        # Check consistency
        is_consistent, contradictions = self._check_consistency(
            self.known_facts,
        )  # Get contradictions

        return {
            "status": "logic_applied",
            "initial_facts": facts,
            "rules_applied_count": len(rules_to_use),
            "inferred_facts": inferred_facts,
            "consistency_check": is_consistent,
            "contradictions": contradictions,  # Include contradictions in the result
        }

    def _format_parsed_rule(self, parsed_rule: dict[str, Any]) -> str:
        """Converts a parsed rule dictionary back into a string format for _infer_facts if needed."""
        antecedent_parts = []
        for ant in parsed_rule["antecedent"]:
            if ant["args"]:
                antecedent_parts.append(f"{ant['predicate']}({', '.join(ant['args'])})")
            else:
                antecedent_parts.append(ant["predicate"])

        consequent_str = parsed_rule["consequent"]["predicate"]
        if parsed_rule["consequent"]["args"]:
            consequent_str += f"({', '.join(parsed_rule['consequent']['args'])})"
        if parsed_rule["consequent"]["negated"]:
            consequent_str = f"NOT {consequent_str}"

        return f"If {' and '.join(antecedent_parts)} then {consequent_str}"

    def _parse_rule(self, rule: str) -> dict[str, Any]:
        """Parses a simple 'If X then Y' rule, supporting conjunctions in X (e.g., 'If A and B then C').
        Extracts predicates and variables, handling negation in consequent.
        Returns {'antecedent': [{'predicate': 'is_bird', 'variable': 'X'}], 'consequent': {'predicate': 'has_feathers', 'variable': 'X', 'negated': False}}
        or None if invalid.
        """
        match = re.match(r"If (.+) then (.+)", rule, re.IGNORECASE)
        if match:
            antecedent_str = match.group(1).strip()
            consequent_str = match.group(2).strip()

            parsed_antecedents = []
            for ant_part in antecedent_str.split(" and "):
                # Enhanced regex to capture multiple arguments
                pred_match = re.match(r"(\w+)\(([\w_,\s]+)\)", ant_part.strip())
                if pred_match:
                    predicate = pred_match.group(1)
                    args_str = pred_match.group(2)
                    args = [arg.strip() for arg in args_str.split(",")]
                    parsed_antecedents.append({"predicate": predicate, "args": args})
                else:
                    # Handle simple facts without variables in antecedent
                    parsed_antecedents.append(
                        {"predicate": ant_part.strip(), "args": []},
                    )

            # Handle negation in consequent
            consequent_negated = False
            if consequent_str.startswith("NOT "):
                consequent_negated = True
                consequent_str = consequent_str[4:]

            # Enhanced regex for consequent to capture multiple arguments
            pred_match_consequent = re.match(
                r"(\w+)\(([\w_,\s]+)\)",
                consequent_str.strip(),
            )
            if pred_match_consequent:
                predicate = pred_match_consequent.group(1)
                args_str = pred_match_consequent.group(2)
                args = [arg.strip() for arg in args_str.split(",")]
                parsed_consequent = {
                    "predicate": predicate,
                    "args": args,
                    "negated": consequent_negated,
                }
            else:
                parsed_consequent = {
                    "predicate": consequent_str.strip(),
                    "args": [],
                    "negated": consequent_negated,
                }

            return {"antecedent": parsed_antecedents, "consequent": parsed_consequent}
        return None

    def _infer_facts(self, facts: list[str], rules: list[str]) -> list[str]:
        """Performs a basic forward chaining inference, supporting simple variable matching and conjunctions.
        Correctly infers concrete negated facts.
        """
        inferred = set(facts)
        new_inferences_made = True
        while new_inferences_made:
            new_inferences_made = False
            newly_inferred = set()  # Collect new inferences in a separate set

            for rule_str in rules:
                parsed_rule = self._parse_rule(rule_str)
                if not parsed_rule:
                    logger.warning(f"M3LogicCore: Invalid rule format: {rule_str}")
                    continue

                antecedents = parsed_rule["antecedent"]
                consequent = parsed_rule["consequent"]

                # Step 1: For each antecedent, find all facts that match its predicate
                # and extract the entity, creating potential bindings for its variable.
                # This will be a list of lists, where each inner list contains potential
                # (fact, binding_dict) pairs for one antecedent.
                potential_matches_per_antecedent = []
                for ant in antecedents:
                    current_antecedent_matches = []
                    for fact in inferred:
                        is_fact_negated = False
                        fact_content = fact
                        if fact.startswith("NOT "):
                            is_fact_negated = True
                            fact_content = fact[4:]

                        # Enhanced regex to capture predicate and all arguments
                        fact_match = re.match(r"(\w+)\(([\w_,\s]*)\)", fact_content)

                        if (
                            not is_fact_negated
                        ):  # Only consider positive facts for positive antecedents
                            if fact_match:
                                fact_predicate = fact_match.group(1)
                                fact_args = [
                                    arg.strip()
                                    for arg in fact_match.group(2).split(",")
                                    if arg.strip()
                                ]
                            else:
                                fact_predicate = fact_content.strip()
                                fact_args = []

                            # Check if the fact's predicate matches the antecedent's predicate
                            if fact_predicate == ant["predicate"]:
                                # Create bindings for all arguments
                                current_bindings_for_fact = {}
                                is_match = True
                                if len(ant["args"]) == len(fact_args):
                                    for i, ant_arg in enumerate(ant["args"]):
                                        fact_arg = fact_args[i]
                                        if ant_arg.isupper():  # It's a variable
                                            current_bindings_for_fact[ant_arg] = (
                                                fact_arg
                                            )
                                        elif (
                                            ant_arg != fact_arg
                                        ):  # It's a constant and doesn't match
                                            is_match = False
                                            break
                                else:  # Argument count mismatch
                                    is_match = False

                                if is_match:
                                    current_antecedent_matches.append(
                                        (fact, current_bindings_for_fact),
                                    )

                    potential_matches_per_antecedent.append(current_antecedent_matches)

                # If any antecedent has no matches, this rule cannot fire
                if any(not matches for matches in potential_matches_per_antecedent):
                    continue

                # Step 2: Generate all combinations of these potential matches
                # using itertools.product to find consistent bindings across all antecedents.
                import itertools

                for combination_of_matches in itertools.product(
                    *potential_matches_per_antecedent,
                ):
                    current_bindings = {}
                    is_consistent_combination = True

                    # Check for consistent bindings across the combination of matches
                    for fact, binding_dict in combination_of_matches:
                        for var, val in binding_dict.items():
                            if var in current_bindings and current_bindings[var] != val:
                                is_consistent_combination = False
                                break
                            current_bindings[var] = val
                        if not is_consistent_combination:
                            break

                    if not is_consistent_combination:
                        continue

                    # Step 3: All antecedents are satisfied with consistent bindings, infer the consequent
                    inferred_consequent_args = []
                    for arg in consequent["args"]:
                        if (
                            arg.isupper() and arg in current_bindings
                        ):  # It's a variable and has a binding
                            inferred_consequent_args.append(current_bindings[arg])
                        else:
                            inferred_consequent_args.append(
                                arg,
                            )  # It's a constant or unbound variable

                    inferred_consequent_fact = consequent["predicate"]
                    if inferred_consequent_args:
                        inferred_consequent_fact += (
                            f"({', '.join(inferred_consequent_args)})"
                        )

                    if consequent["negated"]:
                        inferred_consequent_fact = f"NOT {inferred_consequent_fact}"

                    if (
                        inferred_consequent_fact not in inferred
                        and inferred_consequent_fact not in newly_inferred
                    ):
                        newly_inferred.add(inferred_consequent_fact)
                        new_inferences_made = True
                        logger.debug(
                            f"M3LogicCore: Inferred '{inferred_consequent_fact}' using rule '{rule_str}' and bindings '{current_bindings}'",
                        )

            inferred.update(newly_inferred)
        return list(inferred)

    def _check_consistency(self, facts: list[str]) -> (bool, list[dict[str, str]]):
        """Performs a more robust consistency check.
        Checks for direct contradictions like "X(Y)" and "NOT X(Y)".
        Returns a tuple: (is_consistent, list_of_contradictions).
        """
        contradictions = []
        # Store facts in a structured way for easier contradiction checking
        # {'predicate(entity)': {'positive': True/False, 'negative': True/False}}
        structured_facts_for_consistency = {}

        for fact in facts:
            is_negated = False
            fact_content = fact
            if fact.startswith("NOT "):
                is_negated = True
                fact_content = fact[4:]

            # Extract predicate and entity for structured storage
            pred_match = re.match(r"(\w+)\(([\w_]+)\)", fact_content)
            if pred_match:
                key = f"{pred_match.group(1)}({pred_match.group(2)})"
            else:
                key = fact_content  # For simple facts without (entity)

            if key not in structured_facts_for_consistency:
                structured_facts_for_consistency[key] = {
                    "positive": False,
                    "negative": False,
                }

            if is_negated:
                structured_facts_for_consistency[key]["negative"] = True
            else:
                structured_facts_for_consistency[key]["positive"] = True

        for key, status in structured_facts_for_consistency.items():
            if status["positive"] and status["negative"]:
                contradictions.append(
                    {
                        "fact": key,
                        "contradiction": f"'{key}' is asserted as both True and False.",
                    },
                )

        if contradictions:
            return False, contradictions
        return True, []


if __name__ == "__main__":

    async def main():
        # Set PYTHONPATH to include the project root for module resolution
        import sys

        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent.parent.parent),
        )

        # Test Case 1: Simple Inference with Variable (using direct rules)
        core1 = M3LogicCore()
        print("\n--- Test Case 1: Simple Inference with Variable (direct rules) ---")
        facts1 = ["is_bird(tweety)", "can_fly(tweety)"]
        rules1 = ["If is_bird(X) then has_feathers(X)"]
        result1 = await core1.apply_logic_rules(facts1, rules1)
        print(f"Result 1: {result1}")
        assert "has_feathers(tweety)" in result1["inferred_facts"]
        assert result1["consistency_check"] is True

        # Test Case 2: Inference with Conjunction and Variables (using direct rules)
        core2 = M3LogicCore()
        print(
            "\n--- Test Case 2: Inference with Conjunction and Variables (direct rules) ---",
        )
        facts2 = ["is_mammal(dog)", "has_fur(dog)"]
        rules2 = ["If is_mammal(X) and has_fur(X) then is_warm_blooded(X)"]
        result2 = await core2.apply_logic_rules(facts2, rules2)
        print(f"Result 2: {result2}")
        assert "is_warm_blooded(dog)" in result2["inferred_facts"]
        assert result2["consistency_check"] is True

        # Test Case 3: No Inference (missing antecedent) (using direct rules)
        core3 = M3LogicCore()
        print("\n--- Test Case 3: No Inference (missing antecedent) (direct rules) ---")
        facts3 = ["is_fish(salmon)"]
        rules3 = ["If is_bird(X) then lays_eggs(X)"]
        result3 = await core3.apply_logic_rules(facts3, rules3)
        print(f"Result 3: {result3}")
        assert "lays_eggs(salmon)" not in result3["inferred_facts"]
        assert result3["consistency_check"] is True

        # Test Case 4: Direct Contradiction (using direct rules)
        core4 = M3LogicCore()
        print("\n--- Test Case 4: Direct Contradiction (direct rules) ---")
        facts4 = ["is_alive(cat)", "NOT is_alive(cat)"]
        rules4 = []
        result4 = await core4.apply_logic_rules(facts4, rules4)
        print(f"Result 4: {result4}")
        assert result4["consistency_check"] is False
        assert len(result4["contradictions"]) > 0

        # Test Case 5: Complex Contradiction (after inference) (using direct rules)
        core5 = M3LogicCore()
        print(
            "\n--- Test Case 5: Complex Contradiction (after inference) (direct rules) ---",
        )
        facts5 = ["is_human(socrates)"]
        rules5 = [
            "If is_human(X) then is_mortal(X)",
            "If is_mortal(X) then NOT is_immortal(X)",
            "If is_human(X) then is_immortal(X)",  # Contradictory rule
        ]
        result5 = await core5.apply_logic_rules(facts5, rules5)
        print(f"Result 5: {result5}")
        assert result5["consistency_check"] is False
        assert len(result5["contradictions"]) > 0

        # Test Case 6: Inference with multiple variables (using direct rules)
        core6 = M3LogicCore()
        print("\n--- Test Case 6: Inference with multiple variables (direct rules) ---")
        facts6 = ["parent(john, mary)", "parent(mary, peter)"]
        rules6 = ["If parent(X, Y) and parent(Y, Z) then grandparent(X, Z)"]
        result6 = await core6.apply_logic_rules(facts6, rules6)
        print(f"Result 6: {result6}")
        assert "grandparent(john, peter)" in result6["inferred_facts"]
        assert result6["consistency_check"] is True

        # --- New Test Cases for Rule Loading from Configuration ---
        print("\n--- Test Case 7: Rule Loading from Configuration ---")
        core7 = M3LogicCore()
        config_rules = [
            {"name": "bird_feathers", "if": "is_bird(X)", "then": "has_feathers(X)"},
            {
                "name": "mammal_warm_blooded",
                "if": "is_mammal(X) and has_fur(X)",
                "then": "is_warm_blooded(X)",
            },
        ]
        core7.load_rules(config_rules)

        facts7 = ["is_bird(eagle)", "is_mammal(bear)", "has_fur(bear)"]
        result7 = await core7.apply_logic_rules(facts7)  # Use loaded rules
        print(f"Result 7: {result7}")
        assert "has_feathers(eagle)" in result7["inferred_facts"]
        assert "is_warm_blooded(bear)" in result7["inferred_facts"]
        assert result7["consistency_check"] is True

        print("\n--- Test Case 8: Rule Loading with Contradiction from Config ---")
        core8 = M3LogicCore()
        config_rules_contradiction = [
            {"name": "human_mortal", "if": "is_human(X)", "then": "is_mortal(X)"},
            {
                "name": "human_immortal",
                "if": "is_human(X)",
                "then": "NOT is_mortal(X)",
            },  # Contradictory
        ]
        core8.load_rules(config_rules_contradiction)

        facts8 = ["is_human(plato)"]
        result8 = await core8.apply_logic_rules(facts8)
        print(f"Result 8: {result8}")
        assert result8["consistency_check"] is False
        assert len(result8["contradictions"]) > 0

    asyncio.run(main())
