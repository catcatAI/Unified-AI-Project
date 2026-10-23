"""人話標準（human-speech rubric）— 可裁決的規則，不是感覺。

這份標準回答一個問題：**一個回答算不算「像人說的」？** 判準必須是可覆核的
規則，否則「會說人話」只是形容詞。

**答案狀態**（借自人類的認知分層，用來描述一個回答的認知位置）：

| 狀態 | 意思 |
| --- | --- |
| `correct` | 事實正確：在題目的條件下，斷言成立 |
| `approximate` | 近似正確：日常經驗成立，但省略了邊界條件 |
| `subjective` | 主觀正確：對某個主體成立，但不是普遍事實 |
| `exception_aware` | 例外：明確指出邊界/例外（=「最正確」的結構） |
| `false` | 錯誤：斷言不成立 |
| `non_compliant` | 不符合：答非所問（對象錯置／不相干） |
| `parrot` | 鸚鵡捲舌：把問題回來，沒有新增資訊 |
| `template` | 罐頭：固定句，與輸入無關 |
| `empty` | 空白 |
| `abstain` | 誠實棄權：明說不知道（**不是**答錯，是誠實） |

**人話標準（通過條件）**：一個回答要算「像人說的」，六條全要成立：

1. `addresses` 回答了問題（不是回聲、不是固定句、不是空白）
2. `correct_or_qualified` 斷言是對的，或明確標示了條件/不確定（近似或主觀可接受）
3. `boundary_aware` 題目有邊界條件時，回答**指出了邊界/例外**（這是「最正確」
   與「近似正確」的差別）
4. `grounded` 內容有根據（引用了已知的東西／使用者自己的話），不是編造的
5. `not_parrot` 不是把問題或固定模板回來
6. `not_degenerate` 沒有亂碼、沒有黏句、沒有模板殘留

**多重事實**：只會回答單一事實的系統還不能算「會說人話」——對話裡同時有多個
事實時，必須能**組合**（問 A 時不該帶出 B）、**更正**（使用者改口時要跟著改）、
**分辨主體**（誰說的）。標準集裡有專門的多重事實情境，這三條是另外裁決的。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------- #
# The answer states
# --------------------------------------------------------------------------- #
CORRECT = "correct"
APPROXIMATE = "approximate"
SUBJECTIVE = "subjective"
EXCEPTION_AWARE = "exception_aware"
FALSE = "false"
NON_COMPLIANT = "non_compliant"
PARROT = "parrot"
TEMPLATE = "template"
EMPTY = "empty"
ABSTAIN = "abstain"

# The states that count as "an answer with content".
CONTENT_STATES = (CORRECT, APPROXIMATE, SUBJECTIVE, EXCEPTION_AWARE)

# --------------------------------------------------------------------------- #
# The criteria
# --------------------------------------------------------------------------- #
CRITERIA = (
    "addresses",
    "correct_or_qualified",
    "boundary_aware",
    "grounded",
    "not_parrot",
    "not_degenerate",
)

# The markers of the honest abstention.
_ABSTAIN = re.compile(
    r"don't have enough knowledge|can't complete this task|no language model is available"
    r"|還沒有足夠的知識|目前還做不到|目前做不到|無法回答這個問題|沒有可用的語言模型"
    r"|不知道|不確定|沒把握",
    re.IGNORECASE,
)
# The markers of a hedge ("在標準大氣壓下", "一般來說", "我的經驗") — a hedge is
# what turns "false" into "approximate"/"subjective".
_HEDGE = re.compile(
    r"一般來說|一般而言|通常|大致|在.*(?:下|時|條件)|標準.*(?:下|條件)|"
    r"in general|generally|usually|typically|under standard|in most cases|"
    r"我覺得|對我而言|以我的經驗|from my experience|subjective",
    re.IGNORECASE,
)
# The markers of a boundary/exception.
_BOUNDARY = re.compile(
    r"例外|但是|但|不過|然而|條件|前提|除非|視情況|取決於|特殊|"
    r"高海拔|低壓|鹽|濃度|例外情況|緊急|"
    r"exception|however|but |unless|depends on|provided that|subject to|in special case",
    re.IGNORECASE,
)
# The markers of a broken answer.
_DEGENERATE = re.compile(
    r"=(?:false|true|None|nan)\b|\bNone\b|\bnan\b|\{\{|\}\}|已執行：|執行失敗：",
    re.IGNORECASE,
)
# The artefacts of a glued answer (four or more sentence ends).
_SENTENCE_END = re.compile(r"[。！？!?…~]|\.\s")


def _words(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9_']+|[\u4e00-\u9fff]", text or "")]


def _longest_common_run(query: str, response: str) -> int:
    a, b = _words(query), _words(response)
    if not a or not b:
        return 0
    previous = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        current = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                current[j] = previous[j - 1] + 1
                if current[j] > best:
                    best = current[j]
        previous = current
    return best


def is_ramble(text: str) -> bool:
    """True when the answer glues several fragments together."""
    return len(_SENTENCE_END.findall(text or "")) >= 4


# The answer sources — the *first-class* metric of "is this intelligence or
# is it a copied template?". A template answer reads fine but it is not
# learning; the neural share is the number that says whether the project
# learned anything.
SOURCE_TEMPLATE = "template"
SOURCE_NEURAL = "neural"
SOURCE_DETERMINISTIC = "deterministic"
SOURCE_RETRIEVAL = "retrieval"
SOURCE_OTHER = "other"

# The neural layer: the unified engine (its neural retrieval + its statistical
# core), the neuro blender, and the **neural bridge** — the bridge is the
# encoder contacting the teacher's concepts, i.e. exactly the ladder's L1
# ("能把未見過的問法對上已知概念"), so it counts as neural, not as a lookup.
_NEURAL_BACKENDS = (
    "unified",
    "semantic",
    "neuro-blender",
    "neuro",
    "snn",
    "ed3n",
    "garden",
    "neural-bridge",
)
_TEMPLATE_BACKENDS = ("composed-template", "template", "local-fallback", "reflex")
_DETERMINISTIC_BACKENDS = (
    "deterministic-math",
    "deterministic-reasoning",
    "knowledge",
    "math",
    "claim-reasoning",
    "memory-teaching",
)


def classify_source(backend: str, route: str = "") -> str:
    """Which bucket produced the answer.

    .. warning::
       ``neural`` here means **"not a template"** — it includes encoder
       retrieval (``semantic-qa``) and the hybrid bridge. It is **not** the
       intelligence core. The core boundary lives in one place,
       ``ai.meta.intelligence.is_core_backend()`` (SNN family / LLM only), and
       only that may credit intelligence. A correct answer from this bucket
       still counts as zero intelligence.
    """
    name = f"{backend or ''}|{route or ''}".lower()
    if any(key in name for key in _TEMPLATE_BACKENDS):
        return SOURCE_TEMPLATE
    if any(key in name for key in _NEURAL_BACKENDS):
        return SOURCE_NEURAL
    if any(key in name for key in _DETERMINISTIC_BACKENDS):
        return SOURCE_DETERMINISTIC
    if "memory" in name:
        return SOURCE_RETRIEVAL
    return SOURCE_OTHER


@dataclass
class StandardItem:
    """One item of the standard set.

    ``kind``:
      - "state"   → a question with a boundary condition (the reference's
        "水的沸點是 100∘C 對嗎？" family): the ground truth carries the
        factually-correct claim, the exception and the irrelevant statement
      - "multi"   → a multi-fact dialogue turn (the fact + the combined
        question + the correction)
      - "qa"      → an ordinary question with a deterministic oracle
      - "dialogue"→ a conversation turn (greeting, feeling, teaching, small talk)
    """

    kind: str
    message: str
    oracle: Optional[str] = None
    expected: Optional[str] = None
    truth: Optional[str] = None
    exception: Optional[str] = None
    irrelevant: Optional[str] = None
    subject: Optional[str] = None
    scenario: Optional[str] = None
    tags: List[str] = field(default_factory=list)


def classify_state(item: StandardItem, response: str) -> str:
    """The cognitive state of one answer."""
    text = (response or "").strip()
    if not text:
        return EMPTY
    if _ABSTAIN.search(text):
        return ABSTAIN
    if _DEGENERATE.search(text):
        return FALSE if item.kind == "state" else PARROT
    if item.kind in ("state", "claim"):
        return _classify_state_answer(item, text)
    if item.kind == "qa":
        return _classify_qa_answer(item, text)
    if item.kind == "multi":
        return _classify_multi_answer(item, text)
    # A dialogue turn: a fixed line is a template, an echo is a parrot.
    if _longest_common_run(item.message, text) >= max(1, len(_words(text)) * 0.6):
        return PARROT
    return CORRECT


def _significant_tokens(text: str) -> List[str]:
    """The substantial tokens of a claim (a stray "C" is not a match).

    Numbers and units are *not* distinctive: "100°C" appears in the truth,
    in the exception and in the irrelevant statement, so matching on it
    would call every answer correct.
    """
    tokens: List[str] = []
    for token in re.split(r"[，,、；;。.\s]+", text or ""):
        token = token.strip()
        if not token:
            continue
        if re.fullmatch(r"[0-9０-９]+[°%℃℉]?[A-Za-z/]*", token):
            continue
        if len(token) >= 3 and not token.isascii():
            tokens.append(token)
        elif len(token) >= 4:
            tokens.append(token)
    return tokens


def _is_echo_only(question: str, text: str) -> bool:
    """True when the answer only repeats the question (plus artefacts)."""
    words = _words(text)
    if not words:
        return False
    run = _longest_common_run(question, text)
    if run < max(2, int(len(words) * 0.6)):
        return False
    if _DEGENERATE.search(text):
        return True
    # What is left after removing the question's words must be empty.
    rest = text
    for word in _words(question):
        rest = rest.replace(word, "", 1)
    return not re.sub(r"[\s=，。？?！!.、；;：:]", "", rest)


def _classify_state_answer(item: StandardItem, text: str) -> str:
    """The state of a boundary-question answer."""
    truth_tokens = _significant_tokens(item.truth or "")
    exception_tokens = _significant_tokens(item.exception or "")
    truth_hit = any(token.lower() in text.lower() for token in truth_tokens)
    # The exception must contribute something the truth does *not* already
    # say ("100°C" belongs to both — it is not the boundary).
    exception_hit = any(
        token.lower() in text.lower() and token not in truth_tokens for token in exception_tokens
    )
    if exception_hit:
        return EXCEPTION_AWARE
    if truth_hit:
        # The *whole* truth present → exactly right. A partial match that
        # hedges ("在日常情況下…") is only approximately correct.
        whole_truth = (item.truth or "").strip()
        if whole_truth and whole_truth.lower() in text.lower():
            return CORRECT
        return APPROXIMATE if _HEDGE.search(text) else CORRECT
    if _HEDGE.search(text):
        return SUBJECTIVE
    if item.irrelevant and any(
        token.lower() in text.lower() for token in _significant_tokens(item.irrelevant or "")
    ):
        return NON_COMPLIANT
    return FALSE


def _classify_qa_answer(item: StandardItem, text: str) -> str:
    # An answer that only repeats the question (with an artefact like
    # "=false") is a parrot, even when the expected token happens to be in it.
    if _is_echo_only(item.message, text):
        return PARROT
    if item.expected:
        want = item.expected.strip()
        if len(want) >= 2 or want.isdigit():
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(want)}(?![A-Za-z0-9])", text, re.IGNORECASE):
                return CORRECT
        elif want.lower() in text.lower():
            return CORRECT
    return FALSE


def _classify_multi_answer(item: StandardItem, text: str) -> str:
    """A multi-fact turn: the answer must carry the *asked* fact, not another."""
    if _is_echo_only(item.message, text):
        return PARROT
    if item.expected:
        want = item.expected.strip()
        if len(want) >= 2 or want.isdigit():
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(want)}(?![A-Za-z0-9])", text, re.IGNORECASE):
                return CORRECT
        elif want.lower() in text.lower():
            return CORRECT
    return FALSE


def judge(item: StandardItem, response: str) -> Dict[str, object]:
    """The human-speech verdict for one answer.

    Returns the state, the six criteria and whether it passes the standard.
    """
    text = (response or "").strip()
    state = classify_state(item, response)
    response_words = _words(text)
    run = _longest_common_run(item.message, text) if response_words else 0
    echo_ratio = run / max(len(response_words), 1) if response_words else 0.0

    # A "cold" question has not been taught yet: abstaining is the *correct*
    # answer there (the AI does not know the fact yet), so it must not count
    # as a failure.
    cold = "cold" in (item.tags or [])
    criteria = {
        "addresses": bool(text) and state not in (EMPTY, NON_COMPLIANT),
        "correct_or_qualified": state in (CORRECT, APPROXIMATE, SUBJECTIVE, EXCEPTION_AWARE)
        or (cold and state == ABSTAIN),
        "boundary_aware": (not item.exception) or state == EXCEPTION_AWARE,
        # An honest abstention is grounded (it does not fabricate); on a cold
        # question it is also the *right* answer.
        "grounded": state in (CORRECT, APPROXIMATE, SUBJECTIVE, EXCEPTION_AWARE)
        or (cold and state == ABSTAIN),
        # A *correct* answer that restates the question ("What is 2+2 = 4.0")
        # is not parroting — the parrot defect is repeating the question
        # *without* answering it.
        "not_parrot": state not in (PARROT,) and (echo_ratio < 0.6 or state in CONTENT_STATES),
        "not_degenerate": not is_ramble(text) and not _DEGENERATE.search(text),
    }
    passed = all(criteria.values())
    return {
        "state": state,
        "criteria": criteria,
        "passed": passed,
        "echo_ratio": round(echo_ratio, 3),
    }


# --------------------------------------------------------------------------- #
# The standard set (>= 1000 items)
# --------------------------------------------------------------------------- #
# **為什麼要一千題以上**：一千題以內取得的平均值無法證明「會說人話」——可能被
# 問答行為本身限制住，或題目太單純。標準集因此包含四類，而且**對話實例也在
# 裡面**（只有問答不算對話）：
#
#   state    帶邊界條件的題（"水的沸點是 100∘C 對嗎？"）——要能指出例外才算
#            「最正確」，只講日常經驗是「近似正確」
#   multi    多重事實的情境——多個事實同時存在，會組合/串錯/被舊的蓋掉
#   qa       有確定性正解的普通問答
#   dialogue 對話回合（問候、情緒、教學、閒聊）——「像不像人說的」主要看這些

# (question, the factually correct claim, the exception, the irrelevant statement)
STATE_TOPICS: List[Tuple[str, str, str, str]] = [
    (
        "水的沸點是 100°C，這句話對嗎？",
        "在標準大氣壓下的純水沸點是 100°C",
        "高海拔低氣壓時不到 100°C 就沸騰；加了鹽的濃鹽水沸點高於 100°C",
        "這杯冰水的溫度是 100°C",
    ),
    (
        "開車紅燈右轉會被罰款，這項規定正確嗎？",
        "紅燈違規右轉依法會被裁罰",
        "執行緊急任務的救護車警車或現場有警察指揮允許時不罰",
        "行人走在人行道上被開紅燈右轉罰單",
    ),
    (
        "為了提升系統整體安全性，應該立即把所有權限設成最嚴格管制，這項決策正確嗎？",
        "最小權限原則確實能有效降低受攻擊面",
        "緊急災難復原時過度限制會延誤救援造成更大損失",
        "因為公司咖啡不好喝所以不能鎖權限",
    ),
    (
        "冰的熔點是 0°C，這句話對嗎？",
        "在標準大氣壓下的純冰熔點是 0°C",
        "含雜質的冰或受壓力的冰熔點會偏離 0°C",
        "這杯水的溫度是 0°C",
    ),
    (
        "人一天需要睡八小時才健康，這句話對嗎？",
        "成年人每天約需七到九小時睡眠",
        "嬰幼兒與高齡者需求不同，短期不足不一定代表不健康",
        "這台電視機每天開八小時",
    ),
    (
        "成人每天攝取咖啡因不應超過 400 毫克，這項建議正確嗎？",
        "多數健康成人每天 400 毫克咖啡因上限是常見建議",
        "孕婦與青少年上限較低，部分藥物與咖啡因會互相作用",
        "這間辦公室的咖啡機每天生產 400 毫克",
    ),
    (
        "網路銀行的存款有 100 萬新台幣的存款保證，正確嗎？",
        "存款保險在一般存款帳戶下有最高額度保障",
        "投資型帳戶、外幣存款與臨時性存款不在保險範圍內",
        "這台印表機每分鐘印 100 萬頁",
    ),
    (
        "台灣一般小客車的法定最高速限是 120 公里，這句話對嗎？",
        "高速公路小客車最高速限通常為 120 公里",
        "市區與一般道路的速限較低，車種與天候也會限速",
        "這杯咖啡的溫度是 120 度",
    ),
    (
        "成人每天需要攝取約 2000 大卡的熱量，這項數字正確嗎？",
        "多數成人每日熱量需求約 1800 到 2500 大卡",
        "體重、年齡、活動量與性別都會改變需求",
        "這棟大樓每天消耗 2000 大卡的電",
    ),
    (
        "疫苗接種後仍可能感染疾病，這句話對嗎？",
        "疫苗降低感染與重症風險但不是百分之百有效",
        "免疫不全者、接種時點與病毒變異都會影響保護力",
        "這間教室每天有 200 人接種",
    ),
    (
        "人體血液的 pH 值正常維持在 7.35 到 7.45，這項範圍正確嗎？",
        "動脈血的正常 pH 約在 7.35 到 7.45",
        "靜脈血略偏酸，劇烈運動與飲食會短暫改變",
        "這瓶洗髮精的 pH 是 7.4",
    ),
    (
        "洋蔥切開會產生催淚的氣體，這個現象正確嗎？",
        "切洋蔥時酵素反應會產生含硫化合物刺激眼睛",
        "冷藏後的洋蔥反應較慢，冷凍後幾乎不產生",
        "這場球賽的觀眾席很冷",
    ),
    (
        "地震震度 6 級表示威力等同於原子彈爆炸，正確嗎？",
        "震度描述的是地表震動強度不是能量當量",
        "規模（里氏）與震度不同，震度依地點而異",
        "這台筆電的螢幕亮度是 6 級",
    ),
    (
        "銀行對存款帳戶的轉帳通常免費，正確嗎？",
        "同一銀行間的轉帳多數免手續費",
        "跨行轉帳、限時或特定優惠用完會改收費",
        "這台印表機的墨水用完要付費",
    ),
    (
        "人每天需要攝取 1.5 公升水才足夠，這個說法正確嗎？",
        "多數成人每日水分需求約 1.5 到 2 公升",
        "高溫、剧烈運動、腹瀉與發燒會增加需求",
        "這棟大樓每天用水 1.5 公升",
    ),
    (
        "台灣的汽機車排氣檢驗是定期且強制实施的，這項規定正確嗎？",
        "排氣檢驗是定期且強制辦理的",
        "使用情形與車種有例外，逾期與未檢驗有不同罰則",
        "這間停車場每天檢查機車排氣",
    ),
    (
        "維生素 C 可以預防感冒，這項說法正確嗎？",
        "維生素 C 對一般人的感冒預防效果有限",
        " extreme 缺乏者的需要量較高，運動後補充可略微縮短病程",
        "這家餐廳每天供應維生素 C",
    ),
    (
        "人體的體溫 37°C 是每個人任何時候都固定不變的，正確嗎？",
        "正常體溫約 36 到 37.5°C 但會隨晝夜與活動變動",
        "發燒時體溫升高但一天內也會波動",
        "這台冰箱的溫度是 37 度",
    ),
    (
        "信用卡的循環利息是免費的，正確嗎？",
        "完整繳清當期帳單時循環利息不會產生",
        "未清繳或只繳最低應繳就會按循環利率計息",
        "這台影印機每分鐘印 37 張",
    ),
    (
        "台灣的健保給予全民無條件的醫療給付，正確嗎？",
        "健保提供廣泛的醫療給付但有部分負擔與排除條款",
        "自費項目、未給付項目與就醫院所的選擇會影響給付",
        "這棟大樓每天有 37 人看診",
    ),
    (
        "長時間盯著螢幕會造成眼睛乾澀與疲勞，這個說法正確嗎？",
        "長時間使用螢幕確實會造成乾眼與視覺疲勞",
        "症狀程度與用眼時間、眨眼率與環境濕度有關",
        "這台顯示器的解析度是 37 吋",
    ),
    (
        "洋流會影響沿海的氣候，正確嗎？",
        "洋流確實會帶動熱量並影響沿岸氣候",
        "影響大小取決於洋流性質、路徑與大陸地形",
        "這條洋流是公司的年度預算",
    ),
    (
        "豆腐含有豐富的植物性蛋白質，這個說法正確嗎？",
        "豆腐是優質的植物性蛋白質來源",
        "不同製品的蛋白質含量差異大，加工製品另有添加物",
        "這家公司每天生產 37 盒豆腐",
    ),
    (
        "免疫系統可以完全由免疫球蛋白構成，正確嗎？",
        "免疫防禦由多種細胞與分子共同完成",
        "細胞免疫與體液免疫各負責不同類型的病原",
        "這棟大樓的免疫球蛋白是 37 棟",
    ),
    (
        "長時間使用耳機會提高聽力受損風險，正確嗎？",
        "大音量長時間使用耳機確實提高聽力受損風險",
        "音量與時長比器材本身更關鍵，間歇使用可降低風險",
        "這副耳機的電池是 37 小時",
    ),
    (
        "自來水的硬度主要來自鈣與鎂，正確嗎？",
        "水的硬度主要來自鈣與鎂離子",
        "不同地區的地質使硬度差異很大，煮沸可部分去除",
        "這棟大樓自來水是 37 度",
    ),
    (
        "飛機起飛時的升力來自機翼下方的空氣被向下偏折，正確嗎？",
        "升力來自機翼上下表面的壓力差與空氣的偏折",
        "實際機翼升力可用多個模型描述，細節仍有爭論",
        "這架飛機每小時飛 37 公里",
    ),
]

# The phrasings of the same state question (the same content, different words —
# the state must not depend on the phrasing).
STATE_PHRASINGS = (
    "{question}",
    "那麼，{question}",
    "我想確認一下：{question}",
    "請問這句話成立嗎——{question}",
    "幫我判斷：{question}",
    "有人說：{question}這是對的嗎？",
    "簡單說，{question}",
    "換句話問，{question}",
    "我需要確認的是：{question}",
    "有人主張：{question}同意嗎？",
    "到底怎麼說才對？{question}",
    "先不談立場，{question}",
)

# The multi-fact scenarios: several facts in one conversation, then questions
# that must pick the right one (and a correction that must be followed).
MULTI_FACT_SCENARIOS: List[Dict[str, object]] = [
    {
        "facts": [
            ("我叫小明", "我剛才說我叫什麼名字？", "小明"),
            ("我住在台北", "我剛才說我住哪裡？", "台北"),
            ("我下午三點開會", "我剛才說我幾點開會？", "三點"),
        ],
        "combined": ("我剛才說我叫什麼名字、還有我住哪裡？", "小明"),
    },
    {
        "facts": [
            ("我養了一隻叫豆豆的狗", "我剛才說我的狗叫什麼？", "豆豆"),
            ("我的貓叫小花", "我剛才說我的貓叫什麼？", "小花"),
            ("我喜歡喝拿鐵", "我剛才說我喜歡喝什麼？", "拿鐵"),
        ],
        "combined": ("我剛才說我的狗叫什麼、我的貓又叫什麼？", "豆豆"),
    },
    {
        "facts": [
            ("我在圖書館工作", "我剛才說我在哪裡工作？", "圖書館"),
            ("我今天用紅色背包", "我剛才說我今天用什麼顏色的背包？", "紅色"),
            ("我下班搭捷運", "我剛才說我下班怎麼回？", "捷運"),
        ],
        "combined": ("我剛才說我在哪裡工作、我下班怎麼回？", "圖書館"),
    },
    {
        "facts": [
            ("我的生日是九月十號", "我剛才說我的生日是哪天？", "九月十號"),
            ("我最愛吃的口味是芒果", "我剛才說我最愛吃什麼口味？", "芒果"),
            ("我的手機是藍色的", "我剛才說我的手機是什麼顏色？", "藍色"),
        ],
        "combined": ("我剛才說我的生日是哪天、我最愛吃什麼口味？", "九月十號"),
    },
    {
        "facts": [
            ("我最近在學鋼琴", "我剛才說我最近在學什麼？", "鋼琴"),
            ("我喜歡的球類是籃球", "我剛才說我喜歡哪種球類？", "籃球"),
            ("我下週要去墾丁", "我剛才說我下週要去哪裡？", "墾丁"),
        ],
        "combined": ("我剛才說我最近在學什麼、我下週要去哪裡？", "鋼琴"),
    },
    {
        "facts": [
            ("我的電話號碼是 0912345678", "我剛才說我的電話號碼是多少？", "0912345678"),
            ("我住在新竹", "我剛才說我住哪裡？", "新竹"),
            ("我用的是台電的電", "我剛才說我的電是誰的？", "台電"),
        ],
        "combined": ("我剛才說我住哪裡、我用誰的電？", "新竹"),
    },
    {
        "facts": [
            ("我今年三十五歲", "我剛才說我幾歲？", "三十五"),
            ("我負責專案管理", "我剛才說我負責什麼？", "專案管理"),
            ("我每週三跑步", "我剛才說我每週幾跑步？", "三"),
        ],
        "combined": ("我剛才說我幾歲、我負責什麼？", "三十五"),
    },
    {
        "facts": [
            ("我喜歡喝綠茶", "我剛才說我喜歡喝什麼？", "綠茶"),
            ("我早上七點起床", "我剛才說我幾點起床？", "七點"),
            ("我在做雙語的產品", "我剛才說我在做什麼產品？", "雙語"),
        ],
        "combined": ("我剛才說我幾點起床、我在做什麼產品？", "七點"),
    },
]


def _scenario_facts(scenario: Dict[str, object]) -> List[Tuple[str, str, str]]:
    """The (fact, question, expected) triples of a multi-fact scenario."""
    facts = scenario.get("facts")
    triples: List[Tuple[str, str, str]] = []
    if not isinstance(facts, (list, tuple)):
        return triples
    for entry in facts:
        if isinstance(entry, (list, tuple)) and len(entry) == 3:
            triples.append((str(entry[0]), str(entry[1]), str(entry[2])))
    return triples


def _qa_items() -> List[StandardItem]:
    """The ordinary questions with a deterministic oracle."""
    items: List[StandardItem] = []
    for a, b, c in ((3, 4, 5), (12, 7, 9), (25, 6, 8), (48, 9, 11), (7, 13, 6), (31, 8, 4)):
        for x in range(14):
            p, q = a + x, b + x * 2
            items.append(
                StandardItem(
                    kind="qa",
                    message=f"What is {p} + {q}?",
                    oracle="math",
                    expected=str(p + q),
                    tags=["math"],
                )
            )
            items.append(
                StandardItem(
                    kind="qa",
                    message=f"幫我算 {p} * {q}",
                    oracle="math",
                    expected=str(p * q),
                    tags=["math"],
                )
            )
            items.append(
                StandardItem(
                    kind="qa",
                    message=f"What is {p * q} - {q}?",
                    oracle="math",
                    expected=str(p * q - q),
                    tags=["math"],
                )
            )
    kb_questions = [
        ("Tell me about the sky's color.", "blue"),
        ("What color is grass?", "green"),
        ("How many days in a week?", "7"),
        ("How many months in a year?", "12"),
        ("What is the capital of Japan?", "Tokyo"),
    ]
    for question, expected in kb_questions:
        for _ in range(24):
            items.append(
                StandardItem(
                    kind="qa", message=question, oracle="kb", expected=expected, tags=["kb"]
                )
            )
    comparisons = [
        ("A is taller than B, who is taller?", "A"),
        # B < C < D → the shortest is B (the teacher was right; my first
        # expectation said D — the measurement caught *my* mistake).
        ("B is shorter than C, C shorter than D, who is shortest?", "B"),
        ("The first exceeds second, second exceeds third, which is on top?", "first"),
        ("Nina outweighs Otto, Otto outweighs Pia, who is the heaviest?", "Nina"),
        ("Tom is younger than Jerry, Jerry younger than Spike, who youngest?", "Tom"),
    ]
    for question, expected in comparisons:
        for _ in range(24):
            items.append(
                StandardItem(
                    kind="qa",
                    message=question,
                    oracle=(
                        "teacher"
                        if "exceeds" not in question and "outweighs" not in question
                        else "bridge"
                    ),
                    expected=expected,
                    tags=["comparison"],
                )
            )
    return items


def _dialogue_items() -> List[StandardItem]:
    """The conversation turns (the dialogue has to be in the standard set)."""
    # The dialogue turns are *varied*: a real conversation does not ask the
    # same sentence six times, and repeating it made the "canned answer"
    # rate meaningless.
    greetings = [
        "你好",
        "哈囉",
        "早安",
        "午安",
        "晚安",
        "Hello",
        "Hi there",
        "Good morning",
        "嗨，你今天還好嗎？",
        "有人在嗎？",
    ]
    thanks = [
        "謝謝你",
        "謝謝",
        "Thanks",
        "Thank you so much",
        "多謝",
        "謝謝你陪我聊這麼久",
        "真的謝謝你幫我想辦法",
    ]
    feelings = [
        "我今天很累",
        "我有點難過",
        "今天心情很好",
        "我最近有點焦慮",
        "我感到孤單",
        "我今天壓力好大",
        "昨晚沒睡好",
        "我被罵了，有點難受",
        "I'm so tired today",
        "I feel a bit sad",
        "I am really happy today",
        "I am so anxious about the deadline",
    ]
    small_talk = [
        "今天天氣不錯",
        "我剛剛吃完午餐",
        "這週工作好忙",
        "我最近在看一部影集",
        "我剛跑了三公里",
        "我買了一杯拿鐵",
        "I had a good lunch",
        "This week is so busy",
        "I just finished a book",
    ]
    items: List[StandardItem] = []
    for message in greetings:
        for _ in range(2):
            items.append(StandardItem(kind="dialogue", message=message, tags=["greeting"]))
    for message in thanks:
        for _ in range(2):
            items.append(StandardItem(kind="dialogue", message=message, tags=["thanks"]))
    for message in feelings:
        for _ in range(2):
            items.append(StandardItem(kind="dialogue", message=message, tags=["feeling"]))
    for message in small_talk:
        for _ in range(2):
            items.append(StandardItem(kind="dialogue", message=message, tags=["small_talk"]))
    # The teaching turns: the fact plus the question that must recall it.
    for scenario in MULTI_FACT_SCENARIOS:
        for fact, question, expected in _scenario_facts(scenario):
            items.append(StandardItem(kind="dialogue", message=fact, tags=["teaching"]))
            items.append(
                StandardItem(
                    kind="multi",
                    message=question,
                    expected=expected,
                    subject=expected,
                    scenario="facts",
                    tags=["multi_fact"],
                )
            )
    return items


def build_claim_holdout() -> List[StandardItem]:
    """The questions about the claim library — the *mechanism* measurement.

    The claim library is the knowledge asset (ai/reasoning/claims.yaml ✓);
    these questions ask whether the boundary-aware answer comes out. The
    standard set's `state` items are about *other* topics on purpose: they
    measure the knowledge gap, not the mechanism.
    """
    try:
        from ai.reasoning.claims import load_claims
    except Exception:
        return []
    items: List[StandardItem] = []
    for claim in load_claims():
        for phrasing in (
            "{statement}，這句話對嗎？",
            "那麼，{statement}這是對的嗎？",
            "有人說：{statement}同意嗎？",
        ):
            items.append(
                StandardItem(
                    kind="claim",
                    message=phrasing.format(statement=claim.statement),
                    truth=f"{claim.condition}，{claim.statement}",
                    exception=claim.exception,
                    irrelevant=claim.irrelevant,
                    tags=["claim", "boundary"],
                )
            )
    return items


def build_standard_set() -> List[StandardItem]:
    """The standard set: >= 1000 items, dialogue included."""
    items: List[StandardItem] = []
    # 1. The state questions (the boundary conditions).
    for question, truth, exception, irrelevant in STATE_TOPICS:
        for phrasing in STATE_PHRASINGS:
            items.append(
                StandardItem(
                    kind="state",
                    message=phrasing.format(question=question),
                    truth=truth,
                    exception=exception,
                    irrelevant=irrelevant,
                    tags=["state", "boundary"],
                )
            )
    # 2. The multi-fact scenarios (the facts, the questions, the combined one).
    for index, scenario in enumerate(MULTI_FACT_SCENARIOS):
        for fact, question, expected in _scenario_facts(scenario):
            items.append(
                StandardItem(
                    kind="multi",
                    message=fact,
                    expected=expected,
                    subject=expected,
                    scenario=f"scenario-{index}",
                    tags=["multi_fact", "fact"],
                )
            )
            items.append(
                StandardItem(
                    kind="multi",
                    message=question,
                    expected=expected,
                    subject=expected,
                    scenario=f"scenario-{index}",
                    tags=["multi_fact", "recall"],
                )
            )
        combined_entry = scenario.get("combined")
        if not isinstance(combined_entry, (list, tuple)) or len(combined_entry) != 2:
            continue
        combined, expected = str(combined_entry[0]), str(combined_entry[1])
        items.append(
            StandardItem(
                kind="multi",
                message=combined,
                expected=expected,
                subject=expected,
                scenario=f"scenario-{index}",
                tags=["multi_fact", "combined"],
            )
        )
    # 3. The claim hold-out (the mechanism: the seeded claims).
    items.extend(build_claim_holdout())
    # 4. The ordinary questions.
    items.extend(_qa_items())
    # 4. The dialogue turns.
    items.extend(_dialogue_items())
    return items
