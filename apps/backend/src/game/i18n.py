"""Internationalization — zh/en/ja strings for all UI."""
from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    # === Title Screen ===
    "title": {
        "zh": "文字冒險遊戲",
        "en": "Text Adventure Game",
        "ja": "テキストアドベンチャーゲーム",
    },
    "subtitle": {
        "zh": "基於 ED3N/GARDEN + 確定性引擎",
        "en": "Powered by ED3N/GARDEN + Deterministic Engines",
        "ja": "ED3N/GARDEN + 決定論エンジン搭載",
    },
    "start": {
        "zh": "開始遊戲",
        "en": "Start Game",
        "ja": "ゲーム開始",
    },
    "lang_select": {
        "zh": "語言 / Language / 言語",
        "en": "Language",
        "ja": "言語",
    },
    "quit": {
        "zh": "離開",
        "en": "Quit",
        "ja": "終了",
    },

    # === World Selection ===
    "world_select": {
        "zh": "選擇世界線",
        "en": "Select World",
        "ja": "ワールド選択",
    },
    "world_w01": {
        "zh": "迴廊之弦：秩序與熵增的交響",
        "en": "Corridor of Strings: Symphony of Order and Entropy",
        "ja": "回廊の弦：秩序とエントロピーの交響",
    },
    "world_w01_desc": {
        "zh": "科幻/哲學世界觀。概念靈、迴廊、多元宇宙。",
        "en": "Sci-fi/Philosophy. Concept spirits, corridors, multiverse.",
        "ja": "SF/哲学。概念精霊、回廊、多元宇宙。",
    },
    "world_w02": {
        "zh": "艦娘：三戰餘暉",
        "en": "Ship Girls: Afterglow of Three Wars",
        "ja": "艦娘：三戦の余暉",
    },
    "world_w02_desc": {
        "zh": "軍事/歷史世界觀。艦船擬人化、戰略、陣營。",
        "en": "Military/History. Ship girl anthropomorphism, strategy, factions.",
        "ja": "軍事/歴史。艦船擬人化、戦略、勢力。",
    },

    # === Character Selection ===
    "char_select": {
        "zh": "選擇角色",
        "en": "Select Character",
        "ja": "キャラクター選択",
    },
    "char_hp": {
        "zh": "生命",
        "en": "HP",
        "ja": "HP",
    },
    "char_spirit": {
        "zh": "靈",
        "en": "Spirit",
        "ja": "霊",
    },
    "char_skill": {
        "zh": "技",
        "en": "Skill",
        "ja": "技能",
    },
    "confirm": {
        "zh": "確認",
        "en": "Confirm",
        "ja": "確認",
    },
    "back": {
        "zh": "返回",
        "en": "Back",
        "ja": "戻る",
    },

    # === Game Screen ===
    "equip": {
        "zh": "裝備",
        "en": "Equipment",
        "ja": "装備",
    },
    "inventory": {
        "zh": "背包",
        "en": "Inventory",
        "ja": "背包",
    },
    "none": {
        "zh": "無",
        "en": "None",
        "ja": "無し",
    },
    "empty": {
        "zh": "空的",
        "en": "Empty",
        "ja": "空",
    },
    "scene_info": {
        "zh": "場景資訊",
        "en": "Scene Info",
        "ja": "シーン情報",
    },
    "nearby": {
        "zh": "在場",
        "en": "Present",
        "ja": "存在",
    },
    "input_hint": {
        "zh": "輸入指令...",
        "en": "Enter command...",
        "ja": "コマンド入力...",
    },
    "turn": {
        "zh": "動作",
        "en": "Turn",
        "ja": "ターン",
    },

    # === Choices ===
    "choice_observe": {
        "zh": "觀察周圍環境",
        "en": "Observe surroundings",
        "ja": "周囲を観察",
    },
    "choice_talk": {
        "zh": "與同伴對話",
        "en": "Talk to companion",
        "ja": "仲間と話す",
    },
    "choice_advance": {
        "zh": "前進探索",
        "en": "Advance",
        "ja": "先に進む",
    },
    "choice_rest": {
        "zh": "休息恢復",
        "en": "Rest and recover",
        "ja": "休憩する",
    },
    "choice_inventory": {
        "zh": "檢查背包",
        "en": "Check inventory",
        "ja": "背包を確認",
    },
    "choice_status": {
        "zh": "查看狀態",
        "en": "View status",
        "ja": "ステータス確認",
    },

    # === Game Over ===
    "gameover": {
        "zh": "遊戲結束",
        "en": "Game Over",
        "ja": "ゲームオーバー",
    },
    "gameover_win": {
        "zh": "你成功完成了冒險！",
        "en": "You completed the adventure!",
        "ja": "冒険を達成しました！",
    },
    "gameover_lose": {
        "zh": "你的旅程到此結束...",
        "en": "Your journey ends here...",
        "ja": "旅はここで終わります...",
    },
    "gameover_quit": {
        "zh": "你選擇了離開。",
        "en": "You chose to leave.",
        "ja": "あなたは去ることを選んだ。",
    },
    "summary": {
        "zh": "冒險摘要",
        "en": "Adventure Summary",
        "ja": "冒険サマリー",
    },
    "total_turns": {
        "zh": "總回合數",
        "en": "Total Turns",
        "ja": "合計ターン",
    },
    "play_again": {
        "zh": "再玩一次",
        "en": "Play Again",
        "ja": "もう一度プレイ",
    },

    # === System ===
    "system": {
        "zh": "系統",
        "en": "System",
        "ja": "システム",
    },
    "invalid_choice": {
        "zh": "無效選項",
        "en": "Invalid choice",
        "ja": "無効な選択",
    },
    "rest_msg": {
        "zh": "你稍作休息。HP +{heal}，靈 +{spirit}。",
        "en": "You rest. HP +{heal}, Spirit +{spirit}.",
        "ja": "休憩しました。HP +{heal}、霊 +{spirit}。",
    },
    "inventory_msg": {
        "zh": "背包：{items}",
        "en": "Inventory: {items}",
        "ja": "背包: {items}",
    },

    # === Quest & NPC ===
    "choice_quests": {
        "zh": "查看任務",
        "en": "View quests",
        "ja": "クエスト確認",
    },
    "choice_npc_info": {
        "zh": "查看人物",
        "en": "View NPCs",
        "ja": "NPC情報",
    },
    "quest_active": {
        "zh": "進行中任務",
        "en": "Active Quests",
        "ja": "進行中クエスト",
    },
    "quest_completed": {
        "zh": "已完成任務",
        "en": "Completed Quests",
        "ja": "完了クエスト",
    },
    "no_quests": {
        "zh": "目前沒有進行中的任務",
        "en": "No active quests",
        "ja": "進行中のクエストはありません",
    },
    "quest_progress": {
        "zh": "[{id}] {title} ({pct}%) {done}/{total}",
        "en": "[{id}] {title} ({pct}%) {done}/{total}",
        "ja": "[{id}] {title} ({pct}%) {done}/{total}",
    },
    "quest_done": {
        "zh": "[{id}] {title} - 完成",
        "en": "[{id}] {title} - DONE",
        "ja": "[{id}] {title} - 完了",
    },
    "quest_obj_complete": {
        "zh": "任務目標完成：{desc}",
        "en": "Objective complete: {desc}",
        "ja": "目標完了: {desc}",
    },
    "quest_complete": {
        "zh": "任務完成：{title}",
        "en": "Quest complete: {title}",
        "ja": "クエスト完了: {title}",
    },
    "choice_quests_short": {
        "zh": "任務",
        "en": "Quests",
        "ja": "クエスト",
    },
    "choice_npc_info_short": {
        "zh": "人物",
        "en": "NPC Info",
        "ja": "NPC情報",
    },

    # === Narration (new game, advance, observe) ===
    "narration_scene_intro": {
        "zh": "【{name}】{desc}",
        "en": "[{name}] {desc}",
        "ja": "【{name}】{desc}",
    },
    "narration_enter_world": {
        "zh": "你以 {name} 的身份踏入了這個世界。",
        "en": "You enter this world as {name}.",
        "ja": "{name}としてこの世界に入った。",
    },
    "narration_present": {
        "zh": "在場的人：{names}",
        "en": "Present: {names}",
        "ja": "存在: {names}",
    },
    "narration_no_npcs": {
        "zh": "周圍沒有人。",
        "en": "No one is around.",
        "ja": "周りには誰もいない。",
    },
    "quest_started": {
        "zh": "任務啟動：{title}",
        "en": "Quest started: {title}",
        "ja": "クエスト開始: {title}",
    },

    # === Combat ===
    "combat_success": {
        "zh": "攻擊！擲骰 {roll} + {bonus}(令牌) + {skill}(技能) = {total}。造成 {dmg} 傷害。",
        "en": "Attack! Roll {roll} + {bonus}(token) + {skill}(skill) = {total}. {dmg} damage dealt.",
        "ja": "攻撃！ダイス {roll} + {bonus}(トークン) + {skill}(技能) = {total}。{dmg} ダメージ。",
    },
    "combat_partial": {
        "zh": "攻擊！擲骰 {roll} + {bonus} + {skill} = {total}。部分命中，{dmg} 傷害。",
        "en": "Attack! Roll {roll} + {bonus} + {skill} = {total}. Partial hit, {dmg} damage.",
        "ja": "攻撃！ダイス {roll} + {bonus} + {skill} = {total}。部分的命中、{dmg} ダメージ。",
    },
    "combat_fail": {
        "zh": "攻擊！擲骰 {roll} + {bonus} + {skill} = {total}。失敗。受到 {dmg} 傷害（減傷 {resist}%）。",
        "en": "Attack! Roll {roll} + {bonus} + {skill} = {total}. Failed. Took {dmg} dmg (resist {resist}%).",
        "ja": "攻撃！ダイス {roll} + {bonus} + {skill} = {total}。失敗。{dmg} ダメージ被弾（減傷 {resist}%）。",
    },
    "combat_loot": {
        "zh": "獲得：{item}",
        "en": "Obtained: {item}",
        "ja": "獲得: {item}",
    },
    "loot_spirit_crystal": {
        "zh": "靈子結晶",
        "en": "Spirit Crystal",
        "ja": "霊子結晶",
    },

    # === Observe ===
    "observe_scene": {
        "zh": "場景：{name}",
        "en": "Scene: {name}",
        "ja": "シーン: {name}",
    },
    "observe_spirit": {
        "zh": "靈子濃度：{density}ppm",
        "en": "Spirit: {density}ppm",
        "ja": "霊子濃度: {density}ppm",
    },
    "observe_temp": {
        "zh": "溫度：{temp}",
        "en": "Temperature: {temp}",
        "ja": "温度: {temp}",
    },

    # === Status ===
    "status_turn_hour": {
        "zh": "回合: {turn} | 時間: {hour}:00",
        "en": "Turn: {turn} | Hour: {hour}:00",
        "ja": "ターン: {turn} | 時間: {hour}:00",
    },
    "status_tokens": {
        "zh": "令牌效果：",
        "en": "Token effects:",
        "ja": "トークン効果:",
    },

    # === NPC Info ===
    "no_npcs_here": {
        "zh": "這裡沒有其他人。",
        "en": "No one is here.",
        "ja": "ここには誰もいない。",
    },
    "npc_mood": {
        "zh": "心情: {mood} | 好感: {disp}",
        "en": "Mood: {mood} | Disposition: {disp}",
        "ja": "気分: {mood} | 好感: {disp}",
    },

    # === Character Select Detail ===
    "char_tokens": {
        "zh": "令牌效果",
        "en": "Token Effects",
        "ja": "トークン効果",
    },
    "char_stats_preview": {
        "zh": "HP: {hp} | SP: {sp} | SK: {sk}",
        "en": "HP: {hp} | SP: {sp} | SK: {sk}",
        "ja": "HP: {hp} | SP: {sp} | SK: {sk}",
    },

    # === Inventory Items ===
    "item_flashlight": {
        "zh": "手電筒",
        "en": "Flashlight",
        "ja": "懐中電灯",
    },
    "item_map": {
        "zh": "地圖",
        "en": "Map",
        "ja": "地図",
    },

    # === Scene Panel ===
    "scene_spirit_density": {
        "zh": "靈子濃度：{density}ppm",
        "en": "Spirit: {density}ppm",
        "ja": "霊子濃度: {density}ppm",
    },
    "scene_temperature": {
        "zh": "溫度：{temp}",
        "en": "Temp: {temp}",
        "ja": "温度: {temp}",
    },

    # === Scene Fallbacks ===
    "scene_default_name": {
        "zh": "未知場景",
        "en": "Unknown Scene",
        "ja": "不明シーン",
    },
    "scene_default_desc": {
        "zh": "一片未知的區域",
        "en": "An unknown area",
        "ja": "不明のエリア",
    },

    # === NPC Activity Fallback ===
    "npc_activity_unknown": {
        "zh": "未知",
        "en": "Unknown",
        "ja": "不明",
    },

    # === Interaction Choices ===
    "choice_accept_quest": {
        "zh": "接受 {name} 的委託",
        "en": "Accept {name}'s request",
        "ja": "{name}の依頼を受ける",
    },
    "choice_ask_info": {
        "zh": "詢問 {name} 情報",
        "en": "Ask {name} for info",
        "ja": "{name}に情報を聞く",
    },
    "choice_ask_help": {
        "zh": "向 {name} 求助",
        "en": "Ask {name} for help",
        "ja": "{name}に助けを求める",
    },
    "choice_give_item": {
        "zh": "送 {name} 東西",
        "en": "Give something to {name}",
        "ja": "{name}にアイテムを渡す",
    },
    "choice_leave": {
        "zh": "離開",
        "en": "Leave",
        "ja": "去る",
    },
    "npc_no_quest": {
        "zh": "「目前沒有什麼需要幫忙的。」",
        "en": "\"Nothing I need help with right now.\"",
        "ja": "「今は手伝いが必要じゃない。」",
    },
    "npc_quest_hint": {
        "zh": "「你正在進行的「{quest}」，我覺得線索可能在附近。」",
        "en": "\"About '{quest}'... I think the clue might be nearby.\"",
        "ja": "「{quest}について…手がかりは近くにあるかも。」",
    },
    "npc_help_yes": {
        "zh": "「沒問題，讓我幫你。」{name}為你恢復了 HP +{heal}，靈 +{spirit}。",
        "en": "\"Sure, let me help.\" {name} restored HP +{heal}, Spirit +{spirit}.",
        "ja": "「もちろん、手伝うよ。」{name}がHP +{heal}、霊 +{spirit}を回復した。",
    },
    "npc_help_no": {
        "zh": "「抱歉，我現在不方便。」",
        "en": "\"Sorry, I can't help right now.\"",
        "ja": "「ごめん、今はちょっと。」",
    },
    "npc_item_received": {
        "zh": "「這是給我的？謝謝。」{name}看起來很高興。",
        "en": "\"This is for me? Thank you.\" {name} seems pleased.",
        "ja": "「これ、わたしに？ありがとう。」{name}は嬉しそうだ。",
    },
    "npc_no_item": {
        "zh": "「你手上沒有什麼可以給我的東西。」",
        "en": "\"You don't have anything to give me.\"",
        "ja": "「渡すものがないみたいだね。」",
    },
    "you_leave": {
        "zh": "你離開了{name}。",
        "en": "You leave {name}.",
        "ja": "{name}から離れた。",
    },
    "no_one_nearby": {
        "zh": "這裡沒有人可以對話。",
        "en": "No one is here to talk to.",
        "ja": "話せる人がいない。",
    },

    # === Travel Events ===
    "travel_danger": {
        "zh": "旅途中遭遇了 {enemy}！受到 {dmg} 傷害。",
        "en": "Encountered {enemy} on the way! Took {dmg} damage.",
        "ja": "途中で{enemy}に遭遇！{dmg}ダメージ被弾。",
    },
    "travel_discovery": {
        "zh": "旅途中發現了 {item}！HP 恢復 +{heal}。",
        "en": "Found {item} on the way! HP +{heal}.",
        "ja": "途中で{item}を発見！HP +{heal}。",
    },

    # === Combat (new) ===
    "combat_encounter": {
        "zh": "遭遇了 {enemy}！",
        "en": "Encountered {enemy}!",
        "ja": "{enemy}に遭遇！",
    },
    "combat_win": {
        "zh": "擊敗了 {enemy}！造成 {dmg} 傷害。獲得 {item}，HP +{heal}。",
        "en": "Defeated {enemy}! {dmg} damage. Got {item}, HP +{heal}.",
        "ja": "{enemy}を撃破！{dmg}ダメージ。{item}獲得、HP +{heal}。",
    },
    "combat_draw": {
        "zh": "與 {enemy} 交戰！你受到 {player_dmg} 傷害，敵人受到 {enemy_dmg} 傷害。",
        "en": "Fought {enemy}! You took {player_dmg}, enemy took {enemy_dmg}.",
        "ja": "{enemy}と交戦！あなたは{player_dmg}ダメージ、敵は{enemy_dmg}ダメージ。",
    },
    "combat_lose": {
        "zh": "被 {enemy} 攻擊！受到 {dmg} 傷害（減傷 {resist}%）。",
        "en": "Hit by {enemy}! Took {dmg} dmg (resist {resist}%).",
        "ja": "{enemy}に攻撃された！{dmg}ダメージ被弾（減傷{resist}%）。",
    },

    # === Observe (new) ===
    "observe_footprints": {
        "zh": "地上有一些奇怪的足跡，似乎不久前有人走過。",
        "en": "Strange footprints on the ground — someone was here recently.",
        "ja": "地面に不思議な足跡。誰かが最近通ったようだ。",
    },
    "observe_crack": {
        "zh": "牆壁上有一道細微的裂縫，裡面隱約透出微光。",
        "en": "A thin crack in the wall, faint light leaking through.",
        "ja": "壁に細いひび。微かな光が漏れている。",
    },
    "observe_light": {
        "zh": "遠處有微弱的光源在閃爍，可能是出口或信標。",
        "en": "A faint light flickers in the distance — could be an exit or beacon.",
        "ja": "遠くに微かな光が点滅している。出口かビーコンかも。",
    },
    "observe_sound": {
        "zh": "空氣中傳來低沉的嗡鳴聲，像是某種機械在運轉。",
        "en": "A low hum fills the air — some kind of machine is running.",
        "ja": "低い唸りが空気を満たしている。何らかの機械が稼働中だ。",
    },
    "observe_mark": {
        "zh": "地面上刻著一個符號，似乎是指路的記號。",
        "en": "A symbol carved into the ground — looks like a guide mark.",
        "ja": "地面に刻まれた記号。道標のようだ。",
    },
    "observe_wind": {
        "zh": "一陣冷風吹過，帶來遠處陌生的氣息。",
        "en": "A cold breeze passes, carrying an unfamiliar scent.",
        "ja": "冷たい風が通り過ぎ、見知らぬ匂いを運んできた。",
    },
    "observe_temperature_change": {
        "zh": "溫度突然下降了幾度，空氣中的靈子濃度似乎在變化。",
        "en": "Temperature drops suddenly — spirit density seems to shift.",
        "ja": "気温が急降下。霊子濃度が変化しているようだ。",
    },
    "observe_find": {
        "zh": "你注意到{discovery}，仔細一看，發現了 {item}！",
        "en": "You notice {discovery} — looking closer, found {item}!",
        "ja": "{discovery}に気づき、よく見ると{item}を発見！",
    },
    "observe_quest_clue": {
        "zh": "你注意到{discovery}，這可能跟「{quest}」有關。",
        "en": "You notice {discovery} — this might relate to '{quest}'.",
        "ja": "{discovery}に気づいた。これは「{quest}」に関連しているかも。",
    },
    "observe_generic": {
        "zh": "你注意到{discovery}",
        "en": "You notice {discovery}",
        "ja": "{discovery}に気づいた",
    },

    # === Rest Events ===
    "rest_npc_visit": {
        "zh": "休息時{name}走了過來：{line}",
        "en": "While resting, {name} approaches: {line}",
        "ja": "休憩中、{name}が近づいてきた: {line}",
    },
    "rest_dream_corridor": {
        "zh": "你夢見自己走在無盡的走廊中，兩側的門不斷開合，每一次都露出不同的世界。",
        "en": "You dream of walking an endless corridor. Doors open and close, each revealing a different world.",
        "ja": "夢で無限の回廊を歩いた。両側の扉が開閉し、それぞれ異なる世界が覗いていた。",
    },
    "rest_dream_voice": {
        "zh": "你聽見一個聲音在低語：「選擇已經做出，只是你還沒意識到。」",
        "en": "A voice whispers: \"The choice was already made — you just haven't realized it yet.\"",
        "ja": "声が囁いた。「選択はもう行われた。ただ気づいていないだけだ。」",
    },
    "rest_dream_memory": {
        "zh": "你想起了一個模糊的畫面——有人在等你，但你想不起是誰。",
        "en": "A blurry image surfaces — someone is waiting for you, but you can't remember who.",
        "ja": "ぼんやりとした映像が浮かんだ——誰かがあなたを待っている。だが誰なのか思い出せない。",
    },
    "rest_danger": {
        "zh": "你在休息時遭到偷襲！受到 {dmg} 傷害。",
        "en": "Ambushed while resting! Took {dmg} damage.",
        "ja": "休憩中に不意打ち！{dmg}ダメージ被弾。",
    },

    # === Game Ending ===
    "ending_title": {
        "zh": "冒險結束",
        "en": "Adventure Complete",
        "ja": "冒険終了",
    },
    "ending_summary": {
        "zh": "你以 {name} 的身份完成了 {turn} 回合的冒險。",
        "en": "You completed {turn} turns of adventure as {name}.",
        "ja": "{name}として{turn}ターンの冒険を終えた。",
    },
    "ending_quests": {
        "zh": "完成任務：{done}/{total}",
        "en": "Quests completed: {done}/{total}",
        "ja": "完了クエスト: {done}/{total}",
    },
    "ending_items": {
        "zh": "收集物品：{count} 件",
        "en": "Items collected: {count}",
        "ja": "収集アイテム: {count}件",
    },
    "ending_hp": {
        "zh": "最終狀態 HP: {hp}/{max_hp} | SP: {spirit}/{max_spirit}",
        "en": "Final HP: {hp}/{max_hp} | SP: {spirit}/{max_spirit}",
        "ja": "最終HP: {hp}/{max_hp} | SP: {spirit}/{max_spirit}",
    },
    "ending_alive": {
        "zh": "你活了下來。這段旅程還沒結束。",
        "en": "You survived. This journey isn't over yet.",
        "ja": "生き残った。この旅はまだ終わっていない。",
    },
    "ending_dead": {
        "zh": "你的旅程在這裡終止了。",
        "en": "Your journey ends here.",
        "ja": "あなたの旅はここで終わる。",
    },
    "ending_victory": {
        "zh": "你完成了所有任務。真正的挑戰即將開始。",
        "en": "All quests complete. The real challenge begins.",
        "ja": "全クエスト完了。真の挑戦がこれからだ。",
    },
}


class I18n:
    """Simple internationalization accessor."""

    def __init__(self, lang: str = "zh"):
        self.lang = lang

    def t(self, key: str, **kwargs) -> str:
        """Translate a key, with optional format kwargs."""
        entry = STRINGS.get(key, {})
        text = entry.get(self.lang) or entry.get("en") or key
        if kwargs:
            text = text.format(**kwargs)
        return text
