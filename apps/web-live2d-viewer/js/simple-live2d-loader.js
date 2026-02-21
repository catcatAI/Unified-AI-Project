/**
 * Simple Live2D Model Loader for MVP
 * Loads the Miara Pro model using Cubism SDK
 */

class SimpleLive2DLoader {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.model = null;
        this.app = null;
    }

    async initialize() {
        try {
            console.log('[Live2D] Initializing...');

            // Check if Live2D Cubism SDK is loaded
            if (typeof PIXI === 'undefined') {
                console.warn('[Live2D] PIXI.js not loaded, Live2D disabled');
                return false;
            }

            if (typeof PIXI.live2d === 'undefined') {
                console.warn('[Live2D] Cubism SDK not loaded, Live2D disabled');
                return false;
            }

            // Create PIXI application
            this.app = new PIXI.Application({
                view: this.canvas,
                width: 400,
                height: 600,
                transparent: true,
                autoStart: true
            });

            console.log('[Live2D] PIXI app created');
            return true;
        } catch (error) {
            console.error('[Live2D] Initialization failed:', error);
            return false;
        }
    }

    async loadModel(modelPath) {
        try {
            console.log('[Live2D] Loading model:', modelPath);

            if (!this.app) {
                console.error('[Live2D] App not initialized');
                return false;
            }

            // Load model using Cubism SDK
            this.model = await PIXI.live2d.Live2DModel.from(modelPath);

            if (!this.model) {
                console.error('[Live2D] Failed to load model');
                return false;
            }

            // Scale and position model
            this.model.scale.set(0.15);
            this.model.x = this.app.view.width / 2;
            this.model.y = this.app.view.height / 2;
            this.model.anchor.set(0.5, 0.5);

            // Add to stage
            this.app.stage.addChild(this.model);

            // Enable interaction
            this.model.on('hit', (hitAreas) => {
                console.log('[Live2D] Hit:', hitAreas);
                if (hitAreas.includes('Body')) {
                    this.model.motion('Tap');
                }
            });

            console.log('[Live2D] Model loaded successfully');
            return true;
        } catch (error) {
            console.error('[Live2D] Failed to load model:', error);
            return false;
        }
    }

    setExpression(expressionName) {
        if (this.model && this.model.internalModel) {
            try {
                this.model.expression(expressionName);
            } catch (error) {
                console.warn('[Live2D] Expression not found:', expressionName);
            }
        }
    }

    playMotion(motionGroup, motionIndex = 0) {
        if (this.model) {
            try {
                this.model.motion(motionGroup, motionIndex);
            } catch (error) {
                console.warn('[Live2D] Motion not found:', motionGroup);
            }
        }
    }

    destroy() {
        if (this.model) {
            this.model.destroy();
        }
        if (this.app) {
            this.app.destroy(true);
        }
    }
}

// Export for use in index_mvp.html
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SimpleLive2DLoader;
}
