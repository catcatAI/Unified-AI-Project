"""Offline relational-chain reasoning (shared by ED3N and GARDEN).

This provides a deterministic, parser-driven transitive-closure resolver for
relational comparison questions such as::

    "X is warmer than Y. Y is warmer than Z. Who is warmest?"

The resolver builds a directed "greater-than" graph from the *explicitly stated*
comparisons in the query (no pre-trained associations, no LLM, no torch) and
asks a backend ``resolve_relational_chain`` method to resolve the dominant or
least entity. It complements the regex-based symbolic reasoner by handling novel
comparators and paraphrases that the fixed patterns do not match.
"""

from typing import Callable, Dict, List, Optional, Set, Tuple

# A resolver takes (edges, entities, ask_max) and returns the resolved entity
# string or None. Both CoreNetwork (ED3N) and TensorSNNCore (GARDEN) provide one.
ChainResolver = Callable[
    [List[Tuple[str, str, float]], List[str], bool], Optional[str]
]

_COMPARISON_RE = __import__("re").compile(
    r"\b([A-Za-z一-鿿]{1,20})\s+(?:is\s+)?(taller|shorter|bigger|smaller|larger|"
    r"heavier|lighter|older|younger|faster|slower|hotter|colder|warmer|"
    r"cooler|richer|poorer|stronger|weaker|higher|lower|longer|wider|"
    r"大|小|高|矮|重|輕|快|慢|熱|冷|溫|暖|富|窮|強|弱|長|寬)\s+"
    r"(?:than|then|to)?\s*([A-Za-z一-鿿]{1,20})\b",
    __import__("re").IGNORECASE,
)

# Comparators that express the *lesser* direction (reverse the edge).
_LESSER_COMPARATORS = {
    "shorter", "smaller", "lighter", "younger", "slower",
    "colder", "cooler", "poorer", "weaker", "lower", "wider",
    "小", "矮", "輕", "慢", "冷", "窮", "弱", "低", "寬", "長",
}

# Question keywords that ask for the *least* entity rather than the greatest.
_LEAST_KEYWORDS = (
    "shortest", "smallest", "least", "youngest", "lightest",
    "coldest", "lowest", "weakest", "poorest", "slowest",
    "最小", "最短", "最矮", "最少", "最輕", "最冷", "最低",
    "最弱", "最窮", "最慢",
)


def parse_comparison_edges(text: str) -> Tuple[List[Tuple[str, str, float]], List[str]]:
    """Parse explicit comparison statements from ``text``.

    Returns a tuple ``(edges, entities)`` where each edge is
    ``(subject, object, weight)`` with ``weight > 0`` meaning "subject is
    greater in the compared dimension" and ``weight < 0`` meaning the reverse
    (a lesser comparator). ``entities`` lists all mentioned entity names in
    order of appearance.
    """
    edges: List[Tuple[str, str, float]] = []
    entities: List[str] = []
    for m in _COMPARISON_RE.finditer(text):
        a, comp, b = m.group(1), m.group(2).lower(), m.group(3)
        if a in ("is", "are", "was", "the", "a", "an"):
            continue
        entities.extend([a, b])
        w = -1.0 if comp in _LESSER_COMPARATORS else 1.0
        edges.append((a, b, w))
    return edges, entities


def ask_direction(text: str) -> bool:
    """Return True if the query asks for the *greatest* entity, False for least."""
    q = text.lower()
    return not any(kw in q for kw in _LEAST_KEYWORDS)


def parse_and_resolve_relational_chain(
    text: str,
    resolver: ChainResolver,
    comp_word_greatest: str = "the greatest",
    comp_word_least: str = "the least",
) -> Optional[str]:
    """Parse ``text`` and resolve a relational chain via ``resolver``.

    Returns a natural-language answer string (e.g. ``"X is the greatest"``) or
    None if no relational structure is present or the chain is ambiguous.
    """
    edges, entities = parse_comparison_edges(text)
    if not edges:
        return None
    ask_max = ask_direction(text)
    sol = resolver(edges, entities, ask_max=ask_max)
    if sol is None:
        return None
    comp_word = comp_word_greatest if ask_max else comp_word_least
    return f"{sol} is {comp_word}"


def resolve_relational_chain(
    edges: List[Tuple[str, str, float]],
    query_entities: List[str],
    ask_max: bool = True,
) -> Optional[str]:
    """Resolve a transitive relational chain over explicitly stated edges.

    A genuine multi-hop graph derivation (transitive closure), independent of
    any pre-trained associations. Used as a fallback when the deterministic
    symbolic reasoner does not match a query but the query itself states a
    relational structure (e.g. "X warmer than Y, Y warmer than Z, who warmest?").

    Args:
        edges: List of ``(subject, object, weight>0)`` directed comparisons where
               a larger weight means "subject is greater in the compared
               dimension". For a "lesser" comparator the edge is reversed by the
               caller (weight < 0).
        query_entities: Candidate entity names appearing in the question.
        ask_max: If True resolve the entity that dominates all others (greatest);
                 if False resolve the least (smallest).

    Returns:
        The resolved entity string, or None if no unique solution.
    """
    if not edges or not query_entities:
        return None

    greater: Dict[str, Set[str]] = {}
    lesser: Dict[str, Set[str]] = {}
    all_nodes: Set[str] = set()

    def _record(a: str, b: str) -> None:
        greater.setdefault(a, set()).add(b)
        lesser.setdefault(b, set()).add(a)
        all_nodes.add(a)
        all_nodes.add(b)

    for a, b, w in edges:
        if w > 0:
            _record(a, b)
        elif w < 0:
            _record(b, a)

    if not greater:
        return None

    candidates = [n for n in query_entities if n in all_nodes]
    if not candidates:
        candidates = list(all_nodes)

    def _dominates(node: str, others: Set[str]) -> bool:
        seen: Set[str] = set()
        stack = list(greater.get(node, set()))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(greater.get(n, set()))
        return others.issubset(seen | {node})

    def _dominated_by_all(node: str, others: Set[str]) -> bool:
        seen: Set[str] = set()
        stack = list(lesser.get(node, set()))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(lesser.get(n, set()))
        return others.issubset(seen | {node})

    if ask_max:
        sols = [n for n in candidates if _dominates(n, all_nodes - {n})]
    else:
        sols = [n for n in candidates if _dominated_by_all(n, all_nodes - {n})]

    return sols[0] if len(sols) == 1 else None
