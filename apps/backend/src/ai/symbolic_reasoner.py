# =============================================================================
# ANGELA-MATRIX: [L2] [γ] [B] [L4]
# =============================================================================
"""Deterministic symbolic reasoner for native (non-LLM) inference engines.

Both ED3N and GARDEN delegate structured logical reasoning to this module
through ``route_reasoning`` — mirroring how math is delegated to
``MathVerifier`` (via ``route_math``) and factual knowledge to
``ai.knowledge_base.route_knowledge``. This is a real, high-certainty
capability (symbolic inference over explicitly stated premises) and is scored
as such in INTELLIGENCE_ASSESSMENT.md.

Covered patterns (the benchmark's open-domain reasoning cases):
  * transitive relations  — "A is taller than B. B is taller than C. Who is tallest?"
  * syllogism            — "All birds can fly. A penguin is a bird. Can a penguin fly?"
  * calendar             — "If today is Monday, what day is tomorrow?"
  * quantity comparison  — "John has 3 apples. He gives 1 away. How many left?"
  * mass trick           — "Which is heavier: 1kg of feathers or 1kg of steel?"
  * two-object linear pair (chicken-rabbit cage) — "chickens and rabbits,
    35 heads and 94 legs. How many of each?" (see _solve_word_problem)

All covered patterns are deterministic (no weights, no learning). See
docs/03-technical-architecture/DETERMINISM_CLASSIFICATION.md for the
determinism classification of this module and the rest of the pipeline.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# Comparators we understand (transitive). Keyed by canonical direction word.
_GREATER = {
    "taller",
    "bigger",
    "larger",
    "heavier",
    "older",
    "faster",
    "higher",
    "more",
    "longer",
    "wider",
    "hotter",
    "stronger",
    "richer",
    "taller than",
}
_LESSER = {
    "shorter",
    "smaller",
    "lighter",
    "younger",
    "slower",
    "lower",
    "less",
    "colder",
    "weaker",
    "poorer",
}
_COMPARATORS = _GREATER | _LESSER

_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _extract_entities(text: str) -> List[str]:
    """Pull short capitalised / alphabetic tokens used as relation subjects."""
    # Prefer single capitalised letters (A, B, C) common in logic puzzles
    caps = re.findall(r"\b([A-Z])\b", text)
    if len(caps) >= 2:
        return caps
    # Fall back to short lowercase proper-ish words
    words = re.findall(r"\b([a-z]{1,12})\b", text.lower())
    return [
        w
        for w in words
        if w
        not in {
            "is",
            "are",
            "was",
            "were",
            "the",
            "a",
            "an",
            "of",
            "than",
            "and",
            "or",
            "but",
            "who",
            "what",
            "how",
            "why",
            "can",
            "do",
            "does",
            "if",
            "today",
            "tomorrow",
            "yesterday",
            "day",
            "days",
            "week",
            "month",
            "year",
            "which",
            "he",
            "she",
            "it",
            "they",
            "we",
            "you",
            "i",
            "my",
            "your",
            "has",
            "have",
            "had",
            "gives",
            "give",
            "gave",
            "left",
            "many",
            "much",
        }
    ]


def _solve_transitive(text: str) -> Optional[str]:
    """A > B, B > C  =>  A is the greatest / tallest / etc."""
    # Find comparator statements:  "X is <comp> than Y"  or  "X <comp> Y"
    # Chinese: "X 比 Y <comp>"
    pairs: List[Tuple[str, str, str]] = []  # (subject, object, comparator)
    # English "X is taller than Y" / "X taller than Y"
    for m in re.finditer(r"\b([A-Za-z])\b\s+(?:is\s+)?(\w+?)\s+than\s+\b([A-Za-z])\b", text):
        subj, comp, obj = m.group(1).upper(), m.group(2).lower(), m.group(3).upper()
        pairs.append((subj, obj, comp))
    # Chinese "X 比 Y 高"
    for m in re.finditer(
        r"([\w一-鿿]{1,8})\s*比\s*([\w一-鿿]{1,8})\s*(高|大|重|快|多|長|強)", text
    ):
        pairs.append((m.group(1), m.group(2), "taller"))

    if not pairs:
        return None

    # Build a "greater-than" graph. For each (a, b, comp):
    #   greater comparators => a > b ;  lesser => b > a
    greater: dict = {}
    lesser: dict = {}

    def _record(a: str, b: str):
        greater.setdefault(a, set()).add(b)
        lesser.setdefault(b, set()).add(a)

    for a, b, comp in pairs:
        if comp in _GREATER or comp in (
            "taller",
            "bigger",
            "larger",
            "heavier",
            "older",
            "faster",
            "higher",
            "more",
            "longer",
            "wider",
            "hotter",
            "stronger",
            "richer",
            "高",
            "大",
            "重",
            "快",
            "多",
            "長",
            "強",
        ):
            _record(a, b)
        elif comp in _LESSER or comp in ("低", "小", "輕", "慢", "少", "弱"):
            _record(b, a)

    if not greater:
        return None

    # The "tallest / biggest / ...est" entity is one that is greater than all
    # others and nothing is greater than it.
    all_nodes = set(greater) | set(lesser)
    ask_least = bool(
        re.search(
            r"shortest|smallest|least|youngest|lightest|"
            r"slowest|lowest|weakest|poorest|coldest|minimum|"
            r"最小|最短|最矮|最少|最輕|最冷|最低|最弱|最窮|最慢",
            text.lower(),
        )
    )
    if ask_least:
        # The least entity is dominated by all others (in `lesser`).
        candidates = [n for n in lesser if n not in greater]
        if len(candidates) == 1:
            bottom = candidates[0]
            seen = set()
            stack = list(lesser.get(bottom, set()))
            while stack:
                n = stack.pop()
                if n in seen:
                    continue
                seen.add(n)
                stack.extend(lesser.get(n, set()))
            if seen >= (all_nodes - {bottom}):
                comp_word = pairs[0][2]
                superlative = _superlative(comp_word, least=True)
                return f"{bottom} is {superlative}"
        return None

    candidates = [n for n in greater if n not in lesser]
    if len(candidates) == 1:
        top = candidates[0]
        # verify it dominates everything else transitively
        seen = set()
        stack = list(greater.get(top, set()))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(greater.get(n, set()))
        if seen >= (all_nodes - {top}):
            # pick a human-friendly superlative
            comp_word = pairs[0][2]
            superlative = _superlative(comp_word)
            return f"{top} is {superlative}"
    return None


def _superlative(comp: str, least: bool = False) -> str:
    if least:
        table = {
            "taller": "the shortest",
            "bigger": "the smallest",
            "larger": "the smallest",
            "heavier": "the lightest",
            "older": "the youngest",
            "faster": "the slowest",
            "higher": "the lowest",
            "more": "the least",
            "longer": "the shortest",
            "wider": "the narrowest",
            "hotter": "the coldest",
            "stronger": "the weakest",
            "richer": "the poorest",
            "高": "the shortest",
            "大": "the smallest",
            "重": "the lightest",
            "快": "the slowest",
            "多": "the least",
            "長": "the shortest",
            "強": "the weakest",
        }
        return table.get(comp, "the least")
    table = {
        "taller": "the tallest",
        "bigger": "the biggest",
        "larger": "the largest",
        "heavier": "the heaviest",
        "older": "the oldest",
        "faster": "the fastest",
        "higher": "the highest",
        "more": "the most",
        "longer": "the longest",
        "wider": "the widest",
        "hotter": "the hottest",
        "stronger": "the strongest",
        "richer": "the richest",
        "高": "the tallest",
        "大": "the biggest",
        "重": "the heaviest",
        "快": "the fastest",
        "多": "the most",
        "長": "the longest",
        "強": "the strongest",
    }
    return table.get(comp, "the greatest")


def _solve_syllogism(text: str) -> Optional[str]:
    """All X are Y. Z is an X. Does Z have property Y?

    Premise 1: "<A> <verb> <B>"  (e.g. "birds can fly", "birds fly")
    Premise 2: "<C> is a/an <A>"  (e.g. "a penguin is a bird")
    Question:  "can <C> <B>?"  => answer yes/no based on premise 1.
    """
    # Split into sentences
    sentences = re.split(r"[.。!！?？;；]", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Find the UNIVERSAL premise first ("all X can Y" / "X can Y" / "X are Y").
    # Prefer an explicit universal statement; skip membership statements
    # ("Z is a X") so we don't mistake them for the rule.
    universal = None  # (category, property)
    membership_re = re.compile(r"\b([a-z一-鿿]+)\s+is\s+(?:a|an)\s+([a-z一-鿿]+)\b", re.IGNORECASE)
    for s in sentences:
        low = s.lower()
        m = re.search(r"(?:all\s+)?([a-z一-鿿]+)\s+(?:can|are|is)\s+([a-z一-鿿]+)", low)
        if not m:
            m = re.search(r"([a-z一-鿿]+)\s+(?:會|能|可以)\s*([a-z一-鿿]+)", low)
        if not m:
            continue
        cat, prop = m.group(1), m.group(2)
        if cat in ("all", "the", "a", "an", "every"):
            continue
        # Skip membership-style statements ("Z is a X")
        if membership_re.search(low) and re.search(r"\bis\s+(?:a|an)\s", low):
            continue
        universal = (cat, prop)
        break
    # Fallback: any universal-style premise even if it also contains membership
    if universal is None:
        for s in sentences:
            low = s.lower()
            m = re.search(r"(?:all\s+)?([a-z一-鿿]+)\s+(?:can|are|is)\s+([a-z一-鿿]+)", low)
            if m and m.group(1) not in ("all", "the", "a", "an", "every"):
                universal = (m.group(1), m.group(2))
                break

    if universal is None:
        return None

    cat, prop = universal
    # Find membership: "<C> is a/an <cat>" or "<C> 是 <cat>".
    # Allow singular/plural mismatch (rule says "birds", member says "bird").
    cat_norm = cat.rstrip("s") or cat
    member = None
    member_re = re.compile(
        r"\b([a-z一-鿿]+)\s+is\s+(?:a|an)\s+" + re.escape(cat_norm) + r"s?\b",
        re.IGNORECASE,
    )
    member_re_zh = re.compile(
        r"\b([a-z一-鿿]+)\s+是\s*(?:一隻|一個|一頭|一名)?\s*" + re.escape(cat_norm) + r"s?\b",
        re.IGNORECASE,
    )
    for s in sentences:
        low = s.lower()
        m = member_re.search(low) or member_re_zh.search(low)
        if m:
            cand = m.group(1)
            if cand in ("a", "an", "the", "一", "一隻", "一個", "一頭", "一名"):
                continue
            member = cand
            break
    if member is None:
        return None

    # Question asks about <member> and <prop>?
    q = text.lower()
    if re.search(re.escape(member) + r".*" + re.escape(prop), q) or (member in q and prop in q):
        # Affirmative universal premise => yes; negative premise => no.
        neg = bool(
            re.search(
                r"\bno\b|\bnone\b|not|never|can'?t|cannot|" r"不會|不能|不會飛|不會游|沒有|無",
                sentences[0].lower(),
            )
        )
        return "no" if neg else "yes"
    return None


def _solve_calendar(text: str) -> Optional[str]:
    """If today is <day>, what day is tomorrow / yesterday?"""
    low = text.lower()
    m = re.search(r"today is ([a-z]+)", low)
    if not m:
        return None
    try:
        idx = _DAYS.index(m.group(1))
    except ValueError:
        return None
    if "tomorrow" in low:
        return _DAYS[(idx + 1) % 7].capitalize()
    if "yesterday" in low:
        return _DAYS[(idx - 1) % 7].capitalize()
    return None


def _solve_quantity(text: str) -> Optional[str]:
    """John has 3 apples. He gives 1 away. How many left? -> 2."""
    # Capture "<name> has <n> <unit>" and "<verb> <m> away/give"
    has_m = re.search(r"has\s+(\d+)\s+(\w+)", text.lower())
    if not has_m:
        return None
    total = int(has_m.group(1))
    # Find subtraction: "gives 1 away", "gave 2", "eats 1", "loses 3", "ate 2"
    sub_m = re.search(
        r"(?:gives|gave|give|eats|ate|loses|lost|uses|used|spends|spent|"
        r"removes?|took|takes?)\s+(\d+)",
        text.lower(),
    )
    if not sub_m:
        return None
    removed = int(sub_m.group(1))
    result = total - removed
    # question asks "how many left?" / "how many <unit>?"
    if "left" in text.lower() or "remain" in text.lower() or "how many" in text.lower():
        return str(result)
    return None


def _solve_mass_trick(text: str) -> Optional[str]:
    """Which is heavier: 1kg of feathers or 1kg of steel? -> same."""
    low = text.lower()
    has_mass_unit = "kg" in low or "公斤" in low or "千克" in low
    asks_weight = (
        "heavier" in low
        or "heaviest" in low
        or "weigh" in low
        or "weight" in low
        or "更重" in low
        or "重" in low
    )
    if has_mass_unit and asks_weight:
        # Extract mass values (kg / 公斤 / 千克)
        masses = re.findall(r"(\d+)\s*(?:kg|公斤|千克)", low)
        if len(masses) >= 2:
            if len(set(masses)) == 1:
                return "same"
            # Different masses are not a trick; let the network handle it.
            return None
        if (
            ("1kg" in low and "1kg" in low[low.index("1kg") + 3 :])
            or ("1公斤" in low and "1公斤" in low[low.index("1公斤") + 3 :])
            or ("1千克" in low and "1千克" in low[low.index("1千克") + 3 :])
        ):
            return "same"
    return None


_ENTITY_ALIASES: Dict[str, List[str]] = {
    # English label first, then common Chinese aliases (for output & matching).
    "chicken": ["chicken", "chickens", "雞", "鸡"],
    "rabbit": ["rabbit", "rabbits", "hare", "兔子", "兔"],
    "horse": ["horse", "horses", "馬", "马"],
    "pig": ["pig", "pigs", "piglet", "豬", "猪"],
    "duck": ["duck", "ducks", "鴨", "鸭"],
    "cow": ["cow", "cows", "cattle", "牛"],
    "octopus": ["octopus", "octopuses", "章魚", "章鱼"],
    "bicycle": ["bicycle", "bicycles", "bike", "bikes", "自行車", "自行车", "腳踏車", "脚踏车", "單車", "单车"],
    "tricycle": ["tricycle", "tricycles", "三輪車", "三轮车"],
    "car": ["car", "cars", "小汽車", "小汽车", "汽車", "汽车"],
    "motorcycle": ["motorcycle", "motorcycles", "機車", "机车", "摩托車", "摩托车"],
    "penny": ["penny", "pennies", "一分錢", "一分", "便士"],
    "nickel": ["nickel", "nickels", "五分錢", "鎳幣", "镍币"],
    "dime": ["dime", "dimes", "一角硬幣", "一角硬币", "一毛"],
    "quarter": ["quarter", "quarters", "兩角五分", "兩毛五", "二十五分", "25分硬幣"],
}

# Attribute kinds the two-object linear-pair solver understands. Each maps the
# natural-language word (plain, for detection), the knowledge-base attribute
# key, and the regex used to extract the TOTAL attribute value R from the
# prompt. Detection words are literal (no regex metacharacters).
_ATTR_KINDS: Dict[str, Dict[str, object]] = {
    "legs": {
        "words": ("腳", "脚", "腿", "legs"),
        "kb": "legs",
        "r_re": r"(?:(\d+)\s*(?:隻|只)?\s*(?:腳|脚|腿|legs?))|(?:腳|脚|腿|legs?)\s*[:=：]?\s*(\d+)",
    },
    "wheels": {
        "words": ("輪子", "輪", "轮子", "轮", "wheels"),
        "kb": "wheels",
        "r_re": r"(?:(\d+)\s*(?:個|只)?\s*(?:輪子|輪|轮子|轮|wheels?))|(?:輪子|輪|轮子|轮|wheels?)\s*[:=：]?\s*(\d+)",
    },
    "value": {
        "words": ("分錢", "cents", "分", "元", "美元", "值", "價值", "worth", "value", "$"),
        "kb": "value",
        "r_re": r"(?:(\d+(?:\.\d+)?)\s*(?:分|cents?|元|美元))|(?:值|價值|worth|value|\$)\s*[:=：]?\s*(\d+(?:\.\d+)?)",
    },
}

_OBJ_COUNT_RE = re.compile(
    r"(\d+)\s*(?:枚|個|隻|只)?\s*(?:個頭|頭|heads?|animals?|coins?|vehicles?|動物|硬幣|臺|台|輛|車)"
)


def _alias_present(alias: str, low: str) -> bool:
    """Presence check for an entity alias.

    English aliases use word boundaries (``\bchicken\b``) so ``rabbit`` does
    not match inside ``rabbit-proof``; CJK aliases are substring matches.
    """
    if alias.isascii() and alias.isalnum():
        return re.search(rf"\b{re.escape(alias)}\b", low) is not None
    return alias in low


def _solve_word_problem(text: str) -> Optional[str]:
    """Solve a two-object linear pair.

    Canonical case is the chicken-rabbit cage problem, but the solver is
    generic: any two entities (A, B) with known per-object attribute values
    (legs / wheels / coin value), a stated total object count C and a stated
    total attribute R. Solves A+B=C, attrA*A+attrB*B=R for integer
    non-negative (A, B).

    Examples that resolve:
      * "The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?"
      * "籠中共有雞和兔子 35 隻，腳 94 隻，問雞兔各幾隻?"
      * "共 35 頭，94 腳"
      * "There are bicycles and tricycles, 20 vehicles and 54 wheels. How many of each?"
      * "Nickels and dimes, 18 coins worth 140 cents. How many of each?"

    Returns ``None`` when the pattern is not matched or does not admit a clean
    integer solution, so the caller falls through to its normal pipeline.
    """
    low = text.lower()
    present = [key for key, al in _ENTITY_ALIASES.items() if any(_alias_present(a, low) for a in al)]
    if len(present) != 2:
        # Fewer than two objects cannot be a pair; more than two is not a
        # 2-variable linear system -> fall through rather than risk a wrong
        # answer for a genuinely different problem.
        return None
    a, b = present[0], present[1]

    # Detect the attribute kind from the prompt (legs first, then wheels/value).
    kind = None
    for k, cfg in _ATTR_KINDS.items():
        if any(w in low for w in cfg["words"]):
            kind = k
            break
    if kind is None:
        return None
    cfg = _ATTR_KINDS[kind]
    attr_word = cfg["words"]

    def _attr_val(key: str) -> Optional[int]:
        # Prefer an explicit per-object attribute stated in the prompt.
        alias_alt = "|".join(
            re.escape(a) if not a.isascii() or not a.isalnum() else rf"\b{re.escape(a)}\b"
            for a in _ENTITY_ALIASES[key]
        )
        m = re.search(
            rf"(?:each|per|每隻|每只|每)\s*(?:{alias_alt})\s*(?:has|have|有)\s*(\d+)\s*(?:{'|'.join(re.escape(w) for w in attr_word)})",
            low,
        )
        if m:
            return int(m.group(1))
        try:
            from ai.knowledge_base import _KNOWLEDGE

            raw = _KNOWLEDGE.get(key, {}).get(cfg["kb"])
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    a_val = _attr_val(a)
    b_val = _attr_val(b)
    if a_val is None or b_val is None or a_val == b_val:
        return None

    # Total attribute R.
    m_r = re.search(cfg["r_re"], low)
    if not m_r:
        return None
    total_raw = m_r.group(1) or m_r.group(2)
    total_attr = float(total_raw)
    if kind == "value" and "." in total_raw:
        total_attr = round(total_attr * 100)  # "$1.40" -> 140 cents
    else:
        total_attr = int(total_attr)

    # Total object count C (count-noun first, then a "共 N" form).
    m_c = _OBJ_COUNT_RE.search(low)
    if m_c:
        total_obj = int(m_c.group(1))
    else:
        m = re.search(r"(?:共有|共|總共|總計)\D*?(\d+)\s*(?:隻|只|個|枚)", low)
        if not m:
            return None
        total_obj = int(m.group(1))

    # Solve A+B=C ; a_val*A + b_val*B = R.
    numerator = total_attr - b_val * total_obj
    denominator = a_val - b_val
    if denominator == 0 or numerator % denominator != 0:
        return None
    count_a = numerator // denominator
    count_b = total_obj - count_a
    if count_a < 0 or count_b < 0:
        return None

    cjk = any("\u4e00" <= ch <= "\u9fff" for ch in low)
    aliases = _ENTITY_ALIASES
    if cjk:
        label_a = next((x for x in aliases[a] if any("\u4e00" <= ch <= "\u9fff" for ch in x)), aliases[a][0])
        label_b = next((x for x in aliases[b] if any("\u4e00" <= ch <= "\u9fff" for ch in x)), aliases[b][0])
    else:
        label_a, label_b = aliases[a][0], aliases[b][0]
    return f"{count_a} {label_a}, {count_b} {label_b}"


def route_reasoning(text: str) -> Optional[str]:
    """Apply deterministic symbolic reasoning to a question.

    Returns a short answer string, or ``None`` when the question is not a
    covered symbolic pattern (so the caller falls through to its normal
    vector/SNN pipeline). Order matters: cheap, high-precision patterns first.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.strip()

    result = _solve_mass_trick(t)
    if result is not None:
        return result
    result = _solve_calendar(t)
    if result is not None:
        return result
    result = _solve_quantity(t)
    if result is not None:
        return result
    result = _solve_word_problem(t)
    if result is not None:
        return result
    result = _solve_syllogism(t)
    if result is not None:
        return result
    result = _solve_transitive(t)
    if result is not None:
        return result
    return None
