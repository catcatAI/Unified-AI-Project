# =============================================================================
# ANGELA-MATRIX: [L4-L5] [β] [B] [L7]
# =============================================================================
"""研究管線：搜尋 → 來源排序 → 抓內文 → 抽關鍵事實 → 交叉比對 → 結構化答案。

audit 2026-10-18（第二輪）：六項修復後回應仍是「標題 — URL」連結快取——
DDG Lite HTML 明明有 10 個 ``result-snippet`` 儲存格但解析器硬寫
``snippet: ""``；抓內文/抽取/綜合三步在 gate 路徑不存在。本模組補齊：

1. **來源排序**：可信域（wiki/.gov/.edu/docs/官方路徑加分）浮頂、
   SEO/社群殼站沉底，標 高/中/低——「免費額度」該看官方定價頁。
2. **抓內文**：``fetch_page_text`` 共用文字抽取（script/style/標籤剝除），
   WebSearchAgent.fetch_content 與本管線同源。
3. **抽事實**：句切分＋查詢詞重疊打分＋數字加權，每頁取前 K 句。
4. **交叉比對**：跨來源「同單位不同數值」與「肯定 vs 否定標記」矛盾偵測。
5. **組答案**：關鍵事實 → 分歧 → 可信度排序來源清單（全部有出處）。

LLM 歸納（自然語言成文）在 chat_routes 層做——gate handler 保持無 LLM
依賴；LLM 不可用時本管線的抽取式答案即為終答（結構完整、可離線）。
"""

import logging
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# 可信域（預設；web_search config 的 trusted_domains 額外擴充）。
DEFAULT_TRUSTED: Tuple[str, ...] = (
    "wikipedia.org",
    "wikimedia.org",
    "github.com",
    "readthedocs.io",
    "python.org",
    "pythonhosted.org",
    "stackoverflow.com",
    "arxiv.org",
    "ietf.org",
    "mdn.io",
    "developer.mozilla.org",
    ".gov",
    ".edu",
)
# 社群/影片/SEO 殼站（預設；config 的 penalized_domains 額外擴充）。
DEFAULT_PENALIZED: Tuple[str, ...] = (
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "instagram.com",
    "pinterest.",
    "tiktok.com",
    "twitter.com",
    "x.com/",
    "quora.com",
)
# URL 路徑可信訊號：定價/官方文件頁優先（「免費額度」類問題的正確答案位）。
_TRUST_PATH_BONUS: Tuple[str, ...] = (
    "/pricing",
    "/price",
    "/docs",
    "/api",
    "/documentation",
    "/plans",
)

_STOPWORDS = frozenset(
    "the a an and or of for to in on at is are was were be vs versus how what "
    "why when who which with from by about 的 了 嗎 呢 請 幫 我 你 什麼 怎麼 有 沒 與 和".split()
)
# 數值聲明：數字（含千分位/小數）+ 可選單位詞（緊鄰或其後一詞）。
_NUM_RE = re.compile(
    r"(\d[\d,]*\.?\d*)\s*"
    r"(%|percent|usd|eur|ntd|k\b|m\b|million|billion|queries|tokens|次|美元|元|萬|亿|/month|/mo|per month)?",
    re.IGNORECASE,
)
# 肯定/否定語義矛盾標記（捕捉「已取消免費 vs 仍免費」這類非數值矛盾）。
_NEGATION_MARKERS = (
    "no longer",
    "removed",
    "discontinued",
    "eliminated",
    "ended",
    "取消",
    "已取消",
    "不再",
    "停止",
    "下架",
)
_AFFIRM_MARKERS = (
    "free tier",
    "free plan",
    "free of charge",
    "is free",
    "still free",
    "免費",
    "免费",
    "不收費",
    "免費額度",
)

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SENT_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])\s*|(?<=[a-z0-9\)\"'])\.\s+(?=[A-Z])|\n+")
# 殘標籤樣態（截斷/怪 markup 殘留）——這類句子不可當事實。
_TAGLIKE_RE = re.compile(r"</?\w+[\s>=]|<\w+$")
# JS/導航湯（未閉合 script 被 read cap 截斷時漏進正文；feature 列表非事實）
_SENT_JUNK_RE = re.compile(
    r"first paint|function\s*\(|\bconst\s+\w+\s*=|\bvar\s+\w+\s*=|=>\s*\{|"
    r"Features Web search|Human readable URLs",
    re.IGNORECASE,
)

