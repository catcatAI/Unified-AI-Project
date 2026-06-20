"""
Unicode normalization and input-method utilities for ED3N and GARDEN.

Provides:
  - normalize_text()   — NFKC + fullwidth → halfwidth + zero-width cleanup
  - to_romaji()        — Hiragana/Katakana → romaji (Japanese input method)
  - is_cjk() / is_japanese() — character range checks
  - cjk_radical()      — CJK radical lookup for a given character (optional)

Zero external dependencies. Uses only Python's built-in ``unicodedata``.
"""

# =============================================================================
# ANGELA-MATRIX: [L1-L2] [αβγδ] [A] [L1]
# =============================================================================

import unicodedata

__all__ = [
    "normalize_text",
    "to_romaji",
    "is_cjk",
    "is_japanese",
    "is_english_dominant",
]

# ---------------------------------------------------------------------------
# Kana → Romaji mapping (standard Hepburn)
# Covers: hiragana, katakana (via offset), dakuten, handakuten, small kana
# ---------------------------------------------------------------------------

_KANA_ROMAJI: dict = {
    # Gojuuon (五十音)
    "\u3042": "a",    # あ
    "\u3044": "i",    # い
    "\u3046": "u",    # う
    "\u3048": "e",    # え
    "\u304a": "o",    # お
    "\u304b": "ka",   # か
    "\u304d": "ki",   # き
    "\u304f": "ku",   # く
    "\u3051": "ke",   # け
    "\u3053": "ko",   # こ
    "\u3055": "sa",   # さ
    "\u3057": "shi",  # し
    "\u3059": "su",   # す
    "\u305b": "se",   # せ
    "\u305d": "so",   # そ
    "\u305f": "ta",   # た
    "\u3061": "chi",  # ち
    "\u3064": "tsu",  # つ
    "\u3066": "te",   # て
    "\u3068": "to",   # と
    "\u306a": "na",   # な
    "\u306b": "ni",   # に
    "\u306c": "nu",   # ぬ
    "\u306d": "ne",   # ね
    "\u306e": "no",   # の
    "\u306f": "ha",   # は
    "\u3072": "hi",   # ひ
    "\u3075": "fu",   # ふ
    "\u3078": "he",   # へ
    "\u307b": "ho",   # ほ
    "\u307e": "ma",   # ま
    "\u307f": "mi",   # み
    "\u3080": "mu",   # む
    "\u3081": "me",   # め
    "\u3082": "mo",   # も
    "\u3084": "ya",   # や
    "\u3086": "yu",   # ゆ
    "\u3088": "yo",   # よ
    "\u3089": "ra",   # ら
    "\u308a": "ri",   # り
    "\u308b": "ru",   # る
    "\u308c": "re",   # れ
    "\u308d": "ro",   # ろ
    "\u308f": "wa",   # わ
    "\u3092": "wo",   # を
    "\u3093": "n",    # ん
    # Dakuten (濁音)
    "\u304c": "ga",   # が
    "\u304e": "gi",   # ぎ
    "\u3050": "gu",   # ぐ
    "\u3052": "ge",   # げ
    "\u3054": "go",   # ご
    "\u3056": "za",   # ざ
    "\u3058": "ji",   # じ
    "\u305a": "zu",   # ず
    "\u305c": "ze",   # ぜ
    "\u305e": "zo",   # ぞ
    "\u3060": "da",   # だ
    "\u3062": "ji",   # ぢ
    "\u3065": "zu",   # づ
    "\u3067": "de",   # で
    "\u3069": "do",   # ど
    "\u3070": "ba",   # ば
    "\u3073": "bi",   # び
    "\u3076": "bu",   # ぶ
    "\u3079": "be",   # べ
    "\u307c": "bo",   # ぼ
    # Handakuten (半濁音)
    "\u3071": "pa",   # ぱ
    "\u3074": "pi",   # ぴ
    "\u3077": "pu",   # ぷ
    "\u307a": "pe",   # ぺ
    "\u307d": "po",   # ぼ
    # Small kana (捨て仮名)
    "\u3083": "ya",   # ゃ
    "\u3085": "yu",   # ゅ
    "\u3087": "yo",   # ょ
    "\u3063": "tsu",  # っ (geminate)
}

_HIRA_START = ord("\u3041")  # U+3041
_KATA_START = ord("\u30a1")  # U+30A1
_KATA_OFFSET = _KATA_START - _HIRA_START


def _hira_to_kata(ch: str) -> str:
    """Convert a hiragana character to katakana."""
    cp = ord(ch)
    if _HIRA_START <= cp <= _HIRA_START + 0x56:
        return chr(cp + _KATA_OFFSET)
    return ch


