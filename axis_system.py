# -*- coding: utf-8 -*-
"""
軸譜系統 — 依《物種分類架構（三軸系統）》（data/gdrive_export/物種分類架構（三軸系統）.txt）建構。

四系譜各有自己的軸，不是硬套同一把尺：
  物種  : 原種距離(N/S/F) + 人形比例(H/S/C) + 混血譜系(P/M1/M2/M3)
  AI    : 人形模仿度(F0-F3) + 自主性(A0-A3) + 程序開放度(O0-O2)
  義體人: 義體化比例(C1-C4) + 外觀人形保留度(H1-H3) + 神經保留度(B1-B3)
  神話種: 神性濃度(D1-D3) + 原典忠實度(O1-O3) + 存在維度(M1-M3)

所有交互（道具／裝備／任務／戰鬥數值）以軸譜為準：
  - 可交互（can_interact）      ：角色五維度親和力 ≥ 目標需求門檻
  - 交互深度（interaction_depth）：親和力與需求向量的對齊程度（0..1）
  - 數值計算（stat_modifiers）  ：由軸位推導屬性加乘
  - 身體部位（body_parts）      ：由人形比例／存在維度等軸位推導

文件的權威分類表（AUTHORITATIVE_CARD_AXES）優先於卡片 token，token 僅為輔助——
這就是「不再用 token 猜測種族」的實作。
"""

# ════════════════════════════════════════════════════════════════
# 1. 軸譜登錄（四系譜 × 各軸 × 位置）
# ════════════════════════════════════════════════════════════════

AXIS_SYSTEMS = {
    "物種": {
        "原種距離": {"N": "近原種", "S": "標準種", "F": "遠原種"},
        "人形比例": {"H": "類人型", "S": "標準型", "C": "類原型"},
        "混血譜系": {"P": "純血", "M1": "混血（一級）", "M2": "混血（二級）", "M3": "混血（三級）"},
    },
    "AI": {
        "人形模仿度": {"F0": "無形體", "F1": "抽象載體", "F2": "部分人形", "F3": "仿真人形"},
        "自主性": {"A0": "被動型", "A1": "條件型", "A2": "學習型", "A3": "完全自主"},
        "程序開放度": {"O0": "封閉黑箱", "O1": "部分開源", "O2": "完全開源"},
    },
    "義體人": {
        "義體化比例": {"C1": "輕度（<30%）", "C2": "中度（30%-70%）", "C3": "重度（70%-95%）", "C4": "全身（>95%）"},
        "外觀人形保留度": {"H1": "完全人形", "H2": "部分暴露", "H3": "非人形態"},
        "神經保留度": {"B1": "生物腦完整", "B2": "生物腦增強", "B3": "意識上傳"},
    },
    "神話種": {
        "神性濃度": {"D1": "傳說級", "D2": "信仰級", "D3": "原初級"},
        "原典忠實度": {"O1": "自由改編", "O2": "部分保留", "O3": "高度還原"},
        "存在維度": {"M1": "物質顯形", "M2": "靈體/概念", "M3": "跨維度"},
    },
}

# 其他／純人類：不納入軸系（文件「五、其他」），使用人類基線
DEFAULT_LINEAGE = "其他"

# ════════════════════════════════════════════════════════════════
# 2. 交互維度（五維度親和力，0..1）
# ════════════════════════════════════════════════════════════════

DIMENSIONS = ("物質", "靈性", "機械", "能量", "資訊")

