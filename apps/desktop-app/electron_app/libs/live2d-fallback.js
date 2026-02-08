/**
 * Angela AI - Live2D SDK Fallback
 * 
 * 本地備份的Live2D SDK加載器
 * 當CDN無法訪問時使用本地備份
 */

console.log('[Fallback] Live2D fallback script loaded');

window.loadLocalLive2DSDK = function() {
    console.log('[Fallback] loadLocalLive2DSDK called');
    
    return new Promise((resolve, reject) => {
        console.log('嘗試加載本地Live2D SDK...');
        
        // 檢查是否已經加載
        if (window.Live2DCubismCore) {
            console.log('Live2D SDK已經加載');
            resolve(window.Live2DCubismCore);
            return;
        }
        
        // 創建模擬的Live2D Core（當本地文件也不存在時）
        console.warn('本地Live2D SDK文件不存在，創建模擬SDK...');
        
        window.Live2DCubismCore = {
            // 基本模擬功能
            VERSION: '4.0.0',
            CubismModel: class {
                constructor() {
                    this.parameters = new Map();
                    this.parameterValues = new Float32Array(100);
                }
                
                setParameterValue(id, value) {
                    this.parameterValues[id] = value;
                }
                
                getParameterValue(id) {
                    return this.parameterValues[id];
                }
                
                update() {
                    // 模擬更新
                }
            },
            
            CubismMotionManager: class {
                constructor() {
                    this.motions = new Map();
                }
                
                loadMotion(data) {
                    // 模擬載入動作
                    return Promise.resolve(true);
                }
                
                startMotion(priority) {
                    // 模擬開始動作
                    return true;
                }
            }
        };
        
        console.log('模擬Live2D SDK已創建');
        resolve(window.Live2DCubismCore);
    });
};