/**
 * Angela AI - 系统托盘管理器
 * 
 * 提供系统托盘图标和右键菜单功能
 */

class TrayManager {
    constructor() {
        this.tray = null;
        this.menuItems = [];
        this.callbacks = {};
        this.isLinux = process.platform === 'linux';
        
        console.log('[TrayManager] Initialized');
    }
    
    /**
     * 初始化系统托盘
     * @param {string} iconPath - 图标路径
     * @param {string} tooltip - 提示文本
     */
    initialize(iconPath, tooltip = 'Angela AI') {
        try {
            const { Tray } = require('electron');
            
            // 创建托盘图标
            this.tray = new Tray(iconPath);
            this.tray.setToolTip(tooltip);
            
            // 设置初始菜单
            this._createDefaultMenu();
            
            console.log('[TrayManager] System tray initialized');
            return true;
        } catch (error) {
            console.error('[TrayManager] Failed to initialize tray:', error);
            return false;
        }
    }
    
    /**
     * 创建默认菜单
     */
    _createDefaultMenu() {
        const menuItems = [
            { id: 'show', label: '显示窗口', click: () => this._onShowWindow() },
            { id: 'hide', label: '隐藏窗口', click: () => this._onHideWindow() },
            { type: 'separator' },
            { id: 'settings', label: '设置', click: () => this._onSettings() },
            { id: 'about', label: '关于', click: () => this._onAbout() },
            { type: 'separator' },
            { id: 'start', label: '启动Angela', click: () => this._onStart() },
            { id: 'stop', label: '停止Angela', click: () => this._onStop() },
            { type: 'separator' },
            { id: 'restart', label: '重启', click: () => this._onRestart() },
            { type: 'separator' },
            { id: 'quit', label: '退出', click: () => this._onQuit() }
        ];
        
        this.updateMenu(menuItems);
    }
    
    /**
     * 更新托盘菜单
     * @param {Array} items - 菜单项数组
     */
    updateMenu(items) {
        try {
            const { Menu } = require('electron');
            
            // 构建Electron菜单模板
            const template = items.map(item => {
                if (item.type === 'separator') {
                    return { type: 'separator' };
                }
                
                return {
                    id: item.id,
                    label: item.label,
                    type: 'normal',
                    click: () => this._handleItemClick(item)
                };
            });
            
            // 创建菜单
            const menu = Menu.buildFromTemplate(template);
            this.tray.setContextMenu(menu);
            
            this.menuItems = items;
            
            console.log('[TrayManager] Menu updated:', items.length, 'items');
        } catch (error) {
            console.error('[TrayManager] Failed to update menu:', error);
        }
    }
    
    /**
     * 处理菜单项点击
     * @param {Object} item - 菜单项
     */
    _handleItemClick(item) {
        console.log('[TrayManager] Menu item clicked:', item.id);
        
        // 调用回调
        if (this.callbacks[item.id]) {
            this.callbacks[item.id]();
        }
        
        // 调用通用回调
        if (this.callbacks['itemClick']) {
            this.callbacks['itemClick'](item);
        }
    }
    
    /**
     * 注册菜单项回调
     * @param {string} itemId - 菜单项ID
     * @param {Function} callback - 回调函数
     */
    on(itemId, callback) {
        this.callbacks[itemId] = callback;
    }
    
    /**
     * 设置托盘图标
     * @param {string} iconPath - 图标路径
     */
    setIcon(iconPath) {
        try {
            this.tray.setImage(iconPath);
            console.log('[TrayManager] Icon updated:', iconPath);
        } catch (error) {
            console.error('[TrayManager] Failed to set icon:', error);
        }
    }
    
    /**
     * 设置提示文本
     * @param {string} tooltip - 提示文本
     */
    setTooltip(tooltip) {
        try {
            this.tray.setToolTip(tooltip);
            console.log('[TrayManager] Tooltip updated:', tooltip);
        } catch (error) {
            console.error('[TrayManager] Failed to set tooltip:', error);
        }
    }
    
    /**
     * 显示通知气泡
     * @param {Object} options - 通知选项
     */
    displayBalloon(options) {
        try {
            // Electron的Tray.displayBalloon在某些平台可能不支持
            if (this.tray.displayBalloon) {
                this.tray.displayBalloon({
                    iconType: options.iconType || 'info',
                    title: options.title || '',
                    content: options.content || ''
                });
            } else {
                console.log('[TrayManager] Balloon notification:', options.title, options.content);
            }
        } catch (error) {
            console.error('[TrayManager] Failed to display balloon:', error);
        }
    }
    
    /**
     * 闪烁托盘图标
     * @param {boolean} flash - 是否闪烁
     */
    setFlash(flash) {
        try {
            // Linux平台可能不支持闪烁
            if (this.tray.setFlashFrame) {
                this.tray.setFlashFrame(flash);
            }
        } catch (error) {
            console.error('[TrayManager] Failed to set flash:', error);
        }
    }
    
    /**
     * 销毁托盘
     */
    destroy() {
        try {
            if (this.tray) {
                this.tray.destroy();
                this.tray = null;
                console.log('[TrayManager] Tray destroyed');
            }
        } catch (error) {
            console.error('[TrayManager] Failed to destroy tray:', error);
        }
    }
    
    // 默认事件处理器
    _onShowWindow() {
        console.log('[TrayManager] Show window');
        if (this.callbacks['showWindow']) {
            this.callbacks['showWindow']();
        }
    }
    
    _onHideWindow() {
        console.log('[TrayManager] Hide window');
        if (this.callbacks['hideWindow']) {
            this.callbacks['hideWindow']();
        }
    }
    
    _onSettings() {
        console.log('[TrayManager] Settings');
        if (this.callbacks['settings']) {
            this.callbacks['settings']();
        }
    }
    
    _onAbout() {
        console.log('[TrayManager] About');
        if (this.callbacks['about']) {
            this.callbacks['about']();
        }
    }
    
    _onStart() {
        console.log('[TrayManager] Start Angela');
        if (this.callbacks['start']) {
            this.callbacks['start']();
        }
    }
    
    _onStop() {
        console.log('[TrayManager] Stop Angela');
        if (this.callbacks['stop']) {
            this.callbacks['stop']();
        }
    }
    
    _onRestart() {
        console.log('[TrayManager] Restart');
        if (this.callbacks['restart']) {
            this.callbacks['restart']();
        }
    }
    
    _onQuit() {
        console.log('[TrayManager] Quit');
        if (this.callbacks['quit']) {
            this.callbacks['quit']();
        }
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TrayManager;
}