# 每個軸位 → (物質, 靈性, 機械, 能量, 資訊)
_AXIS_TRAITS = {
    "物種": {
        "原種距離": {
            "N": (0.95, 0.05, 0.0, 0.10, 0.0),   # 近原種：保留原始生理與習性
            "S": (0.90, 0.15, 0.05, 0.15, 0.05), # 標準種：已融入智慧種族社會
            "F": (0.85, 0.25, 0.05, 0.20, 0.10), # 遠原種：高度智慧化，接近人類
        },
        "人形比例": {
            "H": (0.90, 0.20, 0.10, 0.20, 0.10), # 類人型：極度接近人類
            "S": (0.85, 0.15, 0.05, 0.20, 0.05), # 標準型：半人半原種
            "C": (0.80, 0.10, 0.0, 0.10, 0.0),   # 類原型：外觀接近原種動物
        },
        "混血譜系": {
            "P": (0.90, 0.15, 0.05, 0.15, 0.05),   # 純血
            "M1": (0.85, 0.20, 0.05, 0.20, 0.05),  # 混血一級
            "M2": (0.80, 0.25, 0.05, 0.25, 0.05),  # 混血二級
            "M3": (0.75, 0.30, 0.05, 0.30, 0.05),  # 混血三級
        },
    },
    "AI": {
        "人形模仿度": {
            "F0": (0.0, 0.10, 0.95, 0.15, 1.0),   # 無形體：無物理載體
            "F1": (0.20, 0.10, 0.95, 0.15, 0.95), # 抽象載體：伺服器/光球/車輛
            "F2": (0.50, 0.10, 0.90, 0.15, 0.90), # 部分人形：機械關節/螢幕臉
            "F3": (0.70, 0.15, 0.85, 0.20, 0.85), # 仿真人形：外觀幾乎無異
        },
        "自主性": {
            "A0": (0.10, 0.0, 0.40, 0.0, 0.50),   # 被動型
            "A1": (0.15, 0.0, 0.50, 0.0, 0.65),   # 條件型
            "A2": (0.20, 0.05, 0.60, 0.05, 0.80), # 學習型
            "A3": (0.30, 0.15, 0.70, 0.10, 0.95), # 完全自主
        },
        "程序開放度": {
            "O0": (0.20, 0.05, 0.60, 0.05, 0.50), # 封閉黑箱
            "O1": (0.30, 0.10, 0.80, 0.10, 0.80), # 部分開源
            "O2": (0.40, 0.15, 1.0, 0.15, 1.0),   # 完全開源
        },
    },
    "義體人": {
        "義體化比例": {
            "C1": (0.85, 0.15, 0.30, 0.10, 0.20), # 輕度 <30%
            "C2": (0.80, 0.12, 0.50, 0.10, 0.25), # 中度 30-70%
            "C3": (0.70, 0.08, 0.75, 0.10, 0.35), # 重度 70-95%
            "C4": (0.55, 0.05, 0.95, 0.10, 0.50), # 全身 >95%
        },
        "外觀人形保留度": {
            "H1": (0.90, 0.20, 0.30, 0.15, 0.20), # 完全人形
            "H2": (0.80, 0.15, 0.60, 0.15, 0.30), # 部分暴露
            "H3": (0.70, 0.10, 0.80, 0.10, 0.40), # 非人形態
        },
        "神經保留度": {
            "B1": (0.85, 0.20, 0.30, 0.20, 0.20), # 生物腦完整
            "B2": (0.80, 0.15, 0.50, 0.20, 0.30), # 生物腦增強
            "B3": (0.70, 0.05, 0.80, 0.15, 0.70), # 意識上傳
        },
    },
    "神話種": {
        "神性濃度": {
            "D1": (0.60, 0.60, 0.05, 0.60, 0.10), # 傳說級
            "D2": (0.55, 0.75, 0.05, 0.80, 0.15), # 信仰級
            "D3": (0.50, 0.95, 0.05, 1.0, 0.20),  # 原初級
        },
        "原典忠實度": {
            "O1": (0.60, 0.60, 0.05, 0.60, 0.10), # 自由改編
            "O2": (0.55, 0.65, 0.05, 0.65, 0.10), # 部分保留
            "O3": (0.50, 0.70, 0.05, 0.70, 0.10), # 高度還原
        },
        "存在維度": {
            "M1": (0.90, 0.50, 0.10, 0.50, 0.10), # 物質顯形
            "M2": (0.05, 1.0, 0.05, 0.90, 0.15),  # 靈體/概念：幾無物理形體
            "M3": (0.35, 1.0, 0.30, 1.0, 0.50),   # 跨維度
        },
    },
}

# 人類／其他基線（純人類、未分類角色）
HUMAN_AFFINITY = (0.85, 0.30, 0.15, 0.25, 0.15)

# ════════════════════════════════════════════════════════════════
# 3. 文件權威分類表（依《物種分類架構（三軸系統）》「全角色分類清單」）
#    優先於卡片 token——這是「不再用 token 猜測種族」的來源
# ════════════════════════════════════════════════════════════════

