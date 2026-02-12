#!/usr/bin/env python3
"""
添加触摸去抖机制到UnifiedDisplayMatrix

功能：
- 添加去抖配置（去抖间隔、最后触摸时间跟踪）
- 修改handleTouch方法添加去抖检查
- 在构造函数中初始化去抖属性
- 在destroy方法中清理去抖定时器
"""

import re
import os
import logging
logger = logging.getLogger(__name__)

udm_file = '/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/unified-display-matrix.js'

# 读取文件内容
with open(udm_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在构造函数中添加去抖配置
old_constructor_config = '''        // ============================================================
        // 触摸事件本地队列
        // ============================================================
        this.touchQueue = [];
        this.maxTouchQueueSize = 50;
        this.touchQueueProcessing = false;
        this.touchQueueFlushInterval = null;
        
        // 启动触摸队列自动刷新
        this._startTouchQueueFlush();'''

new_constructor_config = '''        // ============================================================
        // 触摸事件本地队列
        // ============================================================
        this.touchQueue = [];
        this.maxTouchQueueSize = 50;
        this.touchQueueProcessing = false;
        this.touchQueueFlushInterval = null;
        
        // 启动触摸队列自动刷新
        this._startTouchQueueFlush();

        // ============================================================
        // 触摸去抖配置 (防止快速连续触摸)
        // ============================================================
        this.debounceConfig = {
            enabled: true,
            interval: 150,        // 去抖间隔（毫秒）
            lastTouchTime: 0,     // 最后一次触摸时间
            lastTouchType: null,  // 最后一次触摸类型
            debounceTimer: null   // 去抖定时器
        };'''

content = content.replace(old_constructor_config, new_constructor_config)

# 2. 修改handleTouch方法添加去抖检查
old_handletouch_start = '''    handleTouch(screenX, screenY, touchType = 'pat') {
        const result = {
            success: false,
            coordinates: null,
            bodyPart: null,
            hapticIntensity: 0,
            stateUpdate: null,
            expression: null,
            errors: []
        };

        try {'''

new_handletouch_start = '''    handleTouch(screenX, screenY, touchType = 'pat') {
        const result = {
            success: false,
            coordinates: null,
            bodyPart: null,
            hapticIntensity: 0,
            stateUpdate: null,
            expression: null,
            errors: [],
            debounced: false  // 标记是否被去抖
        };

        // 检查去抖配置
        if (this.debounceConfig.enabled) {
            const now = Date.now();
            const timeSinceLastTouch = now - this.debounceConfig.lastTouchTime;
            
            // 如果在去抖间隔内，忽略此次触摸
            if (timeSinceLastTouch < this.debounceConfig.interval) {
                console.log('[UDM] Touch debounced:', touchType, '(last:', timeSinceLastTouch, 'ms ago)');
                result.debounced = true;
                result.errors.push({
                    step: 'debounce',
                    error: 'Touch debounced - too soon after last touch'
                });
                return result;
            }
            
            // 更新最后触摸时间和类型
            this.debounceConfig.lastTouchTime = now;
            this.debounceConfig.lastTouchType = touchType;
        }

        try {'''

content = content.replace(old_handletouch_start, new_handletouch_start)

# 3. 在destroy方法中添加去抖定时器清理
old_destroy = '''    destroy() {
        // 停止触摸队列刷新
        this._stopTouchQueueFlush();
        
        // 清空触摸队列
        this.touchQueue = [];
        
        // 清理引用
        this.canvasElement = null;
        this.angelaSystem = { stateMatrix: null, live2DManager: null, hapticHandler: null };
        this.listeners = { scaleChange: [], precisionChange: [], resize: [], touch: [] };
        this.isInitialized = false;
        console.log('[UDM] Destroyed');
    }'''

new_destroy = '''    destroy() {
        // 停止触摸队列刷新
        this._stopTouchQueueFlush();
        
        // 清理去抖定时器
        if (this.debounceConfig.debounceTimer) {
            clearTimeout(this.debounceConfig.debounceTimer);
            this.debounceConfig.debounceTimer = null;
        }
        
        // 清空触摸队列
        this.touchQueue = [];
        
        // 清理引用
        this.canvasElement = null;
        this.angelaSystem = { stateMatrix: null, live2DManager: null, hapticHandler: null };
        this.listeners = { scaleChange: [], precisionChange: [], resize: [], touch: [] };
        this.isInitialized = false;
        console.log('[UDM] Destroyed');
    }'''

content = content.replace(old_destroy, new_destroy)

# 4. 添加配置去抖间隔的方法
# 在setUserScale方法之后添加
old_setusermethod = '''    resetUserScale() {
        setUserScale(this.baseConfig.defaultUserScale);
    }'''

new_setusermethod = '''    resetUserScale() {
        this.setUserScale(this.baseConfig.defaultUserScale);
    }

    // ================================================================
    // 触摸去抖控制
    // ================================================================

    /**
     * 设置去抖间隔
     * @param {number} interval - 去抖间隔（毫秒），0表示禁用去抖
     */
    setDebounceInterval(interval) {
        if (interval <= 0) {
            this.debounceConfig.enabled = false;
            console.log('[UDM] 去抖已禁用');
        } else {
            this.debounceConfig.interval = interval;
            this.debounceConfig.enabled = true;
            console.log('[UDM] 去抖间隔设置为:', interval, 'ms');
        }
    }

    /**
     * 启用/禁用触摸去抖
     * @param {boolean} enabled - 是否启用
     */
    setDebounceEnabled(enabled) {
        this.debounceConfig.enabled = enabled;
        console.log('[UDM] 去抖', enabled ? '已启用' : '已禁用');
    }

    /**
     * 获取去抖状态
     * @returns {object} 去抖状态
     */
    getDebounceStatus() {
        return {
            enabled: this.debounceConfig.enabled,
            interval: this.debounceConfig.interval,
            lastTouchTime: this.debounceConfig.lastTouchTime,
            timeSinceLastTouch: this.debounceConfig.lastTouchTime > 0 ? 
                Date.now() - this.debounceConfig.lastTouchTime : 0
        };
    }'''

content = content.replace(old_setusermethod, new_setusermethod)

# 写入文件
with open(udm_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 触摸去抖机制添加完成")
print("修改内容：")
print("1. 在构造函数中添加了去抖配置（间隔150ms）")
print("2. 在handleTouch方法中添加了去抖检查")
print("3. 在destroy方法中添加了去抖定时器清理")
print("4. 添加了setDebounceInterval、setDebounceEnabled、getDebounceStatus方法")