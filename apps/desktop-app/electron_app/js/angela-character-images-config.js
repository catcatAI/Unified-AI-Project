/**
 * Angela AI - 立繫圖片配置
 * 
 * 三層渲染架構 - 修正版 v5
 * - Layer 1: 主立繫層 (base) - fullbody_ai_assistant
 * - Layer 2: 表情疊加層 (expression) - expression_pack_1 (只包含面部)
 * - Layer 3: 姿態疊加層 (pose) - pose_sequence_1 (⚠️ 包含完整上半身+頭部，需要頭部遮罩)
 * 
 * 修正問題：
 * 1. ⚠️ 姿態序列包含完整上半身和頭部，會導致三個頭部疊加顯示
 * 2. 解決方案：使用頭部遮罩遮蓋姿態層的頭部區域
 * 3. 所有坐標確保為正數
 * 4. 統一觸覺區域坐標系統為 1280x720 畫布坐標
 */

window.ANGELA_CHARACTER_IMAGES = {
  // ================================================================
  // Layer 1: 主立繫層 (Base Layer)
  // ================================================================
  'fullbody_ai_assistant': {
    name: 'AI 助手',
    path: 'resources/Gemini_Generated_Image_hqq027hqq027hqq0.png',
    type: 'single_image',
    layer: 'base',
    zIndex: 0,
    totalSize: { width: 1408, height: 768 },
    renderParams: {
      targetWidth: 1408,
      targetHeight: 768,
      offsetX: 0,
      offsetY: 0,
      scaleToHeight: 720
    },
    // 主立繫觸覺區域 - 基於 1280x720 畫布坐標
    touchRegions: {
      head: {
        x: 640, y: 100, width: 180, height: 180,
        priority: 1,
        sensitivity: 0.8,
        reaction: 'look_at'
      },
      body: {
        x: 640, y: 280, width: 220, height: 280,
        priority: 2,
        sensitivity: 0.6,
        reaction: 'giggle'
      },
      hands: {
        x: 640, y: 560, width: 140, height: 80,
        priority: 3,
        sensitivity: 0.5,
        reaction: 'wave_back'
      }
    }
  },

  // ================================================================
  // Layer 2: 表情疊加層 (Expression Layer)
  // ================================================================
  'expression_pack_1': {
    name: '表情包 1',
    path: 'resources/Gemini_Generated_Image_d9altad9altad9al.png',
    type: 'sprite_sheet',
    layer: 'expression',
    zIndex: 1,
    grid: { rows: 2, cols: 4 },
    cellSize: { width: 352, height: 328 },
    totalSize: { width: 1408, height: 736 },
    renderParams: {
      targetWidth: 352,
      targetHeight: 368,
      offsetX: 0,
      offsetY: 0,
      scaleToHeight: 720,
      opacity: 0.95,
      blendMode: 'source-over'
    },
    expressions: [
      { name: 'neutral', index: 0, gridX: 0, gridY: 0, emotion: 'neutral' },
      { name: 'happy', index: 1, gridX: 1, gridY: 0, emotion: 'happy' },
      { name: 'sad', index: 2, gridX: 2, gridY: 0, emotion: 'sad' },
      { name: 'surprised', index: 3, gridX: 3, gridY: 0, emotion: 'surprised' },
      { name: 'angry', index: 4, gridX: 0, gridY: 1, emotion: 'angry' },
      { name: 'shy', index: 5, gridX: 1, gridY: 1, emotion: 'shy' },
      { name: 'love', index: 6, gridX: 2, gridY: 1, emotion: 'love' },
      { name: 'calm', index: 7, gridX: 3, gridY: 1, emotion: 'calm' }
    ],
    // 表情疊加位置 - 只疊加面部區域
    // ✅ 表情包只包含頭部+頸部+鎖骨，所以可以完整疊加
    expressionOverlayPositions: {
      'neutral': {
        sourceX: 0, sourceY: 0,
        targetX: 640, targetY: 113,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'happy': {
        sourceX: 352, sourceY: 0,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'sad': {
        sourceX: 704, sourceY: 0,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'surprised': {
        sourceX: 1056, sourceY: 0,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'angry': {
        sourceX: 0, sourceY: 368,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'shy': {
        sourceX: 352, sourceY: 368,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'love': {
        sourceX: 704, sourceY: 368,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      },
      'calm': {
        sourceX: 1056, sourceY: 368,
        targetX: 480, targetY: 50,
        targetWidth: 320, targetHeight: 222,
        opacity: 0.95,
        useMask: true
      }
    },
    // 表情觸覺區域
    expressionTouchRegions: {
      'neutral': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.7, reaction: 'blink' }
      },
      'happy': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.8, reaction: 'giggle' },
        cheeks: { x: 620, y: 160, width: 200, height: 60, priority: 1, sensitivity: 0.9, reaction: 'blush' }
      },
      'sad': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.9, reaction: 'look_down' },
        eyes: { x: 655, y: 130, width: 70, height: 30, priority: 1, sensitivity: 1.0, reaction: 'tear_up' }
      },
      'surprised': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.9, reaction: 'widening' },
        eyes: { x: 655, y: 130, width: 70, height: 30, priority: 1, sensitivity: 1.0, reaction: 'sparkle' }
      },
      'angry': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.8, reaction: 'frown' }
      },
      'shy': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.9, reaction: 'look_away' },
        cheeks: { x: 620, y: 160, width: 200, height: 60, priority: 1, sensitivity: 1.0, reaction: 'blush_deep' }
      },
      'love': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.9, reaction: 'heart_eyes' }
      },
      'calm': {
        head: { x: 640, y: 100, width: 160, height: 160, priority: 1, sensitivity: 0.6, reaction: 'close_eyes' }
      }
    }
  },

  // ================================================================
  // Layer 3: 姿態疊加層 (Pose Layer)
  // ================================================================
  'pose_sequence_1': {
    name: '姿態序列 1',
    path: 'resources/Gemini_Generated_Image_z3pzi0z3pzi0z3pz.png',
    type: 'sprite_sheet',
    layer: 'pose',
    zIndex: 2,
    grid: { rows: 2, cols: 4 },
    cellSize: { width: 352, height: 328 },
    totalSize: { width: 1408, height: 736 },
    renderParams: {
      targetWidth: 352,
      targetHeight: 368,
      offsetX: 0,
      offsetY: 0,
      scaleToHeight: 720,
      opacity: 0.5,
      blendMode: 'source-over'
    },
    poses: [
      { name: 'idle', index: 0, gridX: 0, gridY: 0, action: 'idle' },
      { name: 'greeting', index: 1, gridX: 1, gridY: 0, action: 'greeting' },
      { name: 'thinking', index: 2, gridX: 2, gridY: 0, action: 'thinking' },
      { name: 'dancing', index: 3, gridX: 3, gridY: 0, action: 'dancing' },
      { name: 'clapping', index: 4, gridX: 0, gridY: 1, action: 'clapping' },
      { name: 'nodding', index: 5, gridX: 1, gridY: 1, action: 'nodding' },
      { name: 'shaking', index: 6, gridX: 2, gridY: 1, action: 'shaking' },
      { name: 'dancing2', index: 7, gridX: 3, gridY: 1, action: 'dancing' }
    ],
    // 姿態疊加位置 - ⚠️ 關鍵修復
    // 姿態序列包含完整上半身+頭部，需要使用頭部遮罩
    // headMaskRect: 遮蓋姿態層的頭部區域，只保留手勢/身體部分
    poseOverlayPositions: {
      'idle' : {
        sourceX: 0, sourceY: 0,
        targetX: 640, targetY: 350,
        targetWidth: 200, targetHeight: 133,
        opacity: 0.3,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'greeting' : {
        sourceX: 352, sourceY: 0,
        targetX: 640, targetY: 280,
        targetWidth: 250, targetHeight: 178,
        opacity: 0.4,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'thinking' : {
        sourceX: 704, sourceY: 0,
        targetX: 640, targetY: 280,
        targetWidth: 150, targetHeight: 133,
        opacity: 0.4,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'dancing' : {
        sourceX: 1056, sourceY: 0,
        targetX: 640, targetY: 250,
        targetWidth: 300, targetHeight: 222,
        opacity: 0.4,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'clapping' : {
        sourceX: 0, sourceY: 368,
        targetX: 640, targetY: 300,
        targetWidth: 200, targetHeight: 133,
        opacity: 0.4,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'nodding' : {
        sourceX: 352, sourceY: 368,
        targetX: 640, targetY: 350,
        targetWidth: 180, targetHeight: 106,
        opacity: 0.3,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'shaking' : {
        sourceX: 704, sourceY: 368,
        targetX: 640, targetY: 280,
        targetWidth: 220, targetHeight: 160,
        opacity: 0.4,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      },
      'dancing2' : {
        sourceX: 1056, sourceY: 368,
        targetX: 640, targetY: 250,
        targetWidth: 300, targetHeight: 222,
        opacity: 0.4,
        useMask: true,
        // 頭部遮罩
        headMaskRect: {
          x: 630,    // 修正：基於基礎層臉部 rect [630, 71, 777, 156]
          y: 71,
          width: 147,  // 臉部寬度
          height: 85    // 臉部高度
        },
        // 手部遮罩
        handMaskRects: [
          { x: 616, y: 341, width: 44, height: 28 },
          { x: 762, y: 113, width: 44, height: 43 }
        ]
      }
    },
    // 姿態觸覺區域
    poseTouchRegions: {
      'idle': {
        hands: { x: 640, y: 560, width: 140, height: 80, priority: 3, sensitivity: 0.5, reaction: 'wave_back' }
      },
      'greeting': {
        hands: { x: 640, y: 300, width: 200, height: 150, priority: 3, sensitivity: 0.8, reaction: 'wave_back' }
      },
      'thinking': {
        hands: { x: 640, y: 300, width: 150, height: 150, priority: 3, sensitivity: 0.8, reaction: 'tap_chin' }
      },
      'dancing': {
        hands: { x: 640, y: 280, width: 300, height: 250, priority: 3, sensitivity: 1.0, reaction: 'wave' }
      },
      'clapping': {
        hands: { x: 640, y: 350, width: 200, height: 150, priority: 3, sensitivity: 1.0, reaction: 'clap_response' }
      },
      'nodding': {
        hands: { x: 640, y: 400, width: 180, height: 120, priority: 3, sensitivity: 0.7, reaction: 'nod' }
      },
      'shaking': {
        hands: { x: 640, y: 300, width: 220, height: 180, priority: 3, sensitivity: 0.9, reaction: 'wave_no' }
      },
      'dancing2': {
        hands: { x: 640, y: 280, width: 300, height: 250, priority: 3, sensitivity: 1.0, reaction: 'wave' }
      }
    }
  }
};

/**
 * 密度調整輔助函數
 * 根據屏幕密度（devicePixelRatio）調整坐標和尺寸
 * @param {object} position - 原始位置坐標
 * @param {number} density - 屏幕密度（默認為 1）
 * @returns {object} 調整後的位置坐標
 */
function adjustPositionForDensity(position, density = 1) {
  if (!position || typeof density !== 'number' || density <= 0) {
    return position;
  }

  const adjusted = { ...position };

  // 調整所有坐標和尺寸
  if (typeof adjusted.x === 'number') adjusted.x *= density;
  if (typeof adjusted.y === 'number') adjusted.y *= density;
  if (typeof adjusted.width === 'number') adjusted.width *= density;
  if (typeof adjusted.height === 'number') adjusted.height *= density;
  if (typeof adjusted.sourceX === 'number') adjusted.sourceX *= density;
  if (typeof adjusted.sourceY === 'number') adjusted.sourceY *= density;
  if (typeof adjusted.targetX === 'number') adjusted.targetX *= density;
  if (typeof adjusted.targetY === 'number') adjusted.targetY *= density;
  if (typeof adjusted.targetWidth === 'number') adjusted.targetWidth *= density;
  if (typeof adjusted.targetHeight === 'number') adjusted.targetHeight *= density;

  return adjusted;
}

/**
 * 調整所有表達式疊加位置以適應屏幕密度
 * @param {object} overlayPositions - 原始疊加位置
 * @param {number} density - 屏幕密度
 * @returns {object} 調整後的疊加位置
 */
function adjustOverlayPositionsForDensity(overlayPositions, density = 1) {
  if (!overlayPositions || typeof density !== 'number' || density <= 0) {
    return overlayPositions;
  }

  const adjusted = {};

  for (const [expression, position] of Object.entries(overlayPositions)) {
    adjusted[expression] = adjustPositionForDensity(position, density);
  }

  return adjusted;
}

/**
 * 獲取當前屏幕密度
 * @returns {number} devicePixelRatio
 */
function getCurrentDensity() {
  return typeof window !== 'undefined' && window.devicePixelRatio
    ? window.devicePixelRatio
    : 1;
}

/**
 * 獲取調整後的表達式疊加位置（使用當前屏幕密度）
 * @param {object} overlayPositions - 原始疊加位置
 * @returns {object} 調整後的疊加位置
 */
function getDensityAdjustedOverlayPositions(overlayPositions) {
  const density = getCurrentDensity();
  return adjustOverlayPositionsForDensity(overlayPositions, density);
}

// 導出到全局
if (typeof window !== 'undefined') {
  window.ANGELA_CHARACTER_IMAGES = ANGELA_CHARACTER_IMAGES;
  window.adjustPositionForDensity = adjustPositionForDensity;
  window.adjustOverlayPositionsForDensity = adjustOverlayPositionsForDensity;
  window.getCurrentDensity = getCurrentDensity;
  window.getDensityAdjustedOverlayPositions = getDensityAdjustedOverlayPositions;
}

// ES6 模塊導出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ANGELA_CHARACTER_IMAGES;
}