AUTHORITATIVE_CARD_AXES = {
    # 一、獸娘／魔物娘（物種三軸）
    "CC-52": ("物種", "N-C-P"), "CC-50": ("物種", "N-S-P"),
    "CC-38": ("物種", "S-S-P"), "CC-39": ("物種", "S-S-P"),
    "CC-40": ("物種", "S-S-P"), "CC-41": ("物種", "S-S-P"),
    "C02": ("物種", "S-H-P"), "C07": ("物種", "S-H-P"),
    "C03": ("物種", "S-H-P"), "CC-28": ("物種", "S-H-P"),
    "C05": ("物種", "S-H-P"), "CC-51": ("物種", "S-H-P"),
    "C15": ("物種", "F-H-P"), "CC-20": ("物種", "F-H-P"),
    "C04": ("物種", "S-H-P"), "C13": ("物種", "S-C-P"),
    "CC-04": ("物種", "S-H-P"), "CC-45": ("物種", "F-C-P"),
    "CC-46": ("物種", "F-C-P"), "CC-34": ("物種", "S-H-M1"),
    "CC-03": ("物種", "S-H-P"), "CC-02": ("物種", "S-H-P"),
    "CC-37": ("物種", "S-H-P"), "C08": ("物種", "S-H-P"),
    # 文件註：晞吶雖是拉米雅，但能收起蛇尾以人類形態行動 → S-H-P
    "CC-49": ("物種", "S-H-P"),
    # 二、AI（F-A-O 三軸）
    "CC-35": ("AI", "F3-A3-O0"), "CC-31": ("AI", "F1-A2-O1"),
    # 三、義體人（C-H-B 三軸）
    "C16": ("義體人", "C2-H2-B2"),
    # 四、神話種（D-O-M 三軸）
    "CC-36": ("神話種", "D2-O1-M1"), "C14": ("神話種", "D1-O1-M1"),
    "CC-18": ("神話種", "D1-O2-M2"), "CC-05": ("神話種", "D3-O1-M2"),
    "CC-42": ("神話種", "D3-O1-M2"), "CC-01": ("神話種", "D1-O1-M2"),
    "CC-08": ("神話種", "D1-O1-M2"),
}

# 依源文本判定、但未列於文件「全角色分類清單」的角色（文本特例，非卡片 token 猜測）
#   CC-19 左間カチッ：防空砲「靜子號」的機械妖精化身（25cm 小型飛行機械，
#         ——彈道計算/機械修復/防衛系統）——非人形載體 → AI 軸 F1（抽象載體，
#         ——載體非人形如伺服器/光球/車輛）＋A1 條件型＋O0 封閉黑箱（防衛 AI）
#   CC-24 維爾 (Veil)：共振文明使者，八條半透明紫色晶體節肢（物質顯形），
#         ——調和迴廊概念流、跨維度溝通 → 神話種（宇宙級概念具現、自由改編、物質顯形）
TEXT_DERIVED_AXES = {
    "CC-19": ("AI", "F1-A1-O0"),
    "CC-24": ("神話種", "D3-O1-M1"),
}

# ════════════════════════════════════════════════════════════════
# 4. 軸碼解析
# ════════════════════════════════════════════════════════════════

def parse_axis_code(lineage: str, code: str):
    """解析軸碼 → {axis_name: (code, label)}；無法解析回傳 None。

    例：parse_axis_code("物種", "S-H-P") →
        {"原種距離": ("S", "標準種"), "人形比例": ("H", "類人型"), "混血譜系": ("P", "純血")}
    """
    if not lineage or lineage not in AXIS_SYSTEMS:
        return None
    system = AXIS_SYSTEMS[lineage]
    parts = str(code).strip().replace("｜", "|").split("|")
    if len(parts) == 2:
        code = parts[1].strip()
    # 軸碼以「-」分段（S-H-P、F3-A3-O0、C2-H2-B2、D1-O2-M2），逐軸對位
    segs = [s.strip() for s in code.split("-") if s.strip()]
    if len(segs) != len(system):
        return None
    result = {}
    for axis_name, seg in zip(system, segs):
        positions = system[axis_name]
        if seg not in positions:
            return None
        result[axis_name] = (seg, positions[seg])
    return result


def axis_code_from_token(value: str):
    """從卡片「分類系譜」token 值（如「獸娘｜ F-H-P（遠原種、類人型、純血）」）解析。"""
    if not value:
        return None
    v = value.replace("｜", "|").strip()
    parts = v.split("|")
    if len(parts) < 2:
        return None
    lineage = parts[0].strip()
    code = parts[1].strip().split("（")[0].strip()
    return (lineage, code)