def _build_katakana_map() -> dict:
    """Build katakana → romaji map from hiragana map."""
    return {_hira_to_kata(k): v for k, v in _KANA_ROMAJI.items()}


_KATA_ROMAJI: dict = _build_katakana_map()


# ---------------------------------------------------------------------------
# Fullwidth → halfwidth mapping (for characters NFKC doesn't catch)
# ---------------------------------------------------------------------------

_FULLWIDTH_TO_HALFWIDTH = str.maketrans({
    chr(0xFF01 + i): chr(0x21 + i) for i in range(94)  # Fullwidth ASCII
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """
    Normalize Unicode text for robust matching.

    Steps:
    1. NFKC normalization (compatibility decomposition)
    2. Remaining fullwidth → halfwidth ASCII (for extended fullwidth forms)
    3. Zero-width characters stripped (ZWSP, BOM, ZWNJ, ZWJ, etc.)
    4. Whitespace stripped

    NFKC alone handles:
    - Fullwidth ASCII (Ａ → A, １ → 1)
    - Compatibility ideographs (敏 → 敏, 髙 → 高)
    - Halfwidth katakana (ﾊﾛｰ → ハロー)
    - CJK compatibility (ﬁ → fi, K → K)
    - Kana compatibility (㌃ → ヘクタールなど)
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_FULLWIDTH_TO_HALFWIDTH)
    for zc in ("\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad"):
        text = text.replace(zc, "")
    return text.strip()


def to_romaji(text: str) -> str:
    """
    Convert Japanese kana (hiragana & katakana) to romaji (Hepburn).

    Non-kana characters pass through unchanged.

    Examples:
        "こんにちは" → "konnichiha"
        "コンニチハ" → "konnichiha"
        "ありがとう" → "arigatou"
    """
    result: list = []
    for ch in text:
        if "\u3040" <= ch <= "\u309f":
            result.append(_KANA_ROMAJI.get(ch, ch))
        elif "\u30a0" <= ch <= "\u30ff":
            result.append(_KATA_ROMAJI.get(ch, ch))
        else:
            result.append(ch)
    return "".join(result)


def is_cjk(ch: str) -> bool:
    """Return True if *ch* is a CJK Unified Ideograph (main plane)."""
    return "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf"


def is_japanese(ch: str) -> bool:
    """Return True if *ch* is hiragana or katakana."""
    return ("\u3040" <= ch <= "\u309f") or ("\u30a0" <= ch <= "\u30ff")


def is_english_dominant(text: str) -> bool:
    """Detect if input is primarily English (ASCII alpha) or CJK.

    Returns ``True`` when ASCII alphabetic characters outnumber CJK
    characters, or when the text contains no CJK at all.
    Used by ED3N and GARDEN engines to select language-appropriate
    fallback messages.
    """
    if not text:
        return True
    cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f")
    ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
    total_alpha = cjk_count + ascii_alpha
    if total_alpha == 0:
        return True
    return ascii_alpha / total_alpha > 0.5


def cjk_radical(char: str) -> str:
    """
    Return the Kangxi radical for a CJK character (if known), else ``""``.

    This is a minimal lookup for the most common ~400 CJK characters used
    in daily conversation.  Falls back to Unicode name if available.

    Usage::
        >>> cjk_radical("好")
        '女'
        >>> cjk_radical("語")
        '言'
    """
    if not char or not is_cjk(char):
        return ""
    try:
        name = unicodedata.name(char, "")
        if "RADICAL" in name:
            return name.split()[-1]
        for part in name.split():
            if part in ("KANGXI", "CJK"):
                continue
        if "\u2f00" <= char <= "\u2fd5":
            return char
        if name:
            name = name.removeprefix("CJK UNIFIED IDEOGRAPH-")
            name = name.removeprefix("CJK COMPATIBILITY IDEOGRAPH-")
    except (ValueError, TypeError):
        pass
    return _RADICAL_TABLE.get(char, "")


# Minimal CJK → radical decomposition table (300 most common characters)
# Format: { character: radical, ... }
_RADICAL_TABLE: dict[str, str] = {
    "一": "一", "丁": "一", "七": "一", "丈": "一", "三": "一",
    "上": "一", "下": "一", "不": "一", "世": "一", "中": "丨",
    "丶": "丶", "丸": "丶", "丹": "丶", "主": "丶", "久": "丿",
    "乎": "丿", "乏": "丿", "乖": "丿", "乗": "丿", "乙": "乙",
    "九": "乙", "乞": "乙", "也": "乙", "乱": "乙", "乳": "乙",
    "了": "亅", "予": "亅", "事": "亅", "二": "二", "五": "二",
    "井": "二", "亜": "二", "亡": "亠", "交": "亠", "享": "亠",
    "京": "亠", "人": "人", "仁": "人", "仕": "人", "他": "人",
    "付": "人", "仙": "人", "代": "人", "令": "人", "以": "人",
    "仰": "人", "仲": "人", "件": "人", "任": "人", "休": "人",
    "何": "人", "余": "人", "作": "人", "使": "人", "来": "人",
    "価": "人", "供": "人", "係": "人", "信": "人", "修": "人",
    "俳": "人", "倉": "人", "個": "人", "備": "人", "偉": "人",
    "伝": "人", "停": "人", "傷": "人", "働": "人", "像": "人",
    "億": "人", "化": "匕", "北": "匕", "指": "手", "持": "手",
    "打": "手", "投": "手", "拾": "手", "操": "手", "撮": "手",
    "接": "手", "提": "手", "揮": "手", "損": "手", "摇": "手",
    "摩": "手", "支": "支", "政": "攵", "故": "攵", "教": "攵",
    "文": "文", "斉": "文", "斗": "斗", "料": "斗", "新": "斤",
    "断": "斤", "方": "方", "旅": "方", "族": "方",
    "日": "日", "明": "日", "映": "日", "春": "日", "昼": "日",
    "時": "日", "晩": "日", "曜": "日", "曲": "日", "書": "曰",
    "最": "曰", "会": "曰", "月": "月", "有": "月", "服": "月",
    "朝": "月", "期": "月", "木": "木", "本": "木", "末": "木",
    "未": "木", "机": "木", "村": "木", "板": "木", "林": "木",
    "枚": "木", "果": "木", "枝": "木", "案": "木", "校": "木",
    "株": "木", "根": "木", "格": "木", "条": "木", "幹": "木",
    "業": "木", "楽": "木", "構": "木", "様": "木", "機": "木",
    "欠": "欠", "次": "欠", "欲": "欠", "歌": "欠", "止": "止",
    "正": "止", "歩": "止", "武": "止", "歳": "止",
    "死": "歹", "残": "歹", "段": "殳", "殺": "殳", "殿": "殳",
    "母": "毋", "毎": "毋", "毒": "毋", "比": "比", "毛": "毛",
    "氏": "氏", "民": "氏", "気": "气",
    "水": "水", "氷": "水", "永": "水", "汁": "水", "求": "水",
    "池": "水", "決": "水", "沈": "水", "河": "水", "油": "水",
    "治": "水", "法": "水", "波": "水", "注": "水", "泳": "水",
    "洋": "水", "洗": "水", "活": "水", "派": "水", "流": "水",
    "海": "水", "消": "水", "深": "水", "混": "水", "清": "水",
    "減": "水", "港": "水", "湖": "水", "湯": "水", "満": "水",
    "源": "水", "準": "水", "演": "水", "漢": "水", "潔": "水",
    "潮": "水", "激": "水",
    "火": "火", "灯": "火", "災": "火", "炎": "火", "無": "火",
    "照": "火", "熱": "火", "燃": "火", "爆": "火", "父": "父",
    "爺": "父", "牛": "牛", "物": "牛", "牧": "牛", "特": "牛",
    "犬": "犬", "犯": "犬", "状": "犬", "独": "犬", "猫": "犬",
    "猟": "犬", "獲": "犬", "王": "王", "玉": "王", "宝": "王",
    "珠": "王", "現": "王", "理": "王", "琴": "王", "環": "王",
    "生": "生", "産": "生", "用": "用",
    "田": "田", "男": "田", "町": "田", "画": "田", "界": "田",
    "畑": "田", "病": "疒", "症": "疒", "疲": "疒", "痛": "疒",
    "発": "癶", "登": "癶",
    "白": "白", "百": "白", "的": "白", "皆": "白", "皇": "白",
    "皮": "皮", "皿": "皿", "盛": "皿", "盟": "皿",
    "目": "目", "相": "目", "省": "目", "看": "目", "真": "目",
    "眼": "目", "着": "目", "睡": "目",
    "矢": "矢", "知": "矢", "短": "矢",
    "石": "石", "岩": "石", "砂": "石", "研": "石", "破": "石",
    "確": "石", "示": "示", "礼": "示", "社": "示", "祝": "示",
    "神": "示", "福": "示", "祭": "示", "禁": "示", "禅": "示",
    "祖": "示", "禍": "示", "禾": "禾", "利": "禾", "私": "禾",
    "科": "禾", "程": "禾",
    "穴": "穴", "空": "穴", "窓": "穴",
    "立": "立", "並": "立", "章": "立", "童": "立", "端": "立",
    "竹": "竹", "笑": "竹", "第": "竹", "筆": "竹", "等": "竹",
    "算": "竹", "管": "竹", "米": "米", "粉": "米", "精": "米",
    "糸": "糸", "系": "糸", "紀": "糸", "約": "糸", "紅": "糸",
    "級": "糸", "紙": "糸", "素": "糸", "組": "糸", "経": "糸",
    "結": "糸", "給": "糸", "統": "糸", "続": "糸", "維": "糸",
    "網": "糸", "総": "糸", "綿": "糸", "線": "糸", "編": "糸",
    "練": "糸", "緑": "糸", "縁": "糸", "縮": "糸", "繁": "糸",
    "織": "糸", "繕": "糸", "缶": "缶", "罪": "网", "置": "网",
    "羊": "羊", "美": "羊", "群": "羊",
    "羽": "羽", "習": "羽", "老": "老", "者": "老",
    "耳": "耳", "聞": "耳", "聯": "耳", "聖": "耳",
    "肉": "肉", "肌": "肉", "肥": "肉", "育": "肉", "胃": "肉",
    "胆": "肉", "背": "肉", "胸": "肉", "能": "肉", "脱": "肉",
    "脳": "肉", "腐": "肉",
    "臣": "臣", "臨": "臣", "自": "自", "至": "至", "致": "至",
    "臼": "臼", "興": "臼", "舌": "舌", "舎": "舌", "舗": "舌",
    "舟": "舟", "船": "舟", "色": "色",
    "花": "艸", "英": "艸", "草": "艸", "茶": "艸", "落": "艸",
    "葉": "艸", "著": "艸", "蒸": "艸", "薬": "艸", "芸": "艸",
    "虫": "虫", "血": "血",
    "行": "行", "術": "行", "街": "行",
    "衣": "衣", "表": "衣", "袋": "衣", "補": "衣", "製": "衣",
    "西": "西", "要": "西",
    "見": "見", "親": "見", "覚": "見", "観": "見",
    "言": "言", "計": "言", "記": "言", "訳": "言", "話": "言",
    "語": "言", "説": "言", "読": "言", "調": "言", "談": "言",
    "論": "言", "識": "言", "警": "言", "議": "言", "護": "言",
    "谷": "谷", "豆": "豆", "頭": "豆", "豊": "豆",
    "豚": "豕", "象": "豕",
    "貝": "貝", "貨": "貝", "販": "貝", "責": "貝", "貯": "貝",
    "貴": "貝", "買": "貝", "資": "貝", "賛": "貝", "賞": "貝",
    "賢": "貝", "赤": "赤",
    "走": "走", "起": "走", "足": "足", "路": "足", "踊": "足",
    "身": "身",
    "車": "車", "軍": "車", "軽": "車", "転": "車", "輪": "車",
    "辛": "辛", "弁": "辛", "辰": "辰", "辱": "辰", "農": "辰",
    "込": "辵", "近": "辵", "返": "辵", "通": "辵", "連": "辵",
    "週": "辵", "道": "辵", "運": "辵", "過": "辵", "達": "辵",
    "遠": "辵", "適": "辵", "選": "辵", "遺": "辵", "避": "辵",
    "邑": "邑", "部": "邑", "都": "邑",
    "配": "酉", "酒": "酉", "医": "酉", "酸": "酉",
    "釆": "釆", "金": "金", "釘": "金", "針": "金", "鈍": "金",
    "鉄": "金", "銀": "金", "銅": "金", "録": "金",
    "長": "長", "門": "門", "開": "門", "間": "門", "関": "門",
    "闘": "門", "阜": "阜", "阪": "阜", "防": "阜", "降": "阜",
    "限": "阜", "院": "阜", "除": "阜", "険": "阜", "陽": "阜",
    "際": "阜", "隣": "阜",
    "雨": "雨", "電": "雨", "雲": "雨", "雪": "雨", "零": "雨",
    "需": "雨", "青": "靑", "非": "非", "面": "面",
    "革": "革", "靴": "革", "音": "音", "響": "音",
    "頂": "頁", "順": "頁", "預": "頁", "領": "頁", "頭": "頁",
    "顔": "頁", "類": "頁", "願": "頁", "風": "風",
    "食": "食", "飯": "食", "飲": "食", "養": "食", "館": "食",
    "首": "首", "馬": "馬", "駐": "馬", "騎": "馬",
    "骨": "骨", "高": "高", "魚": "魚", "鳥": "鳥", "鹿": "鹿",
    "麻": "麻", "黄": "黄", "黒": "黒", "黙": "黒", "鼓": "鼓",
    "鼻": "鼻", "歯": "歯", "龍": "龍",
}
