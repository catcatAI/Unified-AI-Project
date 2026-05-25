/**
 * Angela AI Pose Configuration
 * 8 種動作姿態配置
 * 
 * Based on Gemini Pose Sheet Analysis
 * Grid: 2 rows x 4 columns, 1920x1080px
 */

const ANGELA_POSES = {
    // 圖片基本信息
    image_info: {
        path: 'resources/angela_poses.png',
        width: 1920,
        height: 1080,
        grid_rows: 2,
        grid_cols: 4,
        cell_width: 480,
        cell_height: 540,
        character_scale: 0.35  // 角色在格子中的相對大小
    },
    
    // 姿態定義
    poses: {
        'idle': {
            id: 'idle',
            name: '待機',
            name_en: 'Idle',
            grid_position: { row: 0, col: 0 },
            crop: { x: 0, y: 0, width: 480, height: 540 },
            
            // Live2D 姿勢參數 (angle/rotation)
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': 0,
                'ParamAngleZ': 0,
                'ParamBodyAngleX': 0,
                'ParamBodyAngleY': 0,
                'ParamBodyAngleZ': 0
            },
            
            // 手部位置參數
            hand_params: {
                'ParamArmL': 0,
                'ParamArmR': 0,
                'ParamHandL': 0,
                'ParamHandR': 0
            },
            
            description: '站立姿態，雙腳併攏，放鬆站姿，溫和微笑',
            usage_scenarios: ['default', 'listening', 'idle_state'],
            priority: 1
        },
        
        'greeting': {
            id: 'greeting',
            name: '問候',
            name_en: 'Greeting',
            grid_position: { row: 0, col: 1 },
            crop: { x: 480, y: 0, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': 5,
                'ParamAngleZ': 0,
                'ParamBodyAngleX': 2,
                'ParamBodyAngleY': 3,
                'ParamBodyAngleZ': 0
            },
            
            hand_params: {
                'ParamArmL': 0,
                'ParamArmR': 0,
                'ParamHandL': 0,
                'ParamHandR': 0
            },
            
            description: '上半身特寫，稍微前傾，熱情開朗的笑容',
            usage_scenarios: ['greeting', 'welcome', 'new_session'],
            priority: 2
        },
        
        'thinking': {
            id: 'thinking',
            name: '思考',
            name_en: 'Thinking',
            grid_position: { row: 0, col: 2 },
            crop: { x: 960, y: 0, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': 10,
                'ParamAngleZ': 0,
                'ParamBodyAngleX': 3,
                'ParamBodyAngleY': 5,
                'ParamBodyAngleZ': 2
            },
            
            hand_params: {
                'ParamArmL': 15,
                'ParamArmR': 20,
                'ParamHandL': 5,
                'ParamHandR': 10  // 右手食指觸碰臉頰
            },
            
            description: '身體稍微側傾，右手食指觸碰臉頰，眼神若有所思',
            usage_scenarios: ['processing', 'reasoning', 'problem_solving'],
            priority: 3
        },
        
        'dancing_1': {
            id: 'dancing_1',
            name: '舞蹈1',
            name_en: 'Dancing 1',
            grid_position: { row: 0, col: 3 },
            crop: { x: 1440, y: 0, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': -10,
                'ParamAngleZ': 5,
                'ParamBodyAngleX': 5,
                'ParamBodyAngleY': -5,
                'ParamBodyAngleZ': 10
            },
            
            hand_params: {
                'ParamArmL': -20,
                'ParamArmR': 25,
                'ParamHandL': 0,
                'ParamHandR': 5
            },
            
            description: '動態姿勢，身體微微扭轉，右腿向前，活潑開心',
            usage_scenarios: ['celebration', 'music_mode', 'happy_state'],
            priority: 4
        },
        
        'clapping': {
            id: 'clapping',
            name: '鼓掌',
            name_en: 'Clapping',
            grid_position: { row: 1, col: 0 },
            crop: { x: 0, y: 540, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': 0,
                'ParamAngleZ': 0,
                'ParamBodyAngleX': 0,
                'ParamBodyAngleY': 0,
                'ParamBodyAngleZ': 0
            },
            
            hand_params: {
                'ParamArmL': 30,
                'ParamArmR': -30,
                'ParamHandL': 20,
                'ParamHandR': -20
            },
            
            description: '雙手在胸前合十拍掌，開心地笑，頭部微側',
            usage_scenarios: ['success', 'approval', 'applause_response'],
            priority: 5
        },
        
        'nodding': {
            id: 'nodding',
            name: '點頭',
            name_en: 'Nodding',
            grid_position: { row: 1, col: 1 },
            crop: { x: 480, y: 540, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': 0,
                'ParamAngleZ': 0,
                'ParamBodyAngleX': 0,
                'ParamBodyAngleY': 0,
                'ParamBodyAngleZ': 0
            },
            
            hand_params: {
                'ParamArmL': 10,
                'ParamArmR': -10,
                'ParamHandL': 15,
                'ParamHandR': 15
            },
            
            description: '雙手在腹部交叉握住，溫和同意的微笑，點頭姿態',
            usage_scenarios: ['agreement', 'acknowledgment', 'active_listening'],
            priority: 6
        },
        
        'shaking': {
            id: 'shaking',
            name: '搖晃',
            name_en: 'Shaking',
            grid_position: { row: 1, col: 2 },
            crop: { x: 960, y: 540, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 0,
                'ParamAngleY': -8,
                'ParamAngleZ': -3,
                'ParamBodyAngleX': -3,
                'ParamBodyAngleY': 5,
                'ParamBodyAngleZ': -5
            },
            
            hand_params: {
                'ParamArmL': 25,
                'ParamArmR': -25,
                'ParamHandL': 0,
                'ParamHandR': 0
            },
            
            description: '雙臂交叉胸前，稍微後仰，有點淘氣的表情',
            usage_scenarios: ['denial', 'playful_rejection', 'teasing'],
            priority: 7
        },
        
        'dancing_2': {
            id: 'dancing_2',
            name: '舞蹈2',
            name_en: 'Dancing 2',
            grid_position: { row: 1, col: 3 },
            crop: { x: 1440, y: 540, width: 480, height: 540 },
            
            live2d_angles: {
                'ParamAngleX': 5,
                'ParamAngleY': 15,
                'ParamAngleZ': 8,
                'ParamBodyAngleX': 8,
                'ParamBodyAngleY': 10,
                'ParamBodyAngleZ': 5
            },
            
            hand_params: {
                'ParamArmL': 30,
                'ParamArmR': 20,
                'ParamHandL': 5,
                'ParamHandR': 10
            },
            
            description: '動感姿勢，右腿微彎，左腿後伸，自信滿滿',
            usage_scenarios: ['entertainment', 'music_playing', 'high_energy'],
            priority: 8
        }
    },
    
    // 姿態過渡時長配置
    transitions: {
        'to_idle': 500,
        'to_thinking': 400,
        'to_dancing': 300,
        'to_emotional': 350,
        'default': 400
    },
    
    // 4D 矩陣到姿態的映射
    matrix_pose_mapping: {
        // Alpha (喚醒度) + Gamma (愉悅度) 組合
        'high_alpha_high_gamma': ['dancing_1', 'dancing_2', 'clapping'],
        'high_alpha_low_gamma': ['shaking', 'surprised_pose'],
        'low_alpha_high_gamma': ['shy_pose', 'nodding'],
        'low_alpha_low_gamma': ['idle', 'thinking'],
        
        // Beta (好奇心) 影響
        'high_beta': ['thinking', 'greeting'],
        'low_beta': ['idle', 'nodding'],
        
        // Delta (專注度) 影響
        'high_delta': ['thinking', 'nodding'],
        'low_delta': ['idle', 'dancing_1']
    },
    
    // 語音同步配置
    voice_sync: {
        'talking': 'idle',
        'singing': 'dancing_1',
        'listening': 'nodding',
        'thinking_aloud': 'thinking'
    }
};

// 導出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ANGELA_POSES;
}
