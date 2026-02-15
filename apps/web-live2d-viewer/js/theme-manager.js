class ThemeManager {
    constructor(config = {}) {
        this.config = {
            defaultTheme: config.defaultTheme || 'light',
            autoDetect: config.autoDetect !== false,
            storageKey: config.storageKey || 'angela_theme',
            transitionDuration: config.transitionDuration || '300ms'
        };
        
        this.themes = {};
        this.currentTheme = this.config.defaultTheme;
        this.transitionEnabled = true;
        this.changeCallbacks = [];
        
        this._init();
    }
    
    _init() {
        this._loadDefaultThemes();
        
        if (this.config.autoDetect) {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.setTheme(prefersDark ? 'dark' : 'light', false);
        }
        
        const savedTheme = localStorage.getItem(this.config.storageKey);
        if (savedTheme && this.themes[savedTheme]) {
            this.setTheme(savedTheme, false);
        }
        
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (this.config.autoDetect) {
                this.setTheme(e.matches ? 'dark' : 'light', false);
            }
        });
        
        this._applyThemeVariables();
    }
    
    _loadDefaultThemes() {
        this.registerTheme('light', {
            name: 'Light',
            colors: {
                primary: '#4A90E2',
                secondary: '#50E3C2',
                background: '#FFFFFF',
                surface: '#F5F5F5',
                text: '#333333',
                textSecondary: '#666666',
                border: '#E0E0E0',
                shadow: 'rgba(0, 0, 0, 0.1)',
                error: '#FF5252',
                warning: '#FFB74D',
                success: '#4CAF50',
                info: '#2196F3'
            },
            typography: {
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: {
                    xs: '12px',
                    sm: '14px',
                    md: '16px',
                    lg: '18px',
                    xl: '24px'
                },
                fontWeight: {
                    normal: 400,
                    medium: 500,
                    bold: 700
                }
            },
            spacing: {
                xs: '4px',
                sm: '8px',
                md: '16px',
                lg: '24px',
                xl: '32px'
            },
            borderRadius: {
                sm: '4px',
                md: '8px',
                lg: '12px',
                xl: '16px'
            },
            shadows: {
                sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
                md: '0 4px 6px rgba(0, 0, 0, 0.1)',
                lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
                xl: '0 20px 25px rgba(0, 0, 0, 0.15)'
            }
        });
        
        this.registerTheme('dark', {
            name: 'Dark',
            colors: {
                primary: '#64B5F6',
                secondary: '#4DB6AC',
                background: '#121212',
                surface: '#1E1E1E',
                text: '#FFFFFF',
                textSecondary: '#B0B0B0',
                border: '#333333',
                shadow: 'rgba(0, 0, 0, 0.3)',
                error: '#FF8A80',
                warning: '#FFB74D',
                success: '#81C784',
                info: '#64B5F6'
            },
            typography: {
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: {
                    xs: '12px',
                    sm: '14px',
                    md: '16px',
                    lg: '18px',
                    xl: '24px'
                },
                fontWeight: {
                    normal: 400,
                    medium: 500,
                    bold: 700
                }
            },
            spacing: {
                xs: '4px',
                sm: '8px',
                md: '16px',
                lg: '24px',
                xl: '32px'
            },
            borderRadius: {
                sm: '4px',
                md: '8px',
                lg: '12px',
                xl: '16px'
            },
            shadows: {
                sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
                md: '0 4px 6px rgba(0, 0, 0, 0.4)',
                lg: '0 10px 15px rgba(0, 0, 0, 0.5)',
                xl: '0 20px 25px rgba(0, 0, 0, 0.6)'
            }
        });
        
        this.registerTheme('angela', {
            name: 'Angela',
            colors: {
                primary: '#FF6B9D',
                secondary: '#C44DFF',
                background: '#FFF0F5',
                surface: '#FFE4EC',
                text: '#4A235A',
                textSecondary: '#8E44AD',
                border: '#FFB6D9',
                shadow: 'rgba(255, 107, 157, 0.2)',
                error: '#FF6B6B',
                warning: '#FFD93D',
                success: '#6BCB77',
                info: '#4D96FF'
            },
            typography: {
                fontFamily: '"Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif',
                fontSize: {
                    xs: '12px',
                    sm: '14px',
                    md: '16px',
                    lg: '18px',
                    xl: '24px'
                },
                fontWeight: {
                    normal: 400,
                    medium: 500,
                    bold: 600
                }
            },
            spacing: {
                xs: '4px',
                sm: '8px',
                md: '16px',
                lg: '24px',
                xl: '32px'
            },
            borderRadius: {
                sm: '6px',
                md: '12px',
                lg: '18px',
                xl: '24px'
            },
            shadows: {
                sm: '0 2px 4px rgba(255, 107, 157, 0.15)',
                md: '0 4px 8px rgba(255, 107, 157, 0.2)',
                lg: '0 8px 16px rgba(255, 107, 157, 0.25)',
                xl: '0 16px 32px rgba(255, 107, 157, 0.3)'
            }
        });
    }
    
    registerTheme(id, theme) {
        this.themes[id] = theme;
    }
    
    getTheme() {
        return this.currentTheme;
    }
    
    setTheme(themeId, save = true) {
        if (!this.themes[themeId]) {
            console.warn(`Theme ${themeId} not found`);
            return false;
        }
        
        const oldTheme = this.currentTheme;
        this.currentTheme = themeId;
        
        this._applyThemeVariables();
        this._notifyChange(themeId, oldTheme);
        
        if (save) {
            localStorage.setItem(this.config.storageKey, themeId);
        }
        
        return true;
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        return this.setTheme(newTheme);
    }
    
    getAvailableThemes() {
        return Object.keys(this.themes).map(id => ({
            id,
            name: this.themes[id].name
        }));
    }
    
    getThemeValue(path) {
        const theme = this.themes[this.currentTheme];
        const keys = path.split('.');
        let value = theme;
        
        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                return null;
            }
        }
        
        return value;
    }
    
    getColor(colorName) {
        return this.getThemeValue(`colors.${colorName}`);
    }
    
    getTypography(path = '') {
        const typography = this.getThemeValue('typography');
        if (!path) return typography;
        return this.getThemeValue(`typography.${path}`);
    }
    
    getSpacing(size = 'md') {
        return this.getThemeValue(`spacing.${size}`);
    }
    
    getBorderRadius(size = 'md') {
        return this.getThemeValue(`borderRadius.${size}`);
    }
    
    getShadow(size = 'md') {
        return this.getThemeValue(`shadows.${size}`);
    }
    
    _applyThemeVariables() {
        const theme = this.themes[this.currentTheme];
        const root = document.documentElement;
        
        if (this.transitionEnabled) {
            root.style.setProperty('--transition-duration', this.config.transitionDuration);
        }
        
        this._applyColorVariables(theme.colors, root);
        this._applyTypographyVariables(theme.typography, root);
        this._applySpacingVariables(theme.spacing, root);
        this._applyBorderRadiusVariables(theme.borderRadius, root);
        this._applyShadowVariables(theme.shadows, root);
    }
    
    _applyColorVariables(colors, root) {
        Object.entries(colors).forEach(([key, value]) => {
            root.style.setProperty(`--color-${key}`, value);
        });
    }
    
    _applyTypographyVariables(typography, root) {
        if (typography.fontFamily) {
            root.style.setProperty('--font-family', typography.fontFamily);
        }
        
        Object.entries(typography.fontSize || {}).forEach(([key, value]) => {
            root.style.setProperty(`--font-size-${key}`, value);
        });
        
        Object.entries(typography.fontWeight || {}).forEach(([key, value]) => {
            root.style.setProperty(`--font-weight-${key}`, value);
        });
    }
    
    _applySpacingVariables(spacing, root) {
        Object.entries(spacing).forEach(([key, value]) => {
            root.style.setProperty(`--spacing-${key}`, value);
        });
    }
    
    _applyBorderRadiusVariables(borderRadius, root) {
        Object.entries(borderRadius).forEach(([key, value]) => {
            root.style.setProperty(`--border-radius-${key}`, value);
        });
    }
    
    _applyShadowVariables(shadows, root) {
        Object.entries(shadows).forEach(([key, value]) => {
            root.style.setProperty(`--shadow-${key}`, value);
        });
    }
    
    enableTransition() {
        this.transitionEnabled = true;
        document.documentElement.style.setProperty('--transition-duration', this.config.transitionDuration);
    }
    
    disableTransition() {
        this.transitionEnabled = false;
        document.documentElement.style.setProperty('--transition-duration', '0ms');
    }
    
    onChange(callback) {
        this.changeCallbacks.push(callback);
    }
    
    offChange(callback) {
        const index = this.changeCallbacks.indexOf(callback);
        if (index > -1) {
            this.changeCallbacks.splice(index, 1);
        }
    }
    
    _notifyChange(newTheme, oldTheme) {
        this.changeCallbacks.forEach(callback => {
            try {
                callback(newTheme, oldTheme);
            } catch (e) {
                console.error('Theme change callback error:', e);
            }
        });
    }
    
    getCurrentTheme() {
        return this.themes[this.currentTheme];
    }
    
    exportTheme(themeId = null) {
        if (themeId) {
            return this.themes[themeId] || null;
        }
        return { ...this.themes };
    }
    
    importTheme(themeId, theme) {
        this.registerTheme(themeId, theme);
        return true;
    }
}

window.ThemeManager = ThemeManager;
window.theme = new ThemeManager();