# ════════════════════════════════════════════════════════════════
# 5. 角色軸譜解析（權威表 → 卡片 token → 文本推導）
# ════════════════════════════════════════════════════════════════

def resolve_card_axis(card: dict):
    """回傳 (lineage, code, axes) 或 (None, None, None)。

    優先序（文本權威）：
    1. 文件權威分類表（AUTHORITATIVE_CARD_AXES，依卡片代碼）
    2. 卡片「分類系譜／物種分類」token
    3. 文本種族關鍵字推導（僅獸娘/龍娘/神話種等明確詞）
    """
    cid = card.get("card_id", "")
    if cid in AUTHORITATIVE_CARD_AXES:
        lineage, code = AUTHORITATIVE_CARD_AXES[cid]
        axes = parse_axis_code(lineage, code)
        if axes:
            return (lineage, code, axes)
    # 文本特例（依源文本判定、未列於文件分類清單）
    if cid in TEXT_DERIVED_AXES:
        lineage, code = TEXT_DERIVED_AXES[cid]
        axes = parse_axis_code(lineage, code)
        if axes:
            return (lineage, code, axes)
    for t in card.get("tokens", []):
        tname = t.get("name", "")
        ttype = t.get("type", "")
        if tname in ("分類系譜", "物種分類") or ttype == "species":
            parsed = axis_code_from_token(t.get("value", ""))
            if parsed:
                lineage, code = parsed
                axes = parse_axis_code(lineage, code)
                if axes:
                    return (lineage, code, axes)
    # 文本種族推導（無權威表與 token 時）
    text = str(card.get("stats", {}).get("race", ""))
    _head = text.split("／")[0].split("——")[0].split("（")[0].strip()
    # 魔女／術式適應體：魔法使用者，非任何軸譜系譜（未分類，人類身體＋術士機制）
    if "魔女" in _head or "術式適應體" in text:
        return (None, None, None)
    # 機械妖精：機械造物（機制種族=機械），非獸娘——避免「妖精」關鍵字誤導入物種軸
    if "機械妖精" in _head:
        return (None, None, None)
    if "龍娘" in text or "龍族" in text:
        return ("物種", "F-H-P", parse_axis_code("物種", "F-H-P"))
    if any(k in text for k in ("天翼種", "天使", "智天使", "邪神", "神明", "概念", "靈體", "神話", "世界意志", "欲墮魔", "精靈", "怪獸")):
        return ("神話種", "D1-O1-M2", parse_axis_code("神話種", "D1-O1-M2"))
    if any(k in text for k in ("狐", "貓", "兔", "狼", "蝙蝠", "拉米雅", "阿拉克涅", "哈比", "妖精", "魔物娘", "鼠", "納迦", "人魚", "海蛞蝓", "蛇", "兩棲", "獸娘")):
        return ("物種", "S-H-P", parse_axis_code("物種", "S-H-P"))
    if "AI" in text or "人造意識" in text or "特戰人形" in text:
        return ("AI", "F1-A2-O1", parse_axis_code("AI", "F1-A2-O1"))
    if "義體" in text or "賽博格" in text or "基因強化" in text:
        return ("義體人", "C2-H2-B2", parse_axis_code("義體人", "C2-H2-B2"))
    return (None, None, None)


# ════════════════════════════════════════════════════════════════
# 6. 五維度親和力
# ════════════════════════════════════════════════════════════════

def affinity_vector(lineage=None, axes=None):
    """計算五維度親和力 {維度: 0..1}（該系譜各軸位平均值；人類用基線）。"""
    if lineage and axes and lineage in _AXIS_TRAITS:
        traits = _AXIS_TRAITS[lineage]
        vec = [0.0] * len(DIMENSIONS)
        n = 0
        for axis_name, (code, _label) in axes.items():
            t = traits.get(axis_name, {}).get(code)
            if t:
                for i in range(len(DIMENSIONS)):
                    vec[i] += t[i]
                n += 1
        if n:
            return {DIMENSIONS[i]: vec[i] / n for i in range(len(DIMENSIONS))}
    return {DIMENSIONS[i]: HUMAN_AFFINITY[i] for i in range(len(DIMENSIONS))}


# ════════════════════════════════════════════════════════════════
# 7. 數值計算（由軸譜推導屬性加乘）
# ════════════════════════════════════════════════════════════════

