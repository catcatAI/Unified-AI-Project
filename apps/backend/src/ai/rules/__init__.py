"""Verified solution rules: 複雜問題解一次，驗證過的答案重複使用免重算。

Admission requires deterministic verification (FunSearch 的「易驗證、難求解」
門檻), serving is exact-identity replay with a confidence gate.
"""

from .solution_rules import (
    RuleStore,
    SolutionRule,
    canonical_key,
    get_rule_store,
    is_dynamic_query,
    verify_solution,
)

__all__ = [
    "RuleStore",
    "SolutionRule",
    "canonical_key",
    "get_rule_store",
    "is_dynamic_query",
    "verify_solution",
]