_MAX_SENT_CHARS = 320
_DEFAULT_FETCH_K = 3
_DEFAULT_FETCH_TIMEOUT = 8.0
# 24KB read cap 曾把 brave.com 的 body/main 截掉（head>22KB → 剝完剩
# 238B 標題殘骸）——提高到 250KB 並在截斷時砍最後半標籤。
_MAX_PAGE_CHARS = 250_000
_MIN_TEXT_CHARS = 500  # 低於此視為無內文（SPA/挑戰頁），交給 snippet 兜底


def _load_web_search_config() -> dict:
    try:
        from core.system.config.tiered_loader import get_config

        ws = (get_config("system/llm") or {}).get("web_search", {})
        if isinstance(ws, dict):
            return ws
    except Exception:
        logger.debug("research_pipeline config read failed, using defaults", exc_info=True)
    return {}


# 定價意圖：pool 裡沒有定價/文件頁時，補一發「query pricing」重整搜尋。
_PRICING_INTENT = (
    "pricing",
    "price",
    "quota",
    "free tier",
    "rate limit",
    "定價",
    "價錢",
    "價格",
    "費用",
    "額度",
    "多少錢",
    "收費",
    "免費",
)
_PRICING_PATH = ("/pricing", "/plans", "/rate-limit", "/rate_limits", "api-dashboard", "/docs/")


def _is_pricing_source(url: str) -> bool:
    u = (url or "").lower()
    return any(p in u for p in _PRICING_PATH)


def _has_pricing_intent(query: str) -> bool:
    q = (query or "").lower()
    return any(k in q for k in _PRICING_INTENT)


def source_score(url: str, cfg: Optional[dict] = None) -> Tuple[int, str]:
    """(score, trust_label) — 分數越高越可信；標 高/中/低。"""
    cfg = cfg or {}
    url_l = (url or "").lower()
    if not url_l.startswith(("http://", "https://")):
        return -10, "低"
    trusted = tuple(cfg.get("trusted_domains") or ()) + DEFAULT_TRUSTED
    penalized = tuple(cfg.get("penalized_domains") or ()) + DEFAULT_PENALIZED
    score = 0
    for d in trusted:
        if d in url_l:
            score += 3 if d in ("wikipedia.org", ".gov", ".edu") else 2
            break
    for d in penalized:
        if d in url_l:
            score -= 4
            break
    path = urllib.parse.urlparse(url_l).path
    if any(p in path for p in _TRUST_PATH_BONUS):
        score += 2
    # 個人站/單頁殼弱化：.dev/.xyz/.info 且非已知可信域
    host = urllib.parse.urlparse(url_l).netloc
    if host.endswith((".xyz", ".info", ".click", ".top")):
        score -= 1
    if score >= 2:
        return score, "高"
    if score <= -1:
        return score, "低"
    return score, "中"


def rank_results(
    results: Sequence[Dict[str, Any]], cfg: Optional[dict] = None
) -> List[Dict[str, Any]]:
    """依來源可信度降序（穩定排序：同分保留原序——provider 已按相關性排）。"""
    cfg = cfg or {}
    decorated = []
    for i, r in enumerate(results):
        if not isinstance(r, dict) or r.get("error"):
            continue
        score, label = source_score(str(r.get("url", "")), cfg)
        item = dict(r)
        item["trust_score"] = score
        item["trust"] = label
        decorated.append((-score, i, item))  # -score → 降序
    decorated.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in decorated]


def fetch_page_text(
    url: str, timeout: float = _DEFAULT_FETCH_TIMEOUT, min_chars: int = _MIN_TEXT_CHARS
) -> Optional[str]:
    """抓 URL → 乾淨純文字（script/style/標籤剝除、空白收斂）。

    與 WebSearchAgent.fetch_content 同源邏輯（此為共用扼流點）；
    剝完文字短於 ``min_chars`` 視為無內文（SPA/bot 挑戰頁）回 None，
    失敗也回 None（不 raise——研究管線容錯）。
    """
    if not url or not url.lower().startswith(("http://", "https://")):
        return None
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; AngelaAI/7.5.0)"}
        )
        with urllib.request.urlopen(
            req, timeout=timeout
        ) as resp:  # nosec B310 - http(s) scheme guard above
            raw = resp.read(_MAX_PAGE_CHARS)
        if len(raw) >= _MAX_PAGE_CHARS:  # 截斷可能落在半個標籤中 → 砍最後 `<` 之後
            cut = raw.rfind(b"<")
            if cut > 0:
                raw = raw[:cut]
        text = raw.decode("utf-8", errors="replace")
        text = _TAG_RE.sub(" ", text)
        text = _ANY_TAG_RE.sub(" ", text)
        text = unescape(text)
        text = _WS_RE.sub(" ", text).strip()
        if len(text) < min_chars:
            return None
        return text or None
    except Exception as e:
        logger.debug("fetch_page_text failed for %s: %s", url, e)
        return None


