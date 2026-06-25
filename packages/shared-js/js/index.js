/**
 * @angela/shared-js
 * 
 * Shared JavaScript modules for Angela AI.
 * Used by both desktop-app (Electron) and web-live2d-viewer.
 * 
 * Load individual modules via <script> tag in the correct dependency order.
 * This file serves as a package entry point for potential future bundling.
 * 
 * @version 7.5.0-dev
 */

console.log('[shared-js] @angela/shared-js loaded');

// Platform detection helper for shared modules
window.AngelaPlatform = {
    isElectron: typeof window.electronAPI !== 'undefined' && 
                typeof window.electronAPI.window !== 'undefined',
    isWeb: typeof window.electronAPI === 'undefined' ||
           window.electronAPI?.platform === 'web',
    getImageRoot: function() {
        return this.isElectron ? 'local://' : '';
    }
};