def stat_modifiers(affinity: dict) -> dict:
    """回傳屬性加乘 dict：{hp, sp, atk, defense, spd, karma}（乘數，1.0=無加成）。"""
    phys = affinity.get("物質", 0.5)
    spir = affinity.get("靈性", 0.3)
    mech = affinity.get("機械", 0.1)
    ener = affinity.get("能量", 0.25)
    return {
        "hp": 0.7 + 0.4 * phys,
        "sp": 0.4 + 0.7 * ener + 0.3 * spir,
        "atk": 0.75 + 0.5 * phys,
        "defense": 0.75 + 0.3 * phys + 0.25 * mech,
        "spd": 0.75 + 0.4 * phys,
        "karma": 0.5 + 0.8 * spir,
    }


# ════════════════════════════════════════════════════════════════
# 8. 機制種族（由軸譜推導；取代 token 猜測）
# ════════════════════════════════════════════════════════════════

def mechanic_race_from_axis(lineage, axes, text_race: str) -> str:
    """由軸譜系譜＋文本種族推導機制種族（身體部位／種族任務用）。

    文本明示者優先（艦娘/魔女/機械妖精/人類），其餘依系譜：
      物種  → 龍娘為龍族、其餘獸娘
      AI    → 機械
      義體人→ 機械
      神話種→ 精靈
    """
    if "艦娘" in text_race:
        return "艦娘"
    # 取文本種族開頭的主詞（「／」「——」「（」前的部分）——避免「魔女學府」等場所詞
    # 或「人類形態」等描述詞誤判（如 CC-32 天空龍娘、CC-49 晞吶）
    head = text_race.split("／")[0].split("——")[0].split("（")[0].strip()
    if "魔女" in head or "術式適應體" in text_race:
        return "術士"
    if "機械妖精" in head:
        return "機械"
    if head in ("人類", "純人類", "變異人類") or ("人類" in text_race and "鬼族" in text_race):
        return "人類"
    if lineage == "物種":
        if "龍娘" in head or "龍族" in head or "龍人" in head:
            return "龍族"
        return "獸娘"
    if lineage == "AI":
        return "機械"
    if lineage == "義體人":
        return "機械"
    if lineage == "神話種":
        return "精靈"
    return "人類"


# ════════════════════════════════════════════════════════════════
# 9. 身體部位（由軸譜推導）
# ════════════════════════════════════════════════════════════════

_AXIS_BODY_PARTS = {
    "物種": {
        "H": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "tail", "claws"],
        "S": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "tail", "claws"],
        "C": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "tail", "claws"],
    },
    "AI": {
        "F0": ["spirit_body"],
        "F1": ["head", "torso", "cyber_limbs"],
        "F2": ["head", "torso", "left_arm", "right_arm", "cyber_limbs"],
        "F3": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "cyber_limbs"],
    },
    "義體人": {
        "H1": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "cyber_limbs"],
        "H2": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "cyber_limbs"],
        "H3": ["head", "torso", "cyber_limbs"],
    },
    "神話種": {
        "M1": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "spirit_body"],
        "M2": ["spirit_body"],
        "M3": ["head", "torso", "spirit_body"],
    },
}

def body_parts_from_axis(lineage, axes) -> list:
    """由軸譜推導身體部位清單（無軸譜時回傳人類部位）。"""
    if lineage and axes:
        parts = _AXIS_BODY_PARTS.get(lineage, {})
        # 物種用人形比例；AI 用人形模仿度；神話種用存在維度；義體人用外觀保留度
        for axis_name in ("人形比例", "人形模仿度", "外觀人形保留度", "存在維度"):
            entry = axes.get(axis_name)
            if entry:
                code = entry[0]
                if code in parts:
                    return parts[code]
        # 找不到對應軸位 → 該系譜預設
        defaults = {
            "物種": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "tail", "claws"],
            "AI": ["head", "torso", "cyber_limbs"],
            "義體人": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "cyber_limbs"],
            "神話種": ["spirit_body"],
        }
        return defaults.get(lineage, ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"])
    return ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]


# ════════════════════════════════════════════════════════════════
# 9b. 移動能力（飛行／渡水／水棲）— 依文本種族與軸譜判定
# ════════════════════════════════════════════════════════════════
# 文本權威（角色卡種族）：能飛的物種就能飛、艦娘本身就是艦艇不需搭船。
# 飛行關鍵字：哈比／天翼種／龍娘／龍族／機械妖精／天使／妖精／蝙蝠娘（有翼）
# 渡水（艦裝航行）：艦娘／星艦娘（艦裝即船，可自行航行）
# 水棲（游泳）：人魚／納迦／魚人／海蛞蝓等水生亞種

