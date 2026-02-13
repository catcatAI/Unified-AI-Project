#!/usr/bin/env python3
"""
Angela Character Image Processor
處理 Angela 立繪圖片，創建身體部位座標映射和透明背景版本
"""

import os
import json
from PIL import Image, ImageDraw
from collections import defaultdict
from datetime import datetime

# 圖片路徑
IMAGE_PATH = "/home/cat/桌面/Gemini_Generated_Image_hqq027hqq027hqq0.png"
OUTPUT_DIR = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app"

def analyze_character_regions():
    """分析圖片，識別身體部位區域"""
    img = Image.open(IMAGE_PATH)
    width, height = img.size
    
    print(f"圖片尺寸: {width} x {height}")
    
    # 創建像素分析
    pixels = img.load()
    
    # 根據圖片分析結果（假設 1920x1080），計算在實際尺寸中的座標
    # 原始分析是基於 1920x1080 的假設，實際圖片是 1408x768
    scale_x = width / 1920
    scale_y = height / 1080
    
    # 身體部位定義（基於圖片分析）
    # 格式: {部位名稱: {"rect": (x1, y1, x2, y2), "color_range": [(r,g,b), (r,g,b)]}}
    body_parts = {}
    
    # ====== 頭部區域 ======
    # 頭髮區域
    body_parts["hair"] = {
        "rect": (int(720 * scale_x), int(65 * scale_y), int(1200 * scale_x), int(450 * scale_y)),
        "color_range": [
            (201, 152, 182),  # 髮尾暗調 #D885B6
            (249, 168, 212),  # 主色 #F9A8D4
        ],
        "description": "頭髮",
        "priority": 1
    }
    
    # 臉部區域
    body_parts["face"] = {
        "rect": (int(860 * scale_x), int(100 * scale_y), int(1060 * scale_x), int(220 * scale_y)),
        "color_range": [
            (232, 213, 217),  # 陰影 #E8D5D9
            (252, 232, 227),  # 肌膚 #FCE8E3
        ],
        "description": "臉部",
        "priority": 2
    }
    
    # 眼睛區域
    body_parts["eyes"] = {
        "rect": (int(900 * scale_x), int(140 * scale_y), int(1020 * scale_x), int(165 * scale_y)),
        "color_range": [
            (139, 69, 19),    # 眼瞼 #8B4513
            (255, 105, 180),  # 眼瞳 #FF69B4
        ],
        "description": "眼睛",
        "priority": 3
    }
    
    # 嘴巴區域
    body_parts["mouth"] = {
        "rect": (int(930 * scale_x), int(175 * scale_y), int(990 * scale_x), int(190 * scale_y)),
        "color_range": [
            (232, 117, 149),  # 嘴唇 #E87595
        ],
        "description": "嘴巴",
        "priority": 3
    }
    
    # ====== 身體區域 ======
    # 脖子區域
    body_parts["neck"] = {
        "rect": (int(890 * scale_x), int(215 * scale_y), int(1030 * scale_x), int(260 * scale_y)),
        "color_range": [
            (232, 213, 217),  # 陰影
            (252, 232, 227),  # 肌膚
        ],
        "description": "脖子",
        "priority": 2
    }
    
    # 肩膀區域
    body_parts["shoulders"] = {
        "rect": (int(860 * scale_x), int(255 * scale_y), int(1060 * scale_x), int(300 * scale_y)),
        "color_range": [
            (194, 122, 163),  # 深粉邊界 #C27AA3
            (255, 253, 246),  # 肩部高光 #FDF4F6
        ],
        "description": "肩膀",
        "priority": 2
    }
    
    # 軀幹區域
    body_parts["torso"] = {
        "rect": (int(870 * scale_x), int(290 * scale_y), int(1050 * scale_x), int(480 * scale_y)),
        "color_range": [
            (139, 69, 19),    # 深色邊界
            (107, 142, 184),  # 衣服藍 #6B8EB8
        ],
        "description": "軀幹/衣服",
        "priority": 2
    }
    
    # ====== 四肢區域 ======
    # 右手臂（舉起）
    body_parts["right_arm"] = {
        "rect": (int(980 * scale_x), int(160 * scale_y), int(1120 * scale_x), int(420 * scale_y)),
        "color_range": [
            (194, 122, 163),  # 深粉線
            (252, 232, 227),  # 肌膚
        ],
        "description": "右手臂",
        "priority": 3
    }
    
    # 左手臂（下垂）
    body_parts["left_arm"] = {
        "rect": (int(820 * scale_x), int(380 * scale_y), int(920 * scale_x), int(510 * scale_y)),
        "color_range": [
            (194, 122, 163),  # 深粉線
            (252, 232, 227),  # 肌膚
        ],
        "description": "左手臂",
        "priority": 3
    }
    
    # 右手
    body_parts["right_hand"] = {
        "rect": (int(1040 * scale_x), int(160 * scale_y), int(1100 * scale_x), int(220 * scale_y)),
        "color_range": [
            (232, 213, 217),  # 指縫陰影
            (255, 255, 255),  # 指尖高光
        ],
        "description": "右手",
        "priority": 4
    }
    
    # 左手
    body_parts["left_hand"] = {
        "rect": (int(840 * scale_x), int(480 * scale_y), int(900 * scale_x), int(520 * scale_y)),
        "color_range": [
            (232, 213, 217),  # 指縫陰影
            (255, 255, 255),  # 指尖高光
        ],
        "description": "左手",
        "priority": 4
    }
    
    # ====== 腿部區域 ======
    # 左腿
    body_parts["left_leg"] = {
        "rect": (int(880 * scale_x), int(480 * scale_y), int(960 * scale_x), int(700 * scale_y)),
        "color_range": [
            (107, 142, 184),  # 褲子藍
            (180, 180, 180),  # 灰絲
        ],
        "description": "左腿",
        "priority": 3
    }
    
    # 右腿
    body_parts["right_leg"] = {
        "rect": (int(1000 * scale_x), int(480 * scale_y), int(1080 * scale_x), int(700 * scale_y)),
        "color_range": [
            (107, 142, 184),  # 褲子藍
            (180, 180, 180),  # 灰絲
        ],
        "description": "右腿",
        "priority": 3
    }
    
    return body_parts, width, height


