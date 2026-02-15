/**
 * Angela Character Configuration
 * 自動生成的身體部位配置 - 修復優先級版本
 */

const ANGELA_CHARACTER_CONFIG = {
  "version": "1.1.0",
  "image_path": "resources/angela_character_masked.png",
  "live2d_config": {
    "enabled": true,
    "fallback_enabled": true,
    "model_path": "models/miara_pro_en/runtime/miara_pro_t03.model3.json",
    "fallback_models": [
      "models/miara_pro_en/runtime/miara_pro_t03.model3.json",
      "models/miara_pro/runtime/miara_pro_t03.model3.json"
    ],
    "auto_retry": true,
    "max_retries": 3
  },
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

// 浏览器环境导出
if (typeof window !== 'undefined') {
    window.ANGELA_CHARACTER_CONFIG = ANGELA_CHARACTER_CONFIG;
}

/**
 * 驗證 ANGELA_CHARACTER_CONFIG 的完整性
 * @returns {Object} 驗證結果 { valid: boolean, errors: Array, warnings: Array }
 */
function validateCharacterConfig() {
    const result = {
        valid: true,
        errors: [],
        warnings: []
    };

    // 檢查必需的頂級屬性
    const requiredTopLevelProps = ['version', 'image_path', 'original_size', 'character_bbox', 'touch_zones', 'body_parts'];
    for (const prop of requiredTopLevelProps) {
        if (!ANGELA_CHARACTER_CONFIG[prop]) {
            result.errors.push(`Missing required top-level property: ${prop}`);
            result.valid = false;
        }
    }

    // 驗證版本號格式
    if (ANGELA_CHARACTER_CONFIG.version) {
        const versionRegex = /^\d+\.\d+\.\d+$/;
        if (!versionRegex.test(ANGELA_CHARACTER_CONFIG.version)) {
            result.warnings.push(`Version number may be invalid: ${ANGELA_CHARACTER_CONFIG.version}`);
        }
    }

    // 驗證 original_size
    if (ANGELA_CHARACTER_CONFIG.original_size) {
        const { width, height } = ANGELA_CHARACTER_CONFIG.original_size;
        if (!width || !height || width <= 0 || height <= 0) {
            result.errors.push('Invalid original_size: width and height must be positive numbers');
            result.valid = false;
        }
    }

    // 驗證 character_bbox
    if (ANGELA_CHARACTER_CONFIG.character_bbox) {
        const { x, y, width, height } = ANGELA_CHARACTER_CONFIG.character_bbox;
        if (typeof x !== 'number' || typeof y !== 'number' || typeof width !== 'number' || typeof height !== 'number') {
            result.errors.push('Invalid character_bbox: x, y, width, height must be numbers');
            result.valid = false;
        }
        if (width <= 0 || height <= 0) {
            result.errors.push('Invalid character_bbox: width and height must be positive');
            result.valid = false;
        }
    }

    // 驗證 touch_zones
    if (ANGELA_CHARACTER_CONFIG.touch_zones) {
        const requiredZoneProps = ['rect', 'description', 'priority', 'param_id'];
        const validExpressions = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'confused', 'sleepy', 'blush', 'wink', 'smile', 'excited'];
        const validTactileTypes = ['pat', 'poke', 'stroke'];

        for (const [zoneName, zoneData] of Object.entries(ANGELA_CHARACTER_CONFIG.touch_zones)) {
            // 檢查必需屬性
            for (const prop of requiredZoneProps) {
                if (!zoneData[prop]) {
                    result.errors.push(`Touch zone "${zoneName}" missing required property: ${prop}`);
                    result.valid = false;
                }
            }

            // 驗證 rect 格式
            if (zoneData.rect) {
                if (!Array.isArray(zoneData.rect) || zoneData.rect.length !== 4) {
                    result.errors.push(`Touch zone "${zoneName}" has invalid rect format: expected [x1, y1, x2, y2]`);
                    result.valid = false;
                }
            }

            // 驗證 priority
            if (typeof zoneData.priority !== 'number') {
                result.errors.push(`Touch zone "${zoneName}" has invalid priority: must be a number`);
                result.valid = false;
            }

            // 驗證 expression
            if (zoneData.expression && !validExpressions.includes(zoneData.expression)) {
                result.warnings.push(`Touch zone "${zoneName}" has unknown expression: ${zoneData.expression}`);
            }

            // 驗證 tactile_type
            if (zoneData.tactile_type && !validTactileTypes.includes(zoneData.tactile_type)) {
                result.warnings.push(`Touch zone "${zoneName}" has unknown tactile_type: ${zoneData.tactile_type}`);
            }
        }
    }

    // 驗證 body_parts（應該與 touch_zones 一致）
    if (ANGELA_CHARACTER_CONFIG.body_parts) {
        const touchZoneNames = Object.keys(ANGELA_CHARACTER_CONFIG.touch_zones || {});
        const bodyPartNames = Object.keys(ANGELA_CHARACTER_CONFIG.body_parts);

        for (const partName of bodyPartNames) {
            if (!touchZoneNames.includes(partName)) {
                result.warnings.push(`Body part "${partName}" exists in body_parts but not in touch_zones`);
            }
        }

        for (const zoneName of touchZoneNames) {
            if (!bodyPartNames.includes(zoneName)) {
                result.warnings.push(`Touch zone "${zoneName}" exists in touch_zones but not in body_parts`);
            }
        }
    }

    // 檢查圖片路徑是否存在
    if (ANGELA_CHARACTER_CONFIG.image_path && typeof window !== 'undefined') {
        // 在瀏覽器環境中檢查圖片是否可加載
        const img = new Image();
        img.onload = () => console.log(`[CharacterConfig] Image found: ${ANGELA_CHARACTER_CONFIG.image_path}`);
        img.onerror = () => {
            result.warnings.push(`Image not found or cannot be loaded: ${ANGELA_CHARACTER_CONFIG.image_path}`);
        };
        img.src = ANGELA_CHARACTER_CONFIG.image_path;
    }

    return result;
}

// 導出驗證函數
if (typeof module !== 'undefined' && module.exports) {
    module.exports.validateCharacterConfig = validateCharacterConfig;
}

// 浏览器环境导出
if (typeof window !== 'undefined') {
    window.validateCharacterConfig = validateCharacterConfig;
}

// 自動驗證（在開發模式下）
if (typeof window !== 'undefined' && window.location && window.location.hostname === 'localhost') {
    const validation = validateCharacterConfig();
    if (!validation.valid) {
        console.error('[CharacterConfig] Validation failed:', validation.errors);
    } else {
        console.log('[CharacterConfig] Validation passed');
    }
    if (validation.warnings.length > 0) {
        console.warn('[CharacterConfig] Validation warnings:', validation.warnings);
    }
}