def query_terms(query: str) -> List[str]:
    """查詢詞袋：拉丁詞（去停用）+ CJK 二元組。"""
    terms: List[str] = []
    for m in re.finditer(r"[a-z0-9][a-z0-9\-\.]{1,}", (query or "").lower()):
        w = m.group(0)
        if w not in _STOPWORDS and len(w) >= 2:
            terms.append(w)
    for m in re.finditer(r"[一-鿿]{1,}", query or ""):
        run = m.group(0)
        if len(run) == 1:
            if run not in _STOPWORDS:
                terms.append(run)
        else:
            for i in range(len(run) - 1):
                bg = run[i : i + 2]
                if bg not in _STOPWORDS:
                    terms.append(bg)
    # 去重保序
    seen = set()
    uniq: List[str] = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _split_sentences(text: str) -> List[str]:
    parts = _SENT_SPLIT_RE.split(text or "")
    out = []
    for p in parts:
        p = (p or "").strip()
        if 12 <= len(p) <= _MAX_SENT_CHARS:
            out.append(p)
    return out


_ENDS_SENTENCE = tuple(".。！？!?；;…\"'”’）)")


def extract_facts(text: str, terms: Sequence[str], max_facts: int = 3) -> List[str]:
    """句子打分：查詢詞重疊 + 數字加權；取前 max_facts。

    拒收：殘標籤句、疑問句（FAQ 標題非事實）、無句末標點的短殘片
    （「Compare Brave Search vs」類——實測曾佔滿事實清單）。
    """
    if not text or not terms:
        return []
    scored: List[Tuple[int, int, str]] = []
    for idx, sent in enumerate(_split_sentences(text)):
        if _TAGLIKE_RE.search(sent) or _SENT_JUNK_RE.search(sent):
            continue
        if sent.endswith(("?", "？")):
            continue  # 疑問句零資訊
        if not sent.endswith(_ENDS_SENTENCE) and len(sent) < 60:
            continue  # 無句末的短殘片（標題截斷）
        low = sent.lower()
        overlap = sum(1 for t in terms if t in low)
        if overlap == 0:
            continue
        score = overlap + (2 if _NUM_RE.search(sent) else 0)
        scored.append((-score, idx, sent))
    scored.sort()
    return [s for _, _, s in scored[:max_facts]]


def _numeric_claims(fact: str) -> List[Tuple[str, str]]:
    """[(value_normalized, unit)] — 值正規化（去逗號、小數規整）供跨源比對。"""
    claims = []
    for m in _NUM_RE.finditer(fact):
        raw_v, unit = m.group(1), (m.group(2) or "").lower()
        try:
            norm = f"{float(raw_v.replace(',', '')):g}"
        except ValueError:
            norm = raw_v
        if not unit:
            # 裸數字太噪——僅在帶單位時才算可比對聲明
            continue
        claims.append((norm, unit))
    return claims


def find_conflicts(facts_with_src: Sequence[Tuple[str, str]], terms: Sequence[str]) -> List[str]:
    """跨來源矛盾：①同單位不同數值；②否定 vs 肯定語義標記。

    facts_with_src: [(fact_text, source_host)]。回傳人讀矛盾描述（≤3 條）。
    """
    conflicts: List[str] = []
    # ① 數值矛盾：unit → {value: [host,...]}
    by_unit: Dict[str, Dict[str, List[str]]] = {}
    for fact, host in facts_with_src:
        for value, unit in _numeric_claims(fact):
            by_unit.setdefault(unit, {}).setdefault(value, []).append(host)
    for unit, values in by_unit.items():
        if len(values) >= 2:
            hosts = {h for hs in values.values() for h in hs}
            if len(hosts) >= 2:
                parts = []
                for v, hs in list(values.items())[:3]:
                    parts.append(f"{v}{unit}（{hs[0]}）")
                conflicts.append(f"數值不一致：{' vs '.join(parts)}")
    # ② 語義矛盾：一源否定、一源肯定、共享 ≥1 查詢詞
    term_set = set(terms)
    neg_facts = [f for f, _h in facts_with_src if any(m in f.lower() for m in _NEGATION_MARKERS)]
    aff_facts = [f for f, _h in facts_with_src if any(m in f.lower() for m in _AFFIRM_MARKERS)]
    if neg_facts and aff_facts:
        for nf in neg_facts:
            nl = nf.lower()
            if any(t in nl for t in term_set):
                conflicts.append(
                    f"來源互相矛盾：一端稱「{nf[:90]}」，另一端仍述免費（建議以官方定價頁為準）"
                )
                break
    return conflicts[:3]


