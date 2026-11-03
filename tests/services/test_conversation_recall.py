"""純本地路徑的「我剛才說什麼」回憶層。

回憶層的兩個缺陷都在 2026-11-01 的純本地對話量測裡現形：

1. 回憶用「編碼器相似度」挑句子，於是「我剛才說我幾歲？」挑到只因為開頭是
   「我剛」的無關句子；代名詞不是屬性。
2. 屬性的匹配只要沾到一個字就算命中，於是「我剛才說我的貓叫什麼？」在貓還
   沒教之前拿狗來回答——那是把錯答案包裝成記憶。

這裡守住的是：問題問的是哪個屬性，答案就必須帶著那個屬性；帶著的程度用
候選池裡的稀有度（idf）衡量；同分時取最近說的。以及「陳述句才會被記住」
不是白名單（白名單等於背下標準集的句型）。
"""

import pytest
from services.llm.memory_integration import (
    _attribute_words,
    _is_teaching_statement,
    _semantic_match,
)


def _match(question: str, statements):
    return _semantic_match(statements, set(_attribute_words(question)))


# --------------------------------------------------------------------------- #
# The attribute a question names
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "question, expected",
    [
        # The meta-question prefix and the pronoun are not the attribute.
        ("我剛才說我住哪裡？", ["住"]),
        ("我剛剛說過我幾歲？", ["歲"]),
        # The interrogative phrase is the shape of the ask, not its subject.
        ("我剛才說我的狗叫什麼？", ["狗", "叫"]),
        ("我剛才說我下班怎麼回？", ["下", "班", "回"]),
        ("我剛才說我幾點開會？", ["點", "開"]),
        # A question with nothing but the meta-prefix names no attribute.
        ("我剛才說什麼？", []),
    ],
)
def test_attribute_words_name_what_is_asked(question, expected):
    assert _attribute_words(question) == expected


# --------------------------------------------------------------------------- #
# Matching a statement to the asked-about attribute
# --------------------------------------------------------------------------- #
FACTS = [
    "我養了一隻叫豆豆的狗",
    "我叫小明",
    "我的生日是九月十號",
    "我今天用紅色背包",
    "我喜歡喝拿鐵",
    "我的手機是藍色的",
    "我喜歡的球類是籃球",
    "我下班搭捷運",
    "我下午三點開會",
    "我住在新竹",
    "我今年三十五歲",
]


@pytest.mark.parametrize(
    "question, expected",
    [
        ("我剛才說我的生日是哪天？", "九月十號"),
        ("我剛才說我的手機是什麼顏色？", "藍色"),
        ("我剛才說我喜歡哪種球類？", "籃球"),
        ("我剛才說我下班怎麼回？", "捷運"),
        ("我剛才說我住哪裡？", "新竹"),
        ("我剛才說我幾歲？", "三十五"),
        ("我剛才說我今天用什麼顏色的背包？", "紅色"),
        ("我剛才說我的狗叫什麼？", "豆豆"),
    ],
)
def test_the_statement_that_carries_the_attribute_wins(question, expected):
    statement = _match(question, FACTS)
    assert statement is not None
    assert expected in statement


def test_a_shared_common_word_is_not_a_match():
    """「我的貓叫什麼」在貓還沒說過之前不能拿狗來回答。

    叫 is shared with the dog (and with the user's own name); 貓 appears
    nowhere. One common character is not the attribute.
    """
    assert _match("我剛才說我的貓叫什麼？", FACTS) is None


def test_an_unrelated_question_abstains():
    assert _match("我剛才說我養的狗叫什麼？", ["我住在台北"]) is None
    assert _match("我剛才說什麼？", FACTS) is None


def test_the_most_recent_statement_wins_a_tie():
    """「剛才說」是指示性的：兩個都帶著屬性時，取最近說的那一句。"""
    recent_first = ["我喜歡喝綠茶", "我喜歡喝拿鐵"]
    assert _match("我剛才說我喜歡喝什麼？", recent_first) == "我喜歡喝綠茶"


# --------------------------------------------------------------------------- #
# Which statements are facts at all
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "message",
    [
        "我叫小明",
        "我今年三十五歲",
        "我每週三跑步",
        "我早上七點起床",
        "我用的是台電的電",
        "我住在台北",
        "I just moved to Taipei",
    ],
)
def test_a_first_person_statement_is_a_fact(message):
    assert _is_teaching_statement(message)


@pytest.mark.parametrize(
    "message",
    [
        # A question is not a statement.
        "我剛才說我住哪裡？",
        # A question without a question mark is still a question.
        "我的電話是幾號",
        "我的貓叫什麼",
        # A feeling gets the empathetic reply, not "記住囉".
        "我今天很累",
        "我今天心情不好",
        # A request is not a fact.
        "我想去旅行",
        "幫我訂票",
        "可以嗎？",
        # Not knowing something is not a fact either.
        "我不知道",
        "",
    ],
)
def test_questions_feelings_and_requests_are_not_facts(message):
    assert not _is_teaching_statement(message)


