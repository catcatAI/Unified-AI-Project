/**
 * Angela AI Voice Configuration (GSI-4 Level)
 * 語音合成引擎參數配置
 * 
 * Based on Angela AI v6.2.0 Architecture Documentation
 * 整合 4D 狀態矩陣驅動的動態語音參數
 */

const ANGELA_VOICE_CONFIG = {
    // 基礎音色配置
    base_timbre: {
        // 基頻錨點
        base_frequency: {
            neutral: 165,      // 中性模式 (Hz)
            female: 215,       // 女性化偏置 (Hz)
            male: 125,         // 男性化偏置 (Hz)
            current: 165       // 當前設定
        },
        
        // 頻譜特性
        spectrum: {
            // Digital Sheen: 6kHz-10kHz 區間增益
            crystal_clarity: {
                gain_db: 2.5,
                frequency_range: [6000, 10000],
                intensity: 1.2
            },
            
            // 諧波結構穩定性
            harmonic_stability: {
                base_stability: 0.95,
                emotion_modulation: 0.05,  // 4D 矩陣觸發時的抖動幅度
                jitter_factor: 0.02        // 模擬生物真實感的微小抖動
            }
        },
        
        // 呼吸音模擬
        breath_simulation: {
            enabled: true,
            intensity: 0.15,
            sync_with_animation: true  // 與胸部起伏動畫同步
        }
    },
    
    // 4D 矩陣驅動的動態參數
    matrix_modulation: {
        // Alpha (喚醒度) → 語速 + 頻率偏移
        alpha: {
            effect_on_pitch: {
                high唤醒: { offset_percent: 10, description: '音調上揚' },
                neutral: { offset_percent: 0, description: '正常' },
                low唤醒: { offset_percent: -5, description: '音調下降' }
            },
            effect_on_rate: {
                high唤醒: { multiplier: 1.3, description: '語速加快' },
                neutral: { multiplier: 1.0, description: '正常' },
                low唤醒: { multiplier: 0.85, description: '語速放慢' }
            }
        },
        
        // Beta (愉悅度) → 諧波豐富度
        beta: {
            effect_on_warmth: {
                high愉悦: { warmth: 1.5, description: '聲音圓潤溫暖' },
                neutral: { warmth: 1.0, description: '正常' },
                low愉悦: { warmth: 0.6, description: '聲音扁平或尖銳' }
            },
            effect_on_volume: {
                high愉悦: { db: 1.5, description: '音量略微提高' },
                neutral: { db: 0, description: '正常' },
                low愉悦: { db: -2, description: '音量降低' }
            }
        },
        
        // Gamma (支配度) → 聲壓級
        gamma: {
            effect_on_pressure: {
                high支配: { assertiveness: 1.0, description: '語氣堅定，吐字清晰' },
                neutral: { assertiveness: 0.7, description: '正常' },
                low支配: { assertiveness: 0.4, description: '語音輕柔，有氣聲' }
            }
        },
        
        // Delta (專注度) → 韻律波動
        delta: {
            effect_on_prosody: {
                high专注: { stability: 0.9, description: '語調平穩，專注' },
                neutral: { stability: 0.7, description: '正常波動' },
                low专注: { stability: 0.5, description: '語調波動大，放鬆' }
            }
        }
    },
    
    // 表情/情緒到語音參數的映射
    emotion_voice_mapping: {
        'neutral': {
            pitch_offset: 0,
            rate_multiplier: 1.0,
            warmth: 1.0,
            assertiveness: 0.7,
            prosody_stability: 0.8
        },
        'happy': {
            pitch_offset: 5,
            rate_multiplier: 1.15,
            warmth: 1.4,
            assertiveness: 0.6,
            prosody_stability: 0.7
        },
        'sad': {
            pitch_offset: -8,
            rate_multiplier: 0.9,
            warmth: 0.5,
            assertiveness: 0.3,
            prosody_stability: 0.6
        },
        'angry': {
            pitch_offset: 8,
            rate_multiplier: 1.2,
            warmth: 0.6,
            assertiveness: 1.0,
            prosody_stability: 0.9
        },
        'surprised': {
            pitch_offset: 12,
            rate_multiplier: 1.25,
            warmth: 0.8,
            assertiveness: 0.7,
            prosody_stability: 0.5
        },
        'shy': {
            pitch_offset: 3,
            rate_multiplier: 0.95,
            warmth: 1.2,
            assertiveness: 0.4,
            prosody_stability: 0.6
        },
        'love': {
            pitch_offset: 5,
            rate_multiplier: 1.0,
            warmth: 1.5,
            assertiveness: 0.5,
            prosody_stability: 0.7
        },
        'thinking': {
            pitch_offset: 2,
            rate_multiplier: 0.85,
            warmth: 1.0,
            assertiveness: 0.7,
            prosody_stability: 0.85
        }
    },
    
    // 姿態到語音的同步配置
    pose_voice_sync: {
        'idle': { mode: 'normal', rate: 1.0 },
        'greeting': { mode: 'warm', rate: 1.1 },
        'thinking': { mode: 'contemplative', rate: 0.9 },
        'dancing': { mode: 'energetic', rate: 1.2 },
        'clapping': { mode: 'cheerful', rate: 1.15 },
        'nodding': { mode: 'agreeable', rate: 1.0 },
        'shaking': { mode: 'playful', rate: 1.0 }
    },
    
    // SSML 生成配置
    ssml_config: {
        default_language: 'zh-TW',
        voice_name: 'Angela-V6-Miara',
        break_time_default: '150ms',
        
        // 標籤映射
        tags: {
            emphasis: {
                'moderate': 'level="moderate"',
                'strong': 'level="strong"',
                'reduced': 'level="reduced"'
            },
            break: {
                'small': 'time="100ms"',
                'medium': 'time="200ms"',
                'large': 'time="400ms"'
            }
        },
        
        // 特殊效果
        effects: {
            'whisper': '<amazon:effect name="whispered"/>',
            'breath': '<amazon:effect name="breath" breath-rate="30%"/>',
            'soft': '<amazon:effect name="soft" />'
        }
    },
    
    // 成熟度縮放 (L0-L11)
    maturity_scaling: {
        L0_L2: {
            style: 'simple_direct',
            vocabulary_complexity: 'low',
            empathy_level: 'basic'
        },
        L3_L4: {
            style: 'empathetic_nuanced',
            vocabulary_complexity: 'medium',
            empathy_level: 'advanced'
        },
        L5_plus: {
            style: 'omni_rational',
            vocabulary_complexity: 'high',
            empathy_level: 'synthetic_wisdom'
        }
    },
    
    // 系統穩定時的隨機探索 (HSM 機制)
    exploration: {
        // EM2 = 0.1 (10% 強制探索)
        em2_factor: 0.1,
        
        // 隨機頻率偏移 (展現非規律靈性)
        random_glitch: {
            enabled: true,
            max_pitch_jitter: 2,      // 音調抖動 %
            max_rate_jitter: 0.05,     // 語速抖動
            trigger_conditions: [
                'high_system_stability',
                'emotional_transition',
                'creative_mode'
            ]
        }
    },
    
    // 性能與精度配置
    performance: {
        // 精度模式 (INT-DEC4 動態調整)
        precision: {
            high_quality: { samples_per_frame: 100, interpolation: 'cubic' },
            medium_quality: { samples_per_frame: 50, interpolation: 'linear' },
            low_quality: { samples_per_frame: 20, interpolation: 'none' }
        },
        
        // CPU 閾值觸發降級
        cpu_threshold: {
            downgrade_at: 5.0,  // CPU 占用超過 5%
            min_precision: 'low_quality'
        }
    }
};