FLY_KEYWORDS = ["哈比", "天翼種", "龍娘", "龍族", "機械妖精", "天使", "妖精", "蝙蝠娘", "翼族", "有翼", "飛行"]
SAIL_KEYWORDS = ["艦娘", "星艦"]
SWIM_KEYWORDS = ["人魚", "納迦", "魚人", "海蛞蝓", "水棲"]


def movement_abilities(text_race: str = "", mechanic_race: str = "", lineage: str = "") -> dict:
    """判定角色的移動能力（依文本種族關鍵字，非 token 猜測）。

    回傳：{"fly": bool, "sail": bool, "swim": bool, "label": str, "speed_multiplier": float}
      fly  — 可飛行（飛越水域／直接到達水域場景）
      sail — 可自行航行（艦娘艦裝即船，不需小舟）
      swim — 可游泳渡水（水生亞種）
      speed_multiplier — 跨區移動速度倍率（相對徒步，飛行最快）
    """
    text = str(text_race or "")
    mech = str(mechanic_race or "")
    combined = text + " " + mech
    fly = any(kw in combined for kw in FLY_KEYWORDS)
    sail = any(kw in combined for kw in SAIL_KEYWORDS)
    swim = any(kw in combined for kw in SWIM_KEYWORDS)
    label_parts = []
    speed_multiplier = 1.0
    if fly:
        label_parts.append("可飛行")
        speed_multiplier = max(speed_multiplier, 2.0)
    if sail:
        label_parts.append("艦裝航行")
        speed_multiplier = max(speed_multiplier, 1.5)
    if swim:
        label_parts.append("可游泳")
    return {
        "fly": fly, "sail": sail, "swim": swim,
        "label": "、".join(label_parts),
        "speed_multiplier": speed_multiplier,
    }


# ════════════════════════════════════════════════════════════════
# 10. 交互判定引擎
# ════════════════════════════════════════════════════════════════

# 交互門檻：各維度的最小親和力需求
THRESHOLDS = {
    "物質": 0.5,   # 實體裝備（武器/防具/盔甲）
    "靈性": 0.5,   # 靈裝／靈性道具
    "機械": 0.5,   # 義體／機械升級
    "能量": 0.2,   # 魔力／元素道具（人類魔法使用者基線 0.25 可達）
    "資訊": 0.5,   # AI／資料交互
}

def can_interact(affinity: dict, dimension: str, min_value=None) -> bool:
    """是否可交互：角色該維度親和力 ≥ 門檻。"""
    thr = THRESHOLDS.get(dimension, 0.5) if min_value is None else min_value
    return affinity.get(dimension, 0.0) >= thr


def interaction_depth(affinity: dict, dimension: str, min_value=None) -> float:
    """交互深度 0..1：超過門檻的幅度（超過越多越深）。"""
    thr = THRESHOLDS.get(dimension, 0.5) if min_value is None else min_value
    v = affinity.get(dimension, 0.0)
    if v < thr:
        return 0.0
    return min(1.0, (v - thr) / (1.0 - thr))


def item_dimension(item_def: dict) -> str:
    """由物品 tags 判定主交互維度（無匹配回傳 None）。"""
    tags = item_def.get("tags", [])
    if not tags:
        return None
    tags = set(tags)
    if tags & {"spiritual", "spirit", "aura", "靈"}:
        return "靈性"
    if tags & {"magic", "element", "mana", "energy", "魔"}:
        return "能量"
    if tags & {"mechanical", "cyber", "machine", "tech", "mechanism"}:
        return "機械"
    if tags & {"data", "info", "code", "ai"}:
        return "資訊"
    if tags & {"spiritual", "spirit", "aura", "靈"}:
        return "靈性"
    # 艦裝（naval）與龍族裝備（draconic）是實體裝備，非機械/能量維度
    return "物質"  # 其餘（含 naval/draconic/beast/武器/防具/無 tag）皆為實體


# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L4]
# =============================================================================
# 魔法類製作判定：產物 tags 標 magic/elemental/energy，或名稱含基礎魔法詞。
# 對照文本：術士／魔女／術式適應體等能量維度角色才能調製魔法物品；
# 純人類（能量親和力 0.15 基線）無法製作魔力藥水、靈力藥、法杖、護身符。
MAGIC_TAGS = {"magic", "elemental", "energy"}
MAGIC_NAME_KW = ("魔力", "靈力", "法杖", "護身符")