def create_touch_zones(body_parts, width, height):
    """創建觸覺區域映射"""
    touch_zones = {}
    
    # 定義區域到 Live2D 參數的映射
    zone_mapping = {
        # 頭部區域
        "hair": {
            "param_id": "PARAM_HAIR_FRONT",
            "expression": "happy",
            "tactile_type": "stroke",
            "priority": 1
        },
        "face": {
            "param_id": "PARAM_CHEEK",
            "expression": "blush",
            "tactile_type": "pat",
            "priority": 2
        },
        "eyes": {
            "param_id": "PARAM_EYE_OPEN",
            "expression": "wink",
            "tactile_type": "poke",
            "priority": 3
        },
        "mouth": {
            "param_id": "PARAM_MOUTH_OPEN",
            "expression": "smile",
            "tactile_type": "poke",
            "priority": 3
        },
        # 身體區域
        "neck": {
            "param_id": "PARAM_NECK",
            "expression": "neutral",
            "tactile_type": "pat",
            "priority": 2
        },
        "shoulders": {
            "param_id": "PARAM_SHOULDER",
            "expression": "happy",
            "tactile_type": "stroke",
            "priority": 2
        },
        "torso": {
            "param_id": "PARAM_CHEST",
            "expression": "neutral",
            "tactile_type": "pat",
            "priority": 2
        },
        # 四肢區域
        "right_arm": {
            "param_id": "PARAM_RARM",
            "expression": "happy",
            "tactile_type": "stroke",
            "priority": 3
        },
        "left_arm": {
            "param_id": "PARAM_LARM",
            "expression": "happy",
            "tactile_type": "stroke",
            "priority": 3
        },
        "right_hand": {
            "param_id": "PARAM_RHAND",
            "expression": "excited",
            "tactile_type": "poke",
            "priority": 4
        },
        "left_hand": {
            "param_id": "PARAM_LHAND",
            "expression": "excited",
            "tactile_type": "poke",
            "priority": 4
        },
        # 腿部區域
        "left_leg": {
            "param_id": "PARAM_RLEG",
            "expression": "neutral",
            "tactile_type": "stroke",
            "priority": 3
        },
        "right_leg": {
            "param_id": "PARAM_RLEG",
            "expression": "neutral",
            "tactile_type": "stroke",
            "priority": 3
        }
    }
    
    for part_name, part_data in body_parts.items():
        if part_name in zone_mapping:
            touch_zones[part_name] = {
                **part_data,
                **zone_mapping[part_name]
            }
    
    return touch_zones