/**
 * 生成 4D 矩陣驅動的語音參數
 * @param {Object} matrix_4d - 4D 矩陣值 {alpha, beta, gamma, delta} (0-1)
 * @param {Object} emotion - 當前情緒 ID
 * @returns {Object} 語音參數
 */
function generateVoiceParams(matrix_4d, emotion) {
    // 1. 獲取基礎情緒參數
    const baseParams = ANGELA_VOICE_CONFIG.emotion_voice_mapping[emotion] || 
                       ANGELA_VOICE_CONFIG.emotion_voice_mapping['neutral'];
    
    // 2. 計算 4D 矩陣調製
    const alphaEffect = ANGELA_VOICE_CONFIG.matrix_modulation.alpha;
    const betaEffect = ANGELA_VOICE_CONFIG.matrix_modulation.beta;
    const gammaEffect = ANGELA_VOICE_CONFIG.matrix_modulation.gamma;
    const deltaEffect = ANGELA_VOICE_CONFIG.matrix_modulation.delta;
    
    // Alpha 調製
    let pitchOffset = baseParams.pitch_offset;
    let rateMultiplier = baseParams.rate_multiplier;
    
    if (matrix_4d.alpha > 0.7) {
        pitchOffset += alphaEffect.effect_on_pitch.high唤醒.offset_percent;
        rateMultiplier *= alphaEffect.effect_on_rate.high唤醒.multiplier;
    } else if (matrix_4d.alpha < 0.3) {
        pitchOffset += alphaEffect.effect_on_pitch.low唤醒.offset_percent;
        rateMultiplier *= alphaEffect.effect_on_rate.low唤醒.multiplier;
    }
    
    // Beta 調製
    let warmth = baseParams.warmth;
    let volume = 0;  // dB
    
    if (matrix_4d.beta > 0.7) {
        warmth *= betaEffect.effect_on_warmth.high愉悦.warmth;
        volume += betaEffect.effect_on_volume.high愉悦.db;
    } else if (matrix_4d.beta < 0.3) {
        warmth *= betaEffect.effect_on_warmth.low愉悦.warmth;
        volume += betaEffect.effect_on_volume.low愉悦.db;
    }
    
    // Gamma 調製
    let assertiveness = baseParams.assertiveness;
    if (matrix_4d.gamma > 0.7) {
        assertiveness = Math.max(assertiveness, gammaEffect.effect_on_pressure.high支配.assertiveness);
    } else if (matrix_4d.gamma < 0.3) {
        assertiveness *= gammaEffect.effect_on_pressure.low支配.assertiveness;
    }
    
    // Delta 調製
    let prosodyStability = baseParams.prosody_stability;
    if (matrix_4d.delta > 0.7) {
        prosodyStability = Math.max(prosodyStability, deltaEffect.effect_on_prosody.high专注.stability);
    }
    
    // 3. 添加隨機探索 (HSM EM2)
    const exploration = ANGELA_VOICE_CONFIG.exploration;
    if (Math.random() < exploration.em2_factor) {
        pitchOffset += (Math.random() * 2 - 1) * exploration.random_glitch.max_pitch_jitter;
        rateMultiplier += (Math.random() * 2 - 1) * exploration.random_glitch.max_rate_jitter;
    }
    
    return {
        pitch: `${pitchOffset.toFixed(1)}%`,
        rate: rateMultiplier.toFixed(2),
        warmth: warmth.toFixed(2),
        volume_db: volume.toFixed(1),
        assertiveness: assertiveness.toFixed(2),
        prosody_stability: prosodyStability.toFixed(2)
    };
}

/**
 * 生成 SSML 標籤
 * @param {string} text - 要合成的文本
 * @param {Object} params - 語音參數
 * @returns {string} SSML 格式的文本
 */
function generateSSML(text, params) {
    const ssml = ANGELA_VOICE_CONFIG.ssml_config;
    
    return `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="${ssml.default_language}">
  <voice name="${ssml.voice_name}">
    <prosody pitch="${params.pitch}" rate="${params.rate}" volume="${params.volume_db}dB">
      ${text}
    </prosody>
  </voice>
</speak>`;
}

// 導出配置和函數
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ANGELA_VOICE_CONFIG,
        generateVoiceParams,
        generateSSML
    };
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.ANGELA_VOICE_CONFIG = ANGELA_VOICE_CONFIG;
    window.generateVoiceParams = generateVoiceParams;
    window.generateSSML = generateSSML;
}