# --------------------------------------------------------------------------- #
# The acknowledgment is a fallback, never a layer that covers the core
# --------------------------------------------------------------------------- #
class _ServiceWithBackends:
    def __init__(self, backend_names):
        self.backends = {name: object() for name in backend_names}


def _ack(service, message):
    import asyncio

    from services.llm.memory_integration import MemoryIntegration

    return asyncio.run(MemoryIntegration(service).try_teaching_ack(message))  # type: ignore[arg-type]


def test_the_native_path_acknowledges_a_fact():
    """沒有可生成的後端時，「記住囉」比罐頭問候好。"""
    response = _ack(_ServiceWithBackends(["unified"]), "我今年三十五歲")
    assert response is not None
    assert "三十五歲" in response.text
    assert response.route == "MEMORY"


def test_the_acknowledgment_does_not_repeat_the_sentence():
    """鸚鵡是缺陷，不是回覆：ack 只能說出那件事的值，不能重述整句。

    "記住囉！我的貓叫小花。" 幾乎就是使用者說的整句（標準集把它判成 parrot）。
    有值可命名時說值，沒有時就只確認——不靠覆述使用者來假裝聽懂了。
    """
    response = _ack(_ServiceWithBackends(["unified"]), "我的貓叫小花")
    assert response is not None
    assert "小花" in response.text
    assert "我的貓叫" not in response.text

    bare = _ack(_ServiceWithBackends(["unified"]), "我負責專案管理")
    assert bare is not None
    assert "我負責專案管理" not in bare.text


def test_a_clause_shaped_value_is_not_echoed_back():
    """值是「一個詞」時才說得出口；值是一整句時，複述它就是鸚鵡。

    「記住囉，彈吉他和看電影！」有九成是使用者的原話，那不是回應。寧可只
    確認（說得少），也不要用覆述稀釋成看起來像聽懂了。
    """
    response = _ack(_ServiceWithBackends(["unified"]), "我的興趣是彈吉他和看電影")
    assert response is not None
    assert "彈吉他" not in response.text


@pytest.mark.parametrize(
    "fact",
    [
        "我的貓叫小花",
        "我今年三十五歲",
        "我住在台北",
        "我在圖書館工作",
        "我每週三跑步",
        "我的電話號碼是 0912345678",
        "我的興趣是彈吉他和看電影",
        "我負責專案管理",
    ],
)
def test_the_acknowledgment_is_never_a_parrot(fact):
    """用標準集自己的判定確認：ack 在任何句型下都不算覆述。

    這條不是把判定調鬆——它就是把「ack 不得覆述」綁在量測用的同一條規則上，
    免得改寫 ack 時悄悄退回原點。
    """
    from ai.response.human_speech import PARROT, StandardItem, classify_state

    response = _ack(_ServiceWithBackends(["unified"]), fact)
    assert response is not None
    assert classify_state(StandardItem(kind="dialogue", message=fact), response.text) != PARROT


def test_a_third_person_fact_is_acknowledged_not_answered_about_weather(tmp_path, monkeypatch):
    """「Zorblax 的首都是 Quuxville。」教了一個事實，就該確認，不是聊聊天氣。

    實測（2026-11-02，audit_placement）：記憶層把這個事實存好了，回覆卻是
    「雨天有雨天的趣味…」——雞同鴨講，而且讓「這句到底是知識還是記憶」在
    稽核裡變成未知。確認句屬記憶層（值來自使用者的句子）。
    """
    from ai.memory.taught_facts import get_taught_facts, reset_taught_facts

    monkeypatch.setenv("ANGELA_TAUGHT_FACTS", str(tmp_path / "ack.json"))
    reset_taught_facts()
    try:
        get_taught_facts().learn_from_turn("Zorblax 的首都是 Quuxville。")
        response = _ack(_ServiceWithBackends(["unified"]), "Zorblax 的首都是 Quuxville。")
        assert response is not None
        assert response.route == "MEMORY"
        assert "記住囉" in response.text
        # 沒有教會任何事的句子不得被背書：假裝記住了是另一種說謊。
        assert _ack(_ServiceWithBackends(["unified"]), "今天天氣不錯") is None
    finally:
        reset_taught_facts()


def test_a_generative_backend_is_not_pre_empted_by_the_frame():
    """接得上真正會生成答案的後端時，罐頭框架不得先回答。

    模板智能不屬於智能。表現層（固定框架）如果排在能回答的後端前面，
    就會重演「模板取代核心」——量測上核心分被罐頭蓋掉，還查不出來。
    """
    service = _ServiceWithBackends(["unified", "openai"])
    assert _ack(service, "我今年三十五歲") is None