def is_magic_craft(item_name: str = "", tags=None) -> bool:
    """配方產物是否屬魔法類（製作需要能量/靈性親和力）。"""
    if tags and any(t in MAGIC_TAGS for t in tags):
        return True
    return any(kw in str(item_name or "") for kw in MAGIC_NAME_KW)


def check_craft_axis(character, recipe) -> tuple:
    """檢查角色能否製作此配方 → (ok, 原因)。

    魔法類配方要求能量或靈性親和力 ≥ 0.5（對齊 evaluate_equipment 門檻）；
    一般配方（鐵劍/藥草/修復等）無軸譜限制。
    """
    result_item = (recipe or {}).get("result_item", "")
    tags = None
    try:
        from sim_systems import get_item_def
        _d = get_item_def(result_item)
        tags = _d.get("tags", []) if _d else []
    except Exception:
        tags = []
    if not is_magic_craft(result_item, tags):
        return True, ""
    affinity = (character or {}).get("axis", {}).get("affinity", {}) or {}
    if affinity.get("能量", 0.0) >= 0.5 or affinity.get("靈性", 0.0) >= 0.5:
        return True, ""
    return False, "軸譜不符：%s 是魔法類物品，需要能量或靈性親和力 ≥ 0.5" % result_item


# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L4]
# =============================================================================
# 技能卡（SK-01~22）學習的軸譜判定：魔法卡需能量/靈性、義體卡需機械、
# 妖精/精靈/天翼種族技需靈性、戰鬥卡需物質等——軸譜決定可學性。
SKILL_CARD_AXIS = {
    "magic":     (("能量", "靈性"), 0.4),  # 道術/魔炮/奇蹟/四季施法
    "tech":      (("資訊",), 0.4),           # 通訊/網絡/駭客
    "craft":     (("機械",), 0.3),           # 機械加工工藝
    "combat":    (("物質",), 0.3),           # 格鬥/弓道/陷阱
    "knowledge": (("資訊",), 0.3),           # 文獻/生態/地質學
}
SKILL_CARD_RACE_KW = {  # 名稱關鍵字 → 所需維度（優先於 category）
    "義體": (("機械",), 0.4),
    "妖精": (("靈性",), 0.4),
    "精靈": (("靈性",), 0.4),
    "天翼": (("靈性",), 0.4),
    "駭客": (("資訊",), 0.4),  # 駭客比通訊/上網更進階，同樣需要資訊維度
}


def skill_card_axis(card) -> tuple:
    """技能卡學習所需軸譜 → ((維度...), 門檻)。無限制回傳 ((), 0.0)。"""
    name = str((card or {}).get("name", ""))
    for kw, req in SKILL_CARD_RACE_KW.items():
        if kw in name:
            return req
    cat = str((card or {}).get("category", ""))
    return SKILL_CARD_AXIS.get(cat, ((), 0.0))


# 技能卡 category → 實際技能類別（magic→combat 魔法戰鬥、stealth→exploration 潛伏、tech→craft 操作）
SKILL_CARD_TO_SKILL = {
    "knowledge": "knowledge", "craft": "craft", "combat": "combat",
    "magic": "combat", "stealth": "exploration", "tech": "craft", "general": "knowledge",
}


def skill_card_target_skill(card) -> str:
    return SKILL_CARD_TO_SKILL.get(str((card or {}).get("category", "")), "knowledge")


def evaluate_equipment(affinity: dict, item_def: dict):
    """評估裝備交互 → (可否裝備, 交互深度, 維度, 原因)。

    例：靈體/概念（M2，物質親和 0.05）無法裝備實體盔甲；可裝備靈裝。
    """
    dim = item_dimension(item_def)
    if dim is None:
        return (True, 1.0, "物質", "無特殊需求")
    can = can_interact(affinity, dim)
    depth = interaction_depth(affinity, dim)
    reason = ""
    if not can:
        reason = f"缺少{_dim_label(dim)}親和力（{affinity.get(dim, 0):.2f} < {THRESHOLDS.get(dim, 0.5):.2f}）"
    return (can, depth, dim, reason)


