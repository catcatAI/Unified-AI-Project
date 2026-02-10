/**
 * Angela Character Configuration
 * 自動生成的身體部位配置 - 修復優先級版本
 */

const ANGELA_CHARACTER_CONFIG = {
  "version": "1.1.0",
  "image_path": "resources/angela_character_masked.png",
  "original_size": {
    "width": 1408,
    "height": 768
  },
  "character_bbox": {
    "x": 508,
    "y": 26,
    "width": 391,
    "height": 491
  },
  "touch_zones": {
    "face": {
      "rect": [630, 71, 777, 156],
      "color_range": [[200, 180, 180], [255, 235, 225]],
      "description": "臉部",
      "priority": 1,
      "param_id": "PARAM_CHEEK",
      "expression": "blush",
      "tactile_type": "pat"
    },
    "eyes": {
      "rect": [660, 99, 748, 117],
      "color_range": [[100, 50, 10], [200, 120, 180]],
      "description": "眼睛",
      "priority": 1,
      "param_id": "PARAM_EYE_OPEN",
      "expression": "wink",
      "tactile_type": "poke"
    },
    "mouth": {
      "rect": [682, 124, 726, 135],
      "color_range": [[200, 100, 130], [240, 140, 170]],
      "description": "嘴巴",
      "priority": 1,
      "param_id": "PARAM_MOUTH_OPEN",
      "expression": "smile",
      "tactile_type": "poke"
    },
    "neck": {
      "rect": [652, 152, 755, 184],
      "color_range": [[200, 180, 180], [255, 235, 225]],
      "description": "脖子",
      "priority": 2,
      "param_id": "PARAM_NECK",
      "expression": "neutral",
      "tactile_type": "pat"
    },
    "shoulders": {
      "rect": [630, 181, 777, 213],
      "color_range": [[180, 100, 150], [255, 240, 230]],
      "description": "肩膀",
      "priority": 2,
      "param_id": "PARAM_SHOULDER",
      "expression": "happy",
      "tactile_type": "stroke"
    },
    "torso": {
      "rect": [638, 206, 770, 341],
      "color_range": [[100, 60, 150], [180, 150, 200]],
      "description": "軀幹/衣服",
      "priority": 2,
      "param_id": "PARAM_CHEST",
      "expression": "neutral",
      "tactile_type": "pat"
    },
    "right_hand": {
      "rect": [762, 113, 806, 156],
      "color_range": [[200, 180, 180], [255, 235, 225]],
      "description": "右手",
      "priority": 3,
      "param_id": "PARAM_RHAND",
      "expression": "excited",
      "tactile_type": "poke"
    },
    "left_hand": {
      "rect": [616, 341, 660, 369],
      "color_range": [[200, 180, 180], [255, 235, 225]],
      "description": "左手",
      "priority": 3,
      "param_id": "PARAM_LHAND",
      "expression": "excited",
      "tactile_type": "poke"
    },
    "right_arm": {
      "rect": [718, 113, 821, 298],
      "color_range": [[180, 100, 150], [255, 235, 225]],
      "description": "右手臂",
      "priority": 4,
      "param_id": "PARAM_RARM",
      "expression": "happy",
      "tactile_type": "stroke"
    },
    "left_arm": {
      "rect": [601, 270, 674, 362],
      "color_range": [[180, 100, 150], [255, 235, 225]],
      "description": "左手臂",
      "priority": 4,
      "param_id": "PARAM_LARM",
      "expression": "happy",
      "tactile_type": "stroke"
    },
    "left_leg": {
      "rect": [645, 341, 704, 497],
      "color_range": [[90, 120, 160], [160, 160, 200]],
      "description": "左腿",
      "priority": 4,
      "param_id": "PARAM_RLEG",
      "expression": "neutral",
      "tactile_type": "stroke"
    },
    "right_leg": {
      "rect": [733, 341, 792, 497],
      "color_range": [[90, 120, 160], [160, 160, 200]],
      "description": "右腿",
      "priority": 4,
      "param_id": "PARAM_RLEG",
      "expression": "neutral",
      "tactile_type": "stroke"
    },
    "hair": {
      "rect": [528, 46, 879, 320],
      "color_range": [[180, 130, 160], [255, 200, 220]],
      "description": "頭髮",
      "priority": 10,
      "param_id": "PARAM_HAIR_FRONT",
      "expression": "happy",
      "tactile_type": "stroke"
    }
  },
  "body_parts": {
    "face": { "rect": [630, 71, 777, 156], "color_range": [[200, 180, 180], [255, 235, 225]], "description": "臉部", "priority": 1 },
    "eyes": { "rect": [660, 99, 748, 117], "color_range": [[100, 50, 10], [200, 120, 180]], "description": "眼睛", "priority": 1 },
    "mouth": { "rect": [682, 124, 726, 135], "color_range": [[200, 100, 130], [240, 140, 170]], "description": "嘴巴", "priority": 1 },
    "neck": { "rect": [652, 152, 755, 184], "color_range": [[200, 180, 180], [255, 235, 225]], "description": "脖子", "priority": 2 },
    "shoulders": { "rect": [630, 181, 777, 213], "color_range": [[180, 100, 150], [255, 240, 230]], "description": "肩膀", "priority": 2 },
    "torso": { "rect": [638, 206, 770, 341], "color_range": [[100, 60, 150], [180, 150, 200]], "description": "軀幹/衣服", "priority": 2 },
    "right_hand": { "rect": [762, 113, 806, 156], "color_range": [[200, 180, 180], [255, 235, 225]], "description": "右手", "priority": 3 },
    "left_hand": { "rect": [616, 341, 660, 369], "color_range": [[200, 180, 180], [255, 235, 225]], "description": "左手", "priority": 3 },
    "right_arm": { "rect": [718, 113, 821, 298], "color_range": [[180, 100, 150], [255, 235, 225]], "description": "右手臂", "priority": 4 },
    "left_arm": { "rect": [601, 270, 674, 362], "color_range": [[180, 100, 150], [255, 235, 225]], "description": "左手臂", "priority": 4 },
    "left_leg": { "rect": [645, 341, 704, 497], "color_range": [[90, 120, 160], [160, 160, 200]], "description": "左腿", "priority": 4 },
    "right_leg": { "rect": [733, 341, 792, 497], "color_range": [[90, 120, 160], [160, 160, 200]], "description": "右腿", "priority": 4 },
    "hair": { "rect": [528, 46, 879, 320], "color_range": [[180, 130, 160], [255, 200, 220]], "description": "頭髮", "priority": 10 }
  },
  "metadata": {
    "generated_at": "2026-02-10 12:27:12.871132",
    "source_image": "/home/cat/桌面/Gemini_Generated_Image_hqq027hqq027hqq0.png",
    "description": "Angela character with body part mapping for tactile interaction",
    "notes": "Priority 1 = detail zones (face, eyes, mouth), Priority 10 = hair (fallback)"
  }
};

// 導出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ANGELA_CHARACTER_CONFIG;
}