def create_mask_image(body_parts, width, height):
    """創建透明背景的圖片（只保留角色區域）"""
    img = Image.open(IMAGE_PATH)
    
    # 檢查是否有 Alpha 通道
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 創建新的透明圖片
    new_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # 計算角色的邊界框
    all_rects = [data["rect"] for data in body_parts.values()]
    min_x = min(r[0] for r in all_rects)
    min_y = min(r[1] for r in all_rects)
    max_x = max(r[2] for r in all_rects)
    max_y = max(r[3] for r in all_rects)
    
    # 稍微擴大範圍以確保完整
    padding = 20
    min_x = max(0, min_x - padding)
    min_y = max(0, min_y - padding)
    max_x = min(width, max_x + padding)
    max_y = min(height, max_y + padding)
    
    # 從原圖複製角色區域
    region = img.crop((min_x, min_y, max_x, max_y))
    new_img.paste(region, (min_x, min_y))
    
    return new_img, (min_x, min_y, max_x, max_y)


def generate_config():
    """生成所有配置數據"""
    print("分析圖片...")
    body_parts, width, height = analyze_character_regions()
    
    print(f"識別到 {len(body_parts)} 個身體部位")
    
    print("創建觸覺區域...")
    touch_zones = create_touch_zones(body_parts, width, height)
    
    print("生成透明背景圖片...")
    mask_img, bbox = create_mask_image(body_parts, width, height)
    
    # 保存透明背景版本
    mask_path = os.path.join(OUTPUT_DIR, "resources/angela_character_masked.png")
    os.makedirs(os.path.dirname(mask_path), exist_ok=True)
    mask_img.save(mask_path, "PNG")
    print(f"保存透明背景圖片: {mask_path}")
    
    # 生成配置數據
    config = {
        "version": "1.0.0",
        "image_path": "resources/angela_character_masked.png",
        "original_size": {
            "width": width,
            "height": height
        },
        "character_bbox": {
            "x": bbox[0],
            "y": bbox[1],
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1]
        },
        "touch_zones": touch_zones,
        "body_parts": body_parts,
        "metadata": {
            "generated_at": str(datetime.now()),
            "source_image": IMAGE_PATH,
            "description": "Angela character with body part mapping for tactile interaction"
        }
    }
    
    # 保存配置
    config_path = os.path.join(OUTPUT_DIR, "resources/angela_character_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"保存配置: {config_path}")
    
    # 生成 JavaScript 模組
    js_module = f"""\/**
 * Angela Character Configuration
 * 自動生成的身體部位配置
 */

const ANGELA_CHARACTER_CONFIG = {json.dumps(config, indent=2, ensure_ascii=False)};

// 導出配置
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = ANGELA_CHARACTER_CONFIG;
}}
"""
    
    js_path = os.path.join(OUTPUT_DIR, "js/angela-character-config.js")
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_module)
    print(f"保存 JavaScript 配置: {js_path}")
    
    print("\n✅ 配置生成完成！")
    print(f"\n圖片尺寸: {width} x {height}")
    print(f"角色邊界: {bbox}")
    print(f"身體部位數量: {len(body_parts)}")
    print(f"觸覺區域數量: {len(touch_zones)}")
    
    return config


if __name__ == "__main__":
    generate_config()