def compose_answer(
    query: str,
    sources: Sequence[Dict[str, Any]],
    facts_with_src: Sequence[Tuple[str, str]],
    conflicts: Sequence[str],
    n_fetched: int,
    fetched_k: int,
) -> str:
    """結構化終答（抽取式；LLM 歸紀在其上層做）。開頭行是 e2e 契約。"""
    lines = [f"「{query}」的搜尋結果："]
    scope = f"（研究摘要：{n_fetched}/{fetched_k} 頁內文）" if n_fetched else "（來源摘要）"
    lines[0] = lines[0].replace("的搜尋結果：", f"的搜尋結果{scope}：")
    if facts_with_src:
        lines.append("【關鍵事實】")
        for f, src in facts_with_src[:8]:
            suffix = f"（{src}）" if src else ""
            lines.append(f"• {f}{suffix}")
    else:
        lines.append("【關鍵事實】（未能抓取內文；以下為來源清單，建議點開閱讀）")
    if conflicts:
        lines.append("【來源分歧】")
        for c in conflicts:
            lines.append(f"• {c}")
    if sources:
        lines.append("【來源（按可信度）】")
        for i, s in enumerate(sources[:5], 1):
            title = str(s.get("title", ""))[:80]
            url = s.get("url", "")
            lines.append(f"{i}. [{s.get('trust', '中')}] {title} — {url}")
    return "\n".join(lines)


def _research_payload(
    ok: bool,
    error: Optional[str] = None,
    answer: str = "",
    sources: Optional[List[Dict[str, Any]]] = None,
    facts: Optional[List[str]] = None,
    conflicts: Optional[List[str]] = None,
    n_fetched: int = 0,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "error": error,
        "answer": answer,
        "sources": sources or [],
        "facts": facts or [],
        "conflicts": conflicts or [],
        "n_fetched": n_fetched,
    }


def _pricing_reformulate(raw: List[Any], query: str, tool: Any) -> List[Any]:
    """定價意圖但 pool 無定價/文件頁 → 補「query pricing」（查詢重整，非造來源）。"""
    if not _has_pricing_intent(query):
        return raw
    if any(_is_pricing_source(str(r.get("url", ""))) for r in raw if isinstance(r, dict)):
        return raw
    try:
        extra = tool.search(f"{query} pricing", num_results=3)
    except Exception as e:
        logger.debug("pricing reformulation skipped: %s", e)
        return raw
    known = {str(r.get("url", "")) for r in raw if isinstance(r, dict)}
    added = [
        r
        for r in (extra or [])
        if isinstance(r, dict) and not r.get("error") and str(r.get("url", "")) not in known
    ]
    if not added:
        return raw
    logger.info("[Research] pricing reformulation added %d source(s)", len(added))
    return list(raw) + added


def _select_targets(sources: List[Dict[str, Any]], fetch_k: int) -> List[Dict[str, Any]]:
    """fetch 目標按 host 去重——zh/en 同域雙佔額會排擠其他來源。"""
    targets: List[Dict[str, Any]] = []
    seen_hosts = set()
    for s in sources:
        if len(targets) >= fetch_k:
            break
        if not s.get("url"):
            continue
        host = urllib.parse.urlparse(str(s["url"])).netloc
        if host in seen_hosts:
            continue
        seen_hosts.add(host)
        targets.append(s)
    return targets