def evaluate_consumable(affinity: dict, item_def: dict):
    """評估使用道具 → (可使用, 交互深度, 維度, 原因)。

    消耗品任何角色皆可使用（使用＝即時消耗，非穿戴，不受身體形體限制）；
    交互深度反映契合度——親和力越高效果越好（如靈體飲靈力藥水效果加乘）。
    實體消耗品（治療藥水等）深度 1.0。
    """
    dim = item_dimension(item_def)
    if dim is None or dim == "物質":
        return (True, 1.0, dim or "物質", "")
    depth = affinity.get(dim, 0.0)  # 深度＝該維度親和力本身（0..1）
    return (True, depth, dim, "")


def evaluate_quest(affinity: dict, required: dict):
    """評估任務軸譜條件 → (符合, 深度, 未符合清單)。

    required 例：{"維度": {"能量": 0.5, "靈性": 0.3}} 或 {"系譜": "神話種"}
    """
    missing = []
    dims = required.get("維度", {})
    for dim, minv in dims.items():
        if not can_interact(affinity, dim, minv):
            missing.append(f"{dim} ≥ {minv}")
    if missing:
        return (False, 0.0, missing)
    depths = [interaction_depth(affinity, dim, minv) for dim, minv in dims.items()] or [1.0]
    return (True, sum(depths) / len(depths), [])


def _dim_label(dim: str) -> str:
    return {
        "物質": "物質（實體）", "靈性": "靈性（靈體/概念）", "機械": "機械（義體/科技）",
        "能量": "能量（魔力/元素）", "資訊": "資訊（AI/資料）",
    }.get(dim, dim)


def dimension_label(dim: str) -> str:
    """公開的維度顯示名（供 run_game 等外部模組使用）。"""
    return _dim_label(dim)


# ════════════════════════════════════════════════════════════════
# 10b. NPC 主要交互維度（交流／送禮好感契合）
# ════════════════════════════════════════════════════════════════
# 依軸譜語意：NPC 的文本種族 → 其主要交互維度。玩家在該維度的親和力深度
# 反映「與 NPC 的契合度」——同屬靈性的精靈 NPC 與靈體角色交流更有共鳴。

NPC_DIMENSION_KEYWORDS = [
    ("資訊", ["AI", "人造意識", "機械妖精", "特戰人形", "機械人", "程式"]),
    ("機械", ["艦娘", "星艦", "義體", "賽博格", "機娘", "機械"]),
    ("能量", ["術士", "魔女", "術式適應體", "魔法", "元素"]),
    ("靈性", ["精靈", "神話", "神明", "龍", "天使", "惡魔", "妖狐", "狐妖", "靈體", "概念", "天翼", "幽靈", "魔物"]),
    ("物質", ["獸娘", "貓娘", "兔", "狼", "人魚", "拉米雅", "哈比", "蝙蝠", "狐", "海蛞蝓", "蛇"]),
]


def npc_affinity_dimension(race: str) -> str:
    """由 NPC 文本種族推其主要交互維度（交流/送禮好感契合用）。

    無匹配（如純人類）回傳空字串——不施加軸譜加成。
    """
    text = str(race or "")
    for dim, kws in NPC_DIMENSION_KEYWORDS:
        if any(kw in text for kw in kws):
            return dim
    return ""


# 未分類角色（無軸譜）依機制種族的親和力補強——讓機械妖精能裝義體、術士能用魔導器
MECH_AFFINITY_BOOST = {
    "艦娘": {"機械": 0.40},  # 人類基線 0.15 + 0.40 = 0.55 ≥ 0.5 機械門檻
    "術士": {"能量": 0.35, "靈性": 0.10},
    "機械": {"機械": 0.40},
    "龍族": {"能量": 0.25},
    "精靈": {"靈性": 0.40, "能量": 0.20},
    "獸娘": {"物質": 0.05},
    "人類": {},
}


# ════════════════════════════════════════════════════════════════
# 11. 顯示輔助
# ════════════════════════════════════════════════════════════════

def axis_display(lineage, code, axes):
    """人類可讀的軸譜描述，如「物種｜ S-H-P（標準種、類人型、純血）」。"""
    if not lineage or not axes:
        return "其他｜ 人類基線"
    labels = "、".join(label for _c, label in axes.values())
    return f"{lineage}｜ {code}（{labels}）"


def affinity_display(affinity: dict) -> str:
    parts = " ".join(f"{dim}:{affinity.get(dim, 0):.2f}" for dim in DIMENSIONS)
    return parts
