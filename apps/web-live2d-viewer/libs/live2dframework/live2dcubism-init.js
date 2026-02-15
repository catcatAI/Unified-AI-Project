/**
 * Live2D Cubism SDK 5 Wrapper
 * Provides proper initialization helpers for the bundled Framework
 * NOTE: Manual initialization via window.initLive2DFramework() is recommended
 */

(function() {
    'use strict';

    // Manual initialization function - call this after Core SDK is loaded
    window.initLive2DFramework = function() {
        if (typeof window.Live2DCubismFramework === 'undefined') {
            console.log('[FrameworkInit] Framework not yet loaded');
            return false;
        }

        if (typeof window.Live2DCubismFramework.CubismFramework === 'undefined') {
            console.log('[FrameworkInit] CubismFramework not found in bundle');
            return false;
        }

        var CubismFramework = window.Live2DCubismFramework.CubismFramework;

        // Start up Framework
        if (typeof CubismFramework.startUp === 'function') {
            CubismFramework.startUp();
            console.log('[FrameworkInit] Framework started up');
        }

        // Initialize Framework
        if (typeof CubismFramework.initialize === 'function') {
            // Initialize with default memory
            CubismFramework.initialize(16 * 1024 * 1024); // 16MB
            console.log('[FrameworkInit] Framework initialized');
        }

        // Mark as initialized
        window.Live2DCubismFramework.initialized = true;

        return true;
    };

    console.log('[FrameworkInit] Wrapper loaded, call window.initLive2DFramework() to initialize');
})();