def _fetch_texts(
    targets: Sequence[Dict[str, Any]], fetch_timeout: float
) -> Dict[int, Optional[str]]:
    texts: Dict[int, Optional[str]] = {}
    if not targets:
        return texts
    with ThreadPoolExecutor(max_workers=max(1, len(targets))) as pool:
        futs = {
            i: pool.submit(fetch_page_text, str(s["url"]), fetch_timeout)
            for i, s in enumerate(targets)
        }
        for i, fut in futs.items():
            try:
                texts[i] = fut.result()
            except Exception as e:  # pragma: no cover - fetch_page_text 已捕獲
                logger.debug("fetch worker error: %s", e)
                texts[i] = None
    return texts


def _collect_facts(
    targets: Sequence[Dict[str, Any]],
    texts: Dict[int, Optional[str]],
    sources: Sequence[Dict[str, Any]],
    terms: Sequence[str],
) -> Tuple[List[Tuple[str, str]], int]:
    """頁面事實（優先）＋全源 snippet 補缺；回 (facts_with_src, n_fetched)。

    snippet 全源參與：搜尋引擎已判定與查詢最相關（定價類事實常只在
    未抓成頁面的 snippet 裡——實測 2026-10-18），抓取失敗時為唯一線索。
    """
    facts: List[str] = []
    facts_with_src: List[Tuple[str, str]] = []
    n_fetched = 0
    for i, s in enumerate(targets):
        text = texts.get(i)
        if not text:
            continue
        n_fetched += 1
        host = urllib.parse.urlparse(str(s["url"])).netloc
        for f in extract_facts(text, terms, max_facts=3):
            if f not in facts:
                facts.append(f)
                facts_with_src.append((f, host))
    for s in sources:
        snip = str(s.get("snippet") or "").strip()
        if not snip or len(facts) >= 8:
            continue
        host = urllib.parse.urlparse(str(s.get("url", ""))).netloc
        for f in extract_facts(snip, terms, max_facts=2):
            if f in facts:
                continue
            facts.append(f)
            facts_with_src.append((f, host))
            if len(facts) >= 8:
                break
    return facts_with_src, n_fetched


def run_research(
    query: str,
    tool: Any = None,
    fetch_k: Optional[int] = None,
    fetch_timeout: Optional[float] = None,
    num_results: int = 5,
) -> Dict[str, Any]:
    """搜尋 + 來源排序 + 並發抓內文 + 抽事實 + 交叉比對 + 組答案。

    回 dict：{ok, error, answer, sources, facts, conflicts, n_fetched}。
    ``tool=None`` 時自建 WebSearchTool；fetcher 可用
    ``monkeypatch research_pipeline.fetch_page_text`` 注入（測試）。
    """
    cfg = _load_web_search_config()
    if fetch_k is None:
        fetch_k = int(cfg.get("research_fetch_k", _DEFAULT_FETCH_K))
    if fetch_timeout is None:
        fetch_timeout = float(cfg.get("research_fetch_timeout", _DEFAULT_FETCH_TIMEOUT))
    if tool is None:
        from core.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()
    try:
        raw = tool.search(query, num_results=num_results)
    except Exception as e:
        logger.warning("run_research tool search failed: %s", e, exc_info=True)
        return _research_payload(False, error=str(e))
    if not raw:
        return _research_payload(True)
    if all(isinstance(r, dict) and r.get("error") for r in raw):
        return _research_payload(False, error=raw[0].get("error"))

    raw = _pricing_reformulate(raw, query, tool)
    sources = rank_results(raw, cfg)
    targets = _select_targets(sources, fetch_k)
    terms = query_terms(query)
    texts = _fetch_texts(targets, fetch_timeout)
    facts_with_src, n_fetched = _collect_facts(targets, texts, sources, terms)
    conflicts = find_conflicts(facts_with_src, terms)
    answer = compose_answer(query, sources, facts_with_src, conflicts, n_fetched, len(targets))
    facts = [f for f, _ in facts_with_src]
    logger.info(
        "[Research] query=%r sources=%d fetched=%d facts=%d conflicts=%d",
        query,
        len(sources),
        n_fetched,
        len(facts),
        len(conflicts),
    )
    return _research_payload(
        True,
        answer=answer,
        sources=sources,
        facts=facts,
        conflicts=conflicts,
        n_fetched=n_fetched,
    )


__all__ = [
    "run_research",
    "rank_results",
    "source_score",
    "fetch_page_text",
    "query_terms",
    "extract_facts",
    "find_conflicts",
    "compose_answer",
]
