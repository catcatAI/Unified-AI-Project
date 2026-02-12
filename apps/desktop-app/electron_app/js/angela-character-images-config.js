/**
 * Angela AI - 立繪圖片配置
 * 
 * 定義所有可用的立繪圖片及其渲染參數
 */

window.ANGELA_CHARACTER_IMAGES = {
  // 圖片 1: 表情包 (2×4 網格, 8種表情)
  // 來源: Gemini_Generated_Image_d9altad9altad9al.png
  // 實際尺寸: 1408×736 px
  // 每格尺寸: 352×368 px
  'expression_pack_1': {
    name: '表情包 1',
    path: 'resources/Gemini_Generated_Image_d9altad9altad9al.png',
    type: 'sprite_sheet',
    grid: { rows: 2, cols: 4 },
    cellSize: { width: 352, height: 368 },
    totalSize: { width: 1408, height: 736 },
    expressions: [
      { name: 'neutral', index: 0, gridX: 0, gridY: 0 },
      { name: 'happy', index: 1, gridX: 1, gridY: 0 },
      { name: 'sad', index: 2, gridX: 2, gridY: 0 },
      { name: 'surprised', index: 3, gridX: 3, gridY: 0 },
      { name: 'angry', index: 4, gridX: 0, gridY: 1 },
      { name: 'shy', index: 5, gridX: 1, gridY: 1 },
      { name: 'love', index: 6, gridX: 2, gridY: 1 },
      { name: 'calm', index: 7, gridX: 3, gridY: 1 }
    ],
    renderParams: {
      targetWidth: 352,
      targetHeight: 368,
      offsetX: 0,
      offsetY: 0,
      scaleX: 1.0,
      scaleY: 1.0,
      scaleToHeight: 720  // 目標高度 720（與 canvas 一致）
    }
  },

  // 圖片 2: 全身立繪（AI 助手 UI 概念）
  // 來源: Gemini_Generated_Image_hqq027hqq027hqq0.png
  // 實際尺寸: 1408×768 px
  'fullbody_ai_assistant': {
    name: 'AI 助手',
    path: 'resources/Gemini_Generated_Image_hqq027hqq027hqq0.png',
    type: 'single_image',
    totalSize: { width: 1408, height: 768 },
    renderParams: {
      targetWidth: 1408,
      targetHeight: 768,
      offsetX: 0,
      offsetY: 0,
      scaleX: 1.0,
      scaleY: 1.0,
      scaleToHeight: 720  // 目標高度 720（與 canvas 一致）
    }
  },

  // 圖片 3: 姿態序列（2×4 網格, 8格姿態）
  // 來源: Gemini_Generated_Image_z3pzi0z3pzi0z3pz.png
  // 實際尺寸: 1408×736 px
  // 每格尺寸: 352×368 px
  'pose_sequence_1': {
    name: '姿態序列 1',
    path: 'resources/Gemini_Generated_Image_z3pzi0z3pzi0z3pz.png',
    type: 'sprite_sheet',
    grid: { rows: 2, cols: 4 },
    cellSize: { width: 352, height: 368 },
    totalSize: { width: 1408, height: 736 },
    poses: [
      { name: 'idle', index: 0, gridX: 0, gridY: 0 },
      { name: 'thinking', index: 1, gridX: 1, gridY: 0 },
      { name: 'dancing', index: 2, gridX: 2, gridY: 0 },
      { name: 'clapping', index: 3, gridX: 3, gridY: 0 },
      { name: 'waving', index: 4, gridX: 0, gridY: 1 },
      { name: 'nodding', index: 5, gridX: 1, gridY: 1 },
      { name: 'shaking', index: 6, gridX: 2, gridY: 1 },
      { name: 'pointing', index: 7, gridX: 3, gridY: 1 }
    ],
    renderParams: {
      targetWidth: 352,
      targetHeight: 368,
      offsetX: 0,
      offsetY: 0,
      scaleX: 1.0,
      scaleY: 1.0,
      scaleToHeight: 720  // 目標高度 720
    }
  },

  // 默認立繪（舊版 Angela）
  // 來源: angela_character_masked.png
  // 實際尺寸: 1408×768 px
  // 角色實際區域: x=508, y=26, width=391, height=491
  // 角色中心: (703, 271)，畫布中心: (704, 384)
  // 偏移: 水平-1（幾乎居中），垂直-113（偏上）
  'default': {
    name: '默認立繪',
    path: 'resources/angela_character_masked.png',
    type: 'single_image',
    totalSize: { width: 1408, height: 768 },
    characterRegion: {
      x: 508,
      y: 26,
      width: 391,
      height: 491
    },
    renderParams: {
      targetWidth: 391,    // 角色實際寬度
      targetHeight: 491,   // 角色實際高度
      offsetX: 508,        // 角色實際偏移
      offsetY: 26,         // 角色實際偏移
      scaleX: 1.0,
      scaleY: 1.0,
      scaleToHeight: 720   // 目標高度 720（與 canvas 一致）
    }
  }
};

// 導出到全局
if (typeof window !== 'undefined') {
  window.ANGELA_CHARACTER_IMAGES = ANGELA_CHARACTER_IMAGES;
}

// ES6 模塊導出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ANGEL_CHARACTER_IMAGES;
}