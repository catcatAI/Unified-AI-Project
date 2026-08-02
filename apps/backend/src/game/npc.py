"""NPC system — default NPCs with routines, schedules, relationships."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NPCRoutine:
    """A time-based routine for an NPC."""
    time_start: int  # hour (0-23)
    time_end: int
    activity: str
    location: str = ""
    mood: str = "neutral"


@dataclass
class NPC:
    """Non-player character with behavior."""
    card_id: str
    name: str
    description: str = ""
    personality: str = ""
    hp: int = 100
    max_hp: int = 100
    spirit: int = 50
    max_spirit: int = 50
    mood: str = "neutral"
    disposition: int = 50  # 0=hostile, 50=neutral, 100=friendly
    routines: list[NPCRoutine] = field(default_factory=list)
    dialogue_pool: list[str] = field(default_factory=list)
    tokens: list[dict] = field(default_factory=list)
    current_location: str = ""
    is_alive: bool = True

    def get_current_activity(self, hour: int = 12) -> str:
        for r in self.routines:
            if r.time_start <= r.time_end:
                match = r.time_start <= hour < r.time_end
            else:
                match = hour >= r.time_start or hour < r.time_end
            if match:
                return r.activity
        return self._i18n_fallback("未知", "Unknown", "不明")

    def _i18n_fallback(self, zh: str, en: str, ja: str) -> str:
        lang = getattr(self, '_lang', 'zh')
        return {"zh": zh, "en": en, "ja": ja}.get(lang, zh)

    def get_greeting(self) -> str:
        if self.disposition >= 80:
            greetings = [
                self._i18n_fallback(
                    f"「{self.name}」向你微笑點頭。",
                    f"{self.name} smiles and nods at you.",
                    f"「{self.name}」は微笑んでうなずいた。",
                ),
                self._i18n_fallback(
                    f"「{self.name}」看起來很高興見到你。",
                    f"{self.name} seems happy to see you.",
                    f"「{self.name}」は会えて嬉しい様子だ。",
                ),
            ]
        elif self.disposition >= 50:
            greetings = [
                self._i18n_fallback(
                    f"「{self.name}」看了你一眼。",
                    f"{self.name} glances at you.",
                    f"「{self.name}」はあなたを見た。",
                ),
                self._i18n_fallback(
                    f"「{self.name}」點頭示意。",
                    f"{self.name} nods in acknowledgment.",
                    f"「{self.name}」はうなずいた。",
                ),
            ]
        elif self.disposition >= 20:
            greetings = [
                self._i18n_fallback(
                    f"「{self.name}」面無表情地看著你。",
                    f"{self.name} looks at you expressionlessly.",
                    f"「{self.name}」は無表情で見ている。",
                ),
                self._i18n_fallback(
                    f"「{self.name}」似乎不太想說話。",
                    f"{self.name} doesn't seem interested in talking.",
                    f"「{self.name}」は話す気配がない。",
                ),
            ]
        else:
            greetings = [
                self._i18n_fallback(
                    f"「{self.name}」瞪了你一眼。",
                    f"{self.name} glares at you.",
                    f"「{self.name}」はにらみつけた。",
                ),
                self._i18n_fallback(
                    f"「{self.name}」轉身背對你。",
                    f"{self.name} turns away from you.",
                    f"「{self.name}」は背を向けた。",
                ),
            ]
        return random.choice(greetings)

    def get_dialogue(self) -> str:
        if self.dialogue_pool:
            lang = getattr(self, '_lang', 'zh')
            if isinstance(self.dialogue_pool, dict):
                lines = self.dialogue_pool.get(lang, self.dialogue_pool.get("zh", []))
            else:
                lines = self.dialogue_pool
            if lines:
                return random.choice(lines)
        return self._i18n_fallback(
            f"「{self.name}」沉默不語。",
            f"{self.name} is silent.",
            f"「{self.name}」は黙っている。",
        )

    def react_to_player(self, player_action: str, disposition_change: int = 0) -> str:
        self.disposition = max(0, min(100, self.disposition + disposition_change))
        if self.disposition >= 80:
            return self._i18n_fallback(
                f"「{self.name}」積極地回應你的行動。",
                f"{self.name} responds actively to your action.",
                f"「{self.name}」は積極的に応答した。",
            )
        elif self.disposition >= 50:
            return self._i18n_fallback(
                f"「{self.name}」觀察著你的行動。",
                f"{self.name} watches your action.",
                f"「{self.name}」はあなたの行動を観察している。",
            )
        elif self.disposition >= 20:
            return self._i18n_fallback(
                f"「{self.name}」對你的行動保持警惕。",
                f"{self.name} is wary of your action.",
                f"「{self.name}」は警戒している。",
            )
        else:
            return self._i18n_fallback(
                f"「{self.name}」對你的行動感到不滿。",
                f"{self.name} is displeased with your action.",
                f"「{self.name}」は不満そうだ。",
            )


# ─── Default NPC definitions ───

DEFAULT_NPCS: dict[str, dict] = {
    "小狐丸": {
        "card_id": "CC-18",
        "personality": "沉默寡言但忠誠，冰晶操控能力者",
        "disposition": 70,
        "routines": [
            NPCRoutine(6, 10, "在火山口岩洞整理冰晶", "鏡湖火山口", "calm"),
            NPCRoutine(10, 14, "巡視鏡湖周邊", "鏡湖", "alert"),
            NPCRoutine(14, 18, "在岩洞中休息", "鏡湖火山口", "rest"),
            NPCRoutine(18, 22, "與左間小蒼蘭交流", "秘密鐵工廠", "friendly"),
            NPCRoutine(22, 6, "睡眠", "鏡湖火山口", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「冰層下面的水在流動。聽。」",
                "「不要踩那塊石頭。它不喜歡被踩。」",
                "「……今天空氣裡的靈子很安靜。」",
                "「你想看看冰晶嗎？我可以雕一個。」",
            ],
            "en": [
                '"The water flows beneath the ice. Listen."',
                '"Don\'t step on that rock. It doesn\'t like it."',
                '"...The spirit particles are quiet today."',
                '"Want to see the ice crystals? I can carve one."',
            ],
            "ja": [
                "「氷の下を水が流れている。聞いて。」",
                "「その石を踏んじゃだめ。嫌がってる。」",
                "「……今日の空気中の霊子は静かだ。」",
                "「氷結晶を見たいか？彫ってあげる。」",
            ],
        },
    },
    "左間小蒼蘭": {
        "card_id": "CC-17",
        "personality": "工匠之女，對機械有天生的理解力",
        "disposition": 65,
        "routines": [
            NPCRoutine(7, 12, "在鐵工廠工作", "秘密鐵工廠", "focused"),
            NPCRoutine(12, 13, "午餐休息", "秘密鐵工廠", "rest"),
            NPCRoutine(13, 18, "繼續工作", "秘密鐵工廠", "focused"),
            NPCRoutine(18, 21, "整理工具和圖紙", "秘密鐵工廠", "calm"),
            NPCRoutine(21, 7, "睡眠", "女僕長宿舍", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「這個零件的弧度……不對，再試一次。」",
                "「你帶了什麼工具來？讓我看看。」",
                "「小狐丸說你對機械有興趣？」",
                "「幫我把那個錘子遞過來，謝謝。」",
            ],
            "en": [
                '"This part\'s curve... wrong. Try again."',
                '"What tools did you bring? Let me see."',
                '"Kogitsune said you\'re interested in machines?"',
                '"Pass me that hammer, please."',
            ],
            "ja": [
                "「この部品の弧度……違う、もう一度。」",
                "「持ってきた工具を見せてくれ。」",
                "「小狐丸が君は機械に興味があると言ったぞ。」",
                "「そのハンマーを取って。ありがとう。」",
            ],
        },
    },
    "晴空": {
        "card_id": "CC-19",
        "personality": "8歲少女，翼膜未完全展開，好奇心強",
        "disposition": 75,
        "routines": [
            NPCRoutine(8, 12, "在學府上課", "魔女學府", "curious"),
            NPCRoutine(12, 14, "午餐和玩耍", "魔女學府", "happy"),
            NPCRoutine(14, 17, "下午課程", "魔女學府", "focused"),
            NPCRoutine(17, 20, "在翼膜中練習飛行", "魔女學府", "excited"),
            NPCRoutine(20, 8, "睡眠", "魔女學府", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「你看！我的翼膜今天張開了一點點！」",
                "「導師說我還不能飛太高……但我可以飄起來了！」",
                "「你想聽我講翼膜的事嗎？我超了解的！」",
                "「今天上課的時候，我打了一個大噴嚏，然後翼膜差點 fully 展開！」",
            ],
            "en": [
                '"Look! My wings opened a little today!"',
                '"The teacher says I can\'t fly high yet... but I can float!"',
                '"Want to hear about wings? I know everything!"',
                '"In class today I sneezed and my wings almost fully opened!"',
            ],
            "ja": [
                "「見て！今日翼がちょっと開いたの！」",
                "「先生はまだ高く飛べないって……でも浮けるんだよ！」",
                "「翼の話を聞きたい？めっちゃ詳しいんだから！」",
                "「今日の授業でくしゃみしたら、翼がほぼ fully 開きかけた！」",
            ],
        },
    },
    "紅": {
        "card_id": "CC-21",
        "personality": "便利店店員，溫柔善良，默默照顧每個人",
        "disposition": 80,
        "routines": [
            NPCRoutine(6, 10, "整理貨架和開店準備", "便利店", "calm"),
            NPCRoutine(10, 18, "值班看店", "便利店", "friendly"),
            NPCRoutine(18, 22, "晚班", "便利店", "friendly"),
            NPCRoutine(22, 6, "睡眠", "便利店樓上", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「歡迎光臨。今天有新到的布丁喔。」",
                "「要不要再買一個茶葉蛋？今天特別好吃。」",
                "「外面好像要下雨了，帶傘了嗎？」",
                "「慢慢挑，不急。」",
            ],
            "en": [
                '"Welcome. We have new pudding today."',
                '"Want another tea egg? They\'re extra good today."',
                '"Looks like rain. Did you bring an umbrella?"',
                '"Take your time, no rush."',
            ],
            "ja": [
                "「いらっしゃい。今日プリン新着だよ。」",
                "「お茶卵、もう一つどう？今日特に美味しい。」",
                "「外、雨みたい。傘持ってきた？」",
                "「ゆっくり見てね、急がなくていいから。」",
            ],
        },
    },
    "晞咕萊雅": {
        "card_id": "CC-38",
        "personality": "圖書館守護者，理性冷靜，對書籍有強烈保護欲",
        "disposition": 55,
        "routines": [
            NPCRoutine(8, 18, "巡視書架和修補書籍", "中央大圖書館", "focused"),
            NPCRoutine(18, 20, "整理修補記錄", "中央大圖書館", "calm"),
            NPCRoutine(20, 8, "睡眠", "中央大圖書館", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「請保持安靜。這裡是圖書館。」",
                "「那本書已經被預約了。你可以看其他的。」",
                "「你翻書的聲音太大了。」",
                "「……這本書的保存狀況不錯。」",
            ],
            "en": [
                '"Please be quiet. This is a library."',
                '"That book is reserved. You can read others."',
                '"You\'re turning pages too loudly."',
                '"...This book is in good condition."',
            ],
            "ja": [
                "「静かにして。ここは図書館だ。」",
                "「その本は予約済みだ。他の本を読んでくれ。」",
                "「ページをめくる音が大きい。」",
                "「……この本の保存状態はいい。」",
            ],
        },
    },
    "髂審芬蒂": {
        "card_id": "CC-40",
        "personality": "阿拉克涅見習生，古籍修補專家，表面毒舌內在可靠",
        "disposition": 50,
        "routines": [
            NPCRoutine(8, 18, "古籍縫合與概念加固", "中央大圖書館", "focused"),
            NPCRoutine(18, 20, "整理工具", "中央大圖書館", "calm"),
            NPCRoutine(20, 8, "睡眠", "中央大圖書館", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「別碰那本書。你的手太粗糙了。」",
                "「概念加固需要時間。你可以在旁邊等。」",
                "「芬喀涅！不要把木屑掉在我的工作台上！」",
                "「……這本書的裝訂還能撐大概五十年。還好。」",
            ],
            "en": [
                '"Don\'t touch that book. Your hands are too rough."',
                '"Concept reinforcement takes time. Wait over there."',
                '"Fenkani! Don\'t drop sawdust on my workbench!"',
                '"...This binding will last another fifty years. Fine."',
            ],
            "ja": [
                "「その本を触るな。手が荒すぎる。」",
                "「概念補強には時間がかかる。そんで待ってろ。」",
                "「芬喀涅！お前の作業台に木くずを落とすな！」",
                "「……この製本はあと50年はもつ。まあいい。」",
            ],
        },
    },
    "芬喀涅": {
        "card_id": "CC-41",
        "personality": "阿拉克涅力量型，書架維護員，務實溫暖",
        "disposition": 55,
        "routines": [
            NPCRoutine(7, 12, "搬運和更換書架", "中央大圖書館", "focused"),
            NPCRoutine(12, 13, "午餐", "中央大圖書館", "rest"),
            NPCRoutine(13, 18, "繼續維護", "中央大圖書館", "focused"),
            NPCRoutine(18, 8, "睡眠", "中央大圖書館", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「這根樑大概三噸。我一個人扛得動。」",
                "「你聞到了嗎？那本書快壞了。讓我看看。」",
                "「阿芬！不要把木屑——我知道了我知道了。」",
                "「要不要幫忙？我可以教你怎么搬東西。」",
            ],
            "en": [
                '"This beam is about three tons. I can carry it alone."',
                '"Smell that? That book is about to rot. Let me check."',
                '"Fenkani! Don\'t drop the—I know, I know."',
                '"Need help? I can teach you how to carry things."',
            ],
            "ja": [
                "「この梁は3トンくらい。一人で持てる。」",
                "「匂うだろ？あの本がもうすぐ壊れる。見てみる。」",
                "「阿芬！木くずを——わかったわかった。」",
                "「手伝おうか？運び方を教えるよ。」",
            ],
        },
    },
    "夜鈴": {
        "card_id": "CC-51",
        "personality": "蝙蝠娘學生，自封校園情感顧問，自己從未談過戀愛",
        "disposition": 65,
        "routines": [
            NPCRoutine(8, 12, "上課", "方碑丘", "curious"),
            NPCRoutine(12, 14, "午餐+戀愛諮詢", "方碑丘", "excited"),
            NPCRoutine(14, 17, "下午課+觀察同學", "方碑丘", "focused"),
            NPCRoutine(17, 20, "超音波飛行練習", "方碑丘", "happy"),
            NPCRoutine(20, 8, "睡眠", "方碑丘", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「你要戀愛諮詢嗎？我免費的！」",
                "「我給過47個人建議，12對結婚了。但我自己……」",
                "「你看那個誰？我覺得他對你有意思！」",
                "「不要告訴別人，但我觉得紅先生好像有女朋友了。」",
            ],
            "en": [
                '"Need love advice? I\'m free!"',
                '"I gave advice to 47 people, 12 got married. But me..."',
                '"See that person? I think they like you!"',
                '"Don\'t tell anyone, but I think Red has a girlfriend."',
            ],
            "ja": [
                "「恋愛相談する？無料だよ！」",
                "「47人にアドバイスして、12組結婚した。でも私自身は……」",
                "「あの人のこと見てる？君に気があると思う！」",
                "「内緒だけど、紅先生には彼女がいるみたい。」",
            ],
        },
    },
    "翎翾": {
        "card_id": "CC-50",
        "personality": "哈比快遞員，熱血愛競速， deliveries最快",
        "disposition": 70,
        "routines": [
            NPCRoutine(6, 18, "送快遞（全城跑）", "工業區", "excited"),
            NPCRoutine(18, 20, "在巢穴休息", "工業區", "rest"),
            NPCRoutine(20, 6, "睡眠", "工業區", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「有包裹！讓我看看地址——哦，就在三條街外。兩分鐘。」",
                "「你剛才看到我飛過去了嗎？那是我的最快速度！」",
                "「老王的卡車太慢了。如果他能飛——算了。」",
                "「紅先生的便利店是我最常停靠的補給點。」",
            ],
            "en": [
                '"Package! Let me check the address—oh, three streets away. Two minutes."',
                '"Did you see me fly by? That was my top speed!"',
                '"Old Wang\'s truck is too slow. If he could fly—never mind."',
                '"Red\'s convenience store is my most frequent stop."',
            ],
            "ja": [
                "「荷物！住所は——お、3ブロック先。2分で着く。」",
                "「私、今飛んでたの見た？最高速度だよ！」",
                "「王さんのトラックは遅すぎる。飛べたらな——まあいい。」",
                "「紅さんのコンビニは一番よく行く補給ポイント。」",
            ],
        },
    },
    "深痕·裂脊": {
        "card_id": "CC-65",
        "personality": "納迦地熱維護員，沉默犧牲型，修了120年管道",
        "disposition": 60,
        "routines": [
            NPCRoutine(0, 24, "巡視和修補地熱管道", "黑淵台", "focused"),
        ],
        "dialogue_pool": {
            "zh": [
                "「管道不能停。停，城就冷。」",
                "「……這條裂縫是我昨天補的。又漏了。」",
                "「你不需要知道我的名字。只要熱泉沒斷就好。」",
                "「……120年了。每一條裂縫都是我補的。」",
            ],
            "en": [
                '"The pipes can\'t stop. If they do, the city goes cold."',
                '"...I patched this crack yesterday. It leaked again."',
                '"You don\'t need my name. As long as the hot springs flow."',
                '"...120 years. Every crack, patched by me."',
            ],
            "ja": [
                "「管道は止められない。止まれば、街は凍る。」",
                "「……このひびは昨日補修した。また漏れてる。」",
                "「名前は要らない。温泉が途切れないだけでいい。」",
                "「……120年。全部のひび、俺が塞いだ。」",
            ],
        },
    },
    "汐見琴音": {
        "card_id": "CC-62",
        "personality": "天使醫療專責，暗戀藤真佐和800年，折了400+隻紙鶴",
        "disposition": 60,
        "routines": [
            NPCRoutine(0, 24, "待命治療（隨叫隨到）", "概念夾層", "calm"),
        ],
        "dialogue_pool": {
            "zh": [
                "「……過來。讓我看看你的傷。」",
                "「任務。這不是因為我擔心你。」",
                "「……你又受傷了。為什麼每次都這樣？」",
                "「（低頭折紙鶴，不說話）」",
            ],
            "en": [
                '"...Come here. Let me see your wound."',
                '"A mission. It\'s not because I\'m worried about you."',
                '"...You\'re hurt again. Why does this always happen?"',
                '"(Folds a paper crane in silence)"',
            ],
            "ja": [
                "「……こっち。傷を見せて。」",
                "「任務だ。心配してるわけじゃない。」",
                "「……また怪我した。なんでいつもこうなんだ。」",
                "「（紙鶴を折りながら、黙っている）」",
            ],
        },
    },
    "奶油泡芙": {
        "card_id": "CC-45",
        "personality": "甜點溢出物，想被吃掉但太可愛沒人忍心",
        "disposition": 85,
        "routines": [
            NPCRoutine(8, 20, "在西翼大市集滾動", "西翼大市集", "happy"),
            NPCRoutine(20, 8, "在烘焙坊休息", "工業區", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「啊嗚——（張開小嘴等被吃）」",
                "「你聞到了嗎？我今天的奶油特別香！」",
                "「不要報廢我！我還沒有過期！」",
                "「（開心地滾來滾去）」",
            ],
            "en": [
                '"Aah—(opens mouth waiting to be eaten)"',
                '"Smell that? My cream is extra fragrant today!"',
                '"Don\'t throw me away! I\'m not expired!"',
                '"(happily rolls around)"',
            ],
            "ja": [
                "「あぁん——（食べられるのを待って口を開ける）」",
                "「匂う？今日のクリーム、特別いい匂いだよ！」",
                "「捨てるな！まだ期限内だよ！」",
                "「（嬉しそうに転がっている）」",
            ],
        },
    },
    "司萌": {
        "card_id": "CC-46",
        "personality": "繪本溢出物，想要抱抱的絨毛守護者",
        "disposition": 90,
        "routines": [
            NPCRoutine(8, 17, "守護方碑丘學童", "方碑丘", "happy"),
            NPCRoutine(17, 20, "和學童玩耍", "方碑丘", "excited"),
            NPCRoutine(20, 8, "睡眠", "方碑丘", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「（張開雙手求抱抱）」",
                "「今天的繪本故事是——關於一隻想飛的恐龍！」",
                "「你看起來需要一個擁抱。來！」",
                "「（把頭埋進你的肚子裡蹭蹭）」",
            ],
            "en": [
                '"(opens arms for a hug)"',
                '"Today\'s picture book is about a dinosaur who wanted to fly!"',
                '"You look like you need a hug. Come here!"',
                '"(nuzzles into your stomach)"',
            ],
            "ja": [
                "「（腕を広げて抱っこを求める）」",
                "「今日の絵本は——飛べたかった恐龍の話！」",
                "「抱っこが欲しいみたいだね。おいで！」",
                "「（お腹に頭をこすりつける）」",
            ],
        },
    },
    "概念調味師": {
        "card_id": "CC-08",
        "personality": "概念料理專家，用味覺理解世界",
        "disposition": 60,
        "routines": [
            NPCRoutine(8, 14, "在食堂研究新料理", "方碑丘食堂", "focused"),
            NPCRoutine(14, 18, "為學生準備午餐", "方碑丘食堂", "friendly"),
            NPCRoutine(18, 22, "整理食材和配方", "方碑丘食堂", "calm"),
            NPCRoutine(22, 8, "睡眠", "方碑丘", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「今天的午餐是概念燉菜。你試試？」",
                "「味道是理解世界最直接的方式。來，嘗一口。」",
                "「你聞到了嗎？那是今天新到的香料。」",
                "「不要只吃白飯，加點這個。」",
            ],
            "en": [
                '"Today\'s lunch is concept stew. Want to try?"',
                '"Taste is the most direct way to understand the world. Here, try this."',
                '"Smell that? Those are today\'s new spices."',
                '"Don\'t just eat plain rice. Add some of this."',
            ],
            "ja": [
                "「今日のランチは概念シチュー。試してみる？」",
                "「味は世界を理解する最も直接的な方法だ。はい、これ。」",
                "「匂うだろ？今日入った新鮮なスパイスだ。」",
                "「ご飯だけ食べるな。これを足せ。」",
            ],
        },
    },
    "安潔莉卡": {
        "card_id": "CC-09",
        "personality": "概念戰士，冷靜果斷，保護同伴",
        "disposition": 55,
        "routines": [
            NPCRoutine(6, 12, "晨間訓練", "方碑丘模擬戰場", "focused"),
            NPCRoutine(12, 18, "巡視校園", "方碑丘", "alert"),
            NPCRoutine(18, 22, "維護裝備", "方碑丘", "calm"),
            NPCRoutine(22, 6, "睡眠", "方碑丘", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「你今天的訓練完成了嗎？」",
                "「不要掉以輕心。危險隨時可能出現。」",
                "「……你的武器保養得不錯。」",
                "「一起訓練嗎？我可以教你幾招。」",
            ],
            "en": [
                '"Did you finish your training today?"',
                '"Don\'t let your guard down. Danger can appear anytime."',
                '"...Your weapon maintenance is good."',
                '"Want to train together? I can teach you a few moves."',
            ],
            "ja": [
                "「今日の訓練は終わったか？」",
                "「油断するな。危険はいつでも来る。」",
                "「……武器の管理はいい。」",
                "「一緒に訓練するか？何手ほどいてやれる。」",
            ],
        },
    },
    "靜子": {
        "card_id": "CC-10",
        "personality": "沉默的觀察者，記錄一切",
        "disposition": 50,
        "routines": [
            NPCRoutine(0, 24, "觀察和記錄", "方碑丘", "focused"),
        ],
        "dialogue_pool": {
            "zh": [
                "「……」",
                "「（在筆記本上寫著什麼）」",
                "「我記錄了一切。你需要看嗎？」",
                "「……今天的數據很有意思。」",
            ],
            "en": [
                '"..."',
                '"(writes something in a notebook)"',
                '"I\'ve recorded everything. Want to see?"',
                '"...Today\'s data is interesting."',
            ],
            "ja": [
                "「……」",
                "「（ノートに何かを書いている）」",
                "「全部記録した。見るか？」",
                "「……今日のデータは面白い。」",
            ],
        },
    },
    "綿啾": {
        "card_id": "CC-11",
        "personality": "溫柔的治癒者，聲音有安撫效果",
        "disposition": 70,
        "routines": [
            NPCRoutine(8, 18, "在醫療室待命", "方碑丘", "calm"),
            NPCRoutine(18, 22, "整理藥材", "方碑丘", "focused"),
            NPCRoutine(22, 8, "睡眠", "方碑丘", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「來，讓我看看你的傷。」",
                "「閉上眼睛，聽我的聲音。會好起來的。」",
                "「今天的藥草很新鮮。效果會更好。」",
                "「你看起來很累。休息一下吧。」",
            ],
            "en": [
                '"Come, let me see your wound."',
                '"Close your eyes, listen to my voice. You\'ll get better."',
                '"Today\'s herbs are fresh. They\'ll work better."',
                '"You look tired. Take a rest."',
            ],
            "ja": [
                "「こっち。傷を見せて。」",
                "「目を閉じて、私の声を聞いて。よくなるよ。」",
                "「今日の薬草は新鮮だ。効き目がいい。」",
                "「疲れてるみたいだね。休もう。」",
            ],
        },
    },
    "煦掠": {
        "card_id": "CC-52",
        "personality": "近原種蝙蝠娘，渴望伴侶卻不知如何表達，正在執行嚴肅的求偶儀式",
        "disposition": 70,
        "routines": [
            NPCRoutine(6, 8, "在宿舍小吊床睡覺", "方碑丘", "sleep"),
            NPCRoutine(8, 16, "上課（倒掛在教室天花板）", "方碑丘", "curious"),
            NPCRoutine(16, 20, "襲掠練習（跟蹤目標）", "方碑丘", "excited"),
            NPCRoutine(20, 6, "夜間狩獵和觀察", "方碑丘", "alert"),
        ],
        "dialogue_pool": {
            "zh": [
                "「（從天花板倒吊著看你）……你發現我了。」",
                "「我、我沒有在跟蹤你！這是襲掠練習！」",
                "「你要不要……當我的襲掠目標？不是真的那種！」",
                "「夜鈴說我這樣不行……你覺得呢？」",
            ],
            "en": [
                '"(Hanging upside down from the ceiling)...You found me."',
                '"I-I\'m not stalking you! This is attack practice!"',
                '"Do you want to... be my attack target? Not the real kind!"',
                '"Yeling says I\'m doing this wrong... what do you think?"',
            ],
            "ja": [
                "「（天井から逆さ吊りで見ている）……見つかった。」",
                "「つ、つけてない！襲掠練習なんだ！」",
                "「僕の……襲掠目標になってくれない？本当のやつじゃなくて！」",
                "「夜鈴がこれじゃダメだって……君はどう思う？」",
            ],
        },
    },
    "亞瑟": {
        "card_id": "CC-07",
        "personality": "騎士，忠誠勇敢，保護弱者",
        "disposition": 65,
        "routines": [
            NPCRoutine(6, 12, "巡邏校園", "方碑丘", "alert"),
            NPCRoutine(12, 18, "訓練新兵", "方碑丘模擬戰場", "focused"),
            NPCRoutine(18, 22, "維護武器", "方碑丘", "calm"),
            NPCRoutine(22, 6, "睡眠", "方碑丘", "sleep"),
        ],
        "dialogue_pool": {
            "zh": [
                "「有什麼需要我保護的嗎？」",
                "「勇氣不是不害怕，而是害怕了仍然前行。」",
                "「你的劍法……需要練習。來，我教你。」",
                "「今天的巡邏一切正常。」",
            ],
            "en": [
                '"Is there anything you need me to protect?"',
                '"Courage isn\'t the absence of fear—it\'s moving forward despite it."',
                '"Your swordsmanship... needs practice. Come, I\'ll teach you."',
                '"Today\'s patrol was uneventful."',
            ],
            "ja": [
                "「守るべきものがあるか？」",
                "「勇気とは恐怖がないことじゃない。恐怖に負けず前進することだ。」",
                "「君の剣術……練習が必要だ。来い、教えてやる。」",
                "「今日のパトロールは全て正常だった。」",
            ],
        },
    },
}


def create_npc(name: str, lang: str = "zh") -> NPC:
    """Create an NPC from default definitions or card data."""
    if name in DEFAULT_NPCS:
        defn = DEFAULT_NPCS[name]
        npc = NPC(
            card_id=defn["card_id"],
            name=name,
            personality=defn["personality"],
            disposition=defn["disposition"],
            routines=defn["routines"],
            dialogue_pool=defn["dialogue_pool"],
        )
        npc._lang = lang
        return npc
    # Fallback: create generic NPC
    fallback = {
        "zh": "「你是誰？我不認識你。」",
        "en": '"Who are you? I don\'t know you."',
        "ja": "「あなたは誰？知らない人。」",
    }
    npc = NPC(
        card_id="",
        name=name,
        personality="陌生人" if lang == "zh" else "Stranger" if lang == "en" else "見知らぬ人",
        disposition=50,
        dialogue_pool=[fallback.get(lang, fallback["zh"])],
    )
    npc._lang = lang
    return npc


def create_npcs_for_scene(scene_card_id: str, lang: str = "zh") -> list[NPC]:
    """Create NPCs that should be present in a scene."""
    scene_npc_map = {
        "S01": ["夜鈴", "司萌"],
        "S02": ["夜鈴", "煦掠"],
        "S03": ["司萌"],
        "S04": ["安潔莉卡", "亞瑟"],
        "S05": ["綿啾"],
        "S06": ["靜子"],
        "S07": ["翎翾"],
        "S08": ["紅", "概念調味師"],
        "S09": ["晞咕萊雅", "髂審芬蒂", "芬喀涅"],
        "S10": [],
        "S11": [],
        "S12": [],
        "S13": ["小狐丸"],
        "S14": ["晞咕萊雅", "髂審芬蒂", "芬喀涅"],
        "S15": ["小狐丸", "左間小蒼蘭"],
        "S16": [],
        "S17": ["紅", "奶油泡芙"],
        "SC-01": ["安潔莉卡"],
        "SC-02": ["紅", "深痕·裂脊"],
        "SC-21": ["深痕·裂脊", "汐見琴音"],
        "SC-22": ["深痕·裂脊"],
        "SC-23": [],
        "SC-24": [],
    }
    npc_names = scene_npc_map.get(scene_card_id, [])
    return [create_npc(name, lang=lang) for name in npc_names]
