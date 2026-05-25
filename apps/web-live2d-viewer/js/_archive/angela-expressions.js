/**
 * Angela AI Expression Configuration
 * 8 種基礎情緒表情配置
 * 
 * Based on Gemini Expression Sheet Analysis
 * Grid: 2 rows x 4 columns, 1024x512px
 */

const ANGELA_EXPRESSIONS = {
    // 圖片基本信息
    image_info: {
        path: 'resources/angela_expressions.png',
        width: 1024,
        height: 512,
        grid_rows: 2,
        grid_cols: 4,
        cell_width: 256,
        cell_height: 256
    },
    
    // 表情定義
    expressions: {
        // Row 1
        'neutral': {
            id: 'neutral',
            name: '中性',
            name_en: 'Neutral',
            grid_position: { row: 0, col: 0 },
            // 裁剪區域 (相對於原圖)
            crop: { x: 0, y: 0, width: 256, height: 256 },
            // Live2D 參數映射
            live2d_params: {
                'ParamEyeLOpen': 1.0,
                'ParamEyeROpen': 1.0,
                'ParamEyeLSmile': 0.0,
                'ParamEyeRSmile': 0.0,
                'ParamBrowLY': 0.0,
                'ParamBrowRY': 0.0,
                'ParamBrowLAngle': 0.0,
                'ParamBrowRAngle': 0.0,
                'ParamMouthForm': 0.0,
                'ParamMouthOpenY': 0.0,
                'ParamCheek': 0.0
            },
            // 描述
            description: '平静、自然的微笑，眼神平和直视前方',
            trigger_conditions: ['idle', 'listening', 'waiting']
        },
        
        'happy': {
            id: 'happy',
            name: '開心',
            name_en: 'Happy',
            grid_position: { row: 0, col: 1 },
            crop: { x: 256, y: 0, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 0.8,
                'ParamEyeROpen': 0.8,
                'ParamEyeLSmile': 1.0,
                'ParamEyeRSmile': 1.0,
                'ParamBrowLY': 0.2,
                'ParamBrowRY': 0.2,
                'ParamBrowLAngle': 0.1,
                'ParamBrowRAngle': 0.1,
                'ParamMouthForm': 0.5,
                'ParamMouthOpenY': 0.3,
                'ParamCheek': 0.5
            },
            description: '大幅度的開心笑容，眼睛彎成月牙，臉頰泛紅',
            trigger_conditions: ['greeting', 'success', 'praise', 'celebration']
        },
        
        'sad': {
            id: 'sad',
            name: '悲傷',
            name_en: 'Sad',
            grid_position: { row: 0, col: 2 },
            crop: { x: 512, y: 0, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 0.6,
                'ParamEyeROpen': 0.6,
                'ParamEyeLSmile': -0.5,
                'ParamEyeRSmile': -0.5,
                'ParamBrowLY': -0.3,
                'ParamBrowRY': -0.3,
                'ParamBrowLAngle': -0.2,
                'ParamBrowRAngle': -0.2,
                'ParamMouthForm': -0.5,
                'ParamMouthOpenY': 0.0,
                'ParamCheek': 0.0
            },
            description: '眼神哀傷，眼眶濕潤含淚，嘴角下撇',
            trigger_conditions: ['ignored', 'failure', 'bad_news', 'sympathy_needed']
        },
        
        // NOTE: 原始圖片標籤為 THINKING，但實際表情為驚訝 (SURPRISED)
        'surprised': {
            id: 'surprised',
            name: '驚訝',
            name_en: 'Surprised',
            alt_label: 'THINKING',  // 原始標籤
            grid_position: { row: 0, col: 3 },
            crop: { x: 768, y: 0, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 1.2,
                'ParamEyeROpen': 1.2,
                'ParamEyeLSmile': 0.0,
                'ParamEyeRSmile': 0.0,
                'ParamBrowLY': 0.4,
                'ParamBrowRY': 0.4,
                'ParamBrowLAngle': 0.2,
                'ParamBrowRAngle': 0.2,
                'ParamMouthForm': 0.0,
                'ParamMouthOpenY': 0.5,
                'ParamCheek': 0.3
            },
            description: '驚訝地睜大眼睛，嘴巴微張呈 O 型',
            trigger_conditions: ['sudden_realization', 'unexpected_event', 'question_mark']
        },
        
        // Row 2
        'angry': {
            id: 'angry',
            name: '憤怒',
            name_en: 'Angry',
            grid_position: { row: 1, col: 0 },
            crop: { x: 0, y: 256, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 0.7,
                'ParamEyeROpen': 0.7,
                'ParamEyeLSmile': -0.8,
                'ParamEyeRSmile': -0.8,
                'ParamBrowLY': -0.6,
                'ParamBrowRY': -0.6,
                'ParamBrowLAngle': -0.5,
                'ParamBrowRAngle': -0.5,
                'ParamMouthForm': -0.7,
                'ParamMouthOpenY': 0.0,
                'ParamCheek': 0.7
            },
            description: '雙眉緊鎖，眼神銳利，嘴唇緊抿，臉頰泛紅',
            trigger_conditions: ['error', 'frustration', 'objection', 'system_error']
        },
        
        'shy': {
            id: 'shy',
            name: '害羞',
            name_en: 'Shy',
            grid_position: { row: 1, col: 1 },
            crop: { x: 256, y: 256, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 0.5,
                'ParamEyeROpen': 0.5,
                'ParamEyeLSmile': 0.2,
                'ParamEyeRSmile': 0.2,
                'ParamBrowLY': 0.1,
                'ParamBrowRY': 0.1,
                'ParamBrowLAngle': 0.0,
                'ParamBrowRAngle': 0.0,
                'ParamMouthForm': -0.2,
                'ParamMouthOpenY': 0.0,
                'ParamCheek': 0.8
            },
            description: '眼神躲閃，臉頰大面積泛紅，表情靦腆',
            trigger_conditions: ['praise', 'intimate_topic', 'compliment', 'maturity_l4_plus']
        },
        
        'love': {
            id: 'love',
            name: '喜愛',
            name_en: 'Love',
            grid_position: { row: 1, col: 2 },
            crop: { x: 512, y: 256, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 0.9,
                'ParamEyeROpen': 0.9,
                'ParamEyeLSmile': 0.8,
                'ParamEyeRSmile': 0.8,
                'ParamBrowLY': 0.1,
                'ParamBrowRY': 0.1,
                'ParamBrowLAngle': 0.0,
                'ParamBrowRAngle': 0.0,
                'ParamMouthForm': 0.3,
                'ParamMouthOpenY': 0.1,
                'ParamCheek': 0.9
            },
            description: '眼神溫柔呈心形，臉頰泛紅，表情甜蜜',
            trigger_conditions: ['affection', 'deep_connection', 'love_topic', 'long_term_user']
        },
        
        // NOTE: 原始圖片標籤為 THINKING，實際為沉思/保密姿勢
        'thinking': {
            id: 'thinking',
            name: '思考',
            name_en: 'Thinking',
            grid_position: { row: 1, col: 3 },
            crop: { x: 768, y: 256, width: 256, height: 256 },
            live2d_params: {
                'ParamEyeLOpen': 0.7,
                'ParamEyeROpen': 0.7,
                'ParamEyeLSmile': 0.1,
                'ParamEyeRSmile': 0.1,
                'ParamBrowLY': 0.2,
                'ParamBrowRY': 0.2,
                'ParamBrowLAngle': 0.1,
                'ParamBrowRAngle': 0.1,
                'ParamMouthForm': -0.1,
                'ParamMouthOpenY': 0.0,
                'ParamCheek': 0.2
            },
            description: '食指抵唇，眼神若有所思，俏皮神秘',
            trigger_conditions: ['processing_question', 'complex_reasoning', 'gpt_inference']
        }
    },
    
    // 4D 矩陣觸發映射
    matrix_triggers: {
        'high_alpha_high_beta': 'happy',      // 高喚醒 + 高愉悅
        'high_alpha_low_beta': 'surprised',   // 高喚醒 + 低愉悅
        'low_alpha_high_beta': 'shy',        // 低喚醒 + 高愉悅
        'low_alpha_low_beta': 'sad',          // 低喚醒 + 低愉悅
        'high_gamma_low_beta': 'angry',      // 高支配 + 低愉悅
        'high_delta_high_beta': 'love',       // 高專注 + 高愉悅
        'high_delta': 'thinking'              // 高專注
    },
    
    // 過渡動畫配置
    transitions: {
        default_duration: 300,  // ms
        smooth_params: ['ParamEyeLOpen', 'ParamEyeROpen', 'ParamMouthOpenY'],
        instant_params: ['ParamCheek']  // 臉紅立即生效
    }
};

// 導出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ANGELA_EXPRESSIONS;
}
