/**
 * Angela AI - 立繪圖片配置
 * 
 * 定義所有可用的立繪圖片及其渲染參數
 */

window.ANGELA_CHARACTER_IMAGES = {
  // 圖片 1: 表情包 (2×4 網格, 8種表情)
  // 來源: Gemini_Generated_Image_d9altad9altad9al.png
  // 實際尺寸: 2048×1024 px
  // 每格尺寸: 256×512 px
  'expression_pack_1': {
    name: '表情包 1',
    path: 'resources/Gemini_Generated_Image_d9altad9altad9al.png',
    type: 'sprite_sheet',
    grid: { rows: 2, cols: 4 },
    cellSize: { width: 256, height: 512 },
    totalSize: { width: 2048, height: 1024 },
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
    // 渲染參數（根據實際圖片分析）
    renderParams: {
      targetWidth: 256,
      targetHeight: 512,
      offsetX: 0,
      offsetY: 0,
      scaleX: 1.0,
      scaleY: 1.0
    }
  },

  // 圖片 2: 全身立繪（AI 助手 UI 概念）
  // 來源: Gemini_Generated_Image_hqq027hqq027hqq0.png
  // 實際尺寸: 1920×1080 px
  // 角色區域: 約 620×980 px
  // 畫面構圖: 全身站立，右手舉起，中心略偏左
  'fullbody_ai_assistant': {
    name: 'AI 助手',
    path: 'resources/Gemini_Generated_Image_hqq027hqq027hqq0.png',
    type: 'single_image',
    totalSize: { width: 1920, height: 1080 },
    // 根據分析：角色佔畫面約 55% 寬 × 70% 高
    // 角色本身約 620×980 px，位於畫面垂直中軸偏左 5%
    characterRegion: {
      x: 650,      // 約 (1920 - 620) / 2 = 650 (中心位置)
      y: 50,       // 頂部留白約 50px
      width: 620,
      height: 980
    },
    renderParams: {
      targetWidth: 620,
      targetHeight: 980,
      offsetX: 650,
      offsetY: 50,
      scaleX: 1.0,
      scaleY: 1.0,
      // 根據角色頭身比約 7 head-height 調整
      scaleToHeight: 720  // 目標高度 720（與 canvas 一致）
    }
  },

  // 圖片 3: 姿態序列（4×2 網格, 8格姿態）
  // 來源: Gemini_Generated_Image_z3pzi0z3pzi0z3pz.png
  // 實際尺寸: 1920×1080 px
  // 每格尺寸: 480×540 px（含文字標籤區）
  'pose_sequence_1': {
    name: '姿態序列 1',
    path: 'resources/Gemini_Generated_Image_z3pzi0z3pzi0z3pz.png',
    type: 'sprite_sheet',
    grid: { rows: 2, cols: 4 },
    cellSize: { width: 480, height: 540 },
    totalSize: { width: 1920, height: 1080 },
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
      targetWidth: 480,
      targetHeight: 540,
      offsetX: 0,
      offsetY: 0,
      scaleX: 1.0,
      scaleY: 1.0,
      scaleToHeight: 720  // 目標高度 720
    }
  },

  // 默認立繪（舊版，保持兼容）
  'default': {
    name: '默認立繪',
    path: 'resources/angela_character_masked.png',
    type: 'single_image',
    totalSize: { width: 512, height: 720 },
    renderParams: {
      targetWidth: 512,
      targetHeight: 720,
      offsetX: 0,
      offsetY: 0,
      scaleX: 1.0,
      scaleY: 1.0
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