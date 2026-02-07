class I18nManager {
    constructor(config = {}) {
        this.config = {
            defaultLocale: config.defaultLocale || 'en',
            fallbackLocale: config.fallbackLocale || 'en',
            availableLocales: config.availableLocales || ['en', 'zh-CN', 'zh-TW', 'ja', 'ko'],
            autoDetect: config.autoDetect !== false
        };
        
        this.translations = {};
        this.currentLocale = this.config.defaultLocale;
        this.changeCallbacks = [];
        
        this._init();
    }
    
    _init() {
        this._loadDefaultTranslations();
        
        if (this.config.autoDetect) {
            const detectedLocale = this._detectLocale();
            if (detectedLocale) {
                this.setLocale(detectedLocale);
            }
        }
    }
    
    _detectLocale() {
        const browserLocale = navigator.language || navigator.userLanguage;
        const normalizedLocale = this._normalizeLocale(browserLocale);
        
        if (this.config.availableLocales.includes(normalizedLocale)) {
            return normalizedLocale;
        }
        
        const localePart = browserLocale.split('-')[0];
        const matchedLocale = this.config.availableLocales.find(
            locale => locale.startsWith(localePart)
        );
        
        return matchedLocale || null;
    }
    
    _normalizeLocale(locale) {
        return locale.replace('_', '-');
    }
    
    _loadDefaultTranslations() {
        this.registerTranslations('en', {
            app: {
                name: 'Angela AI',
                loading: 'Loading Angela AI...',
                ready: 'Angela AI is ready!',
                error: 'An error occurred'
            },
            ui: {
                settings: 'Settings',
                minimize: 'Minimize',
                close: 'Close',
                save: 'Save',
                cancel: 'Cancel',
                apply: 'Apply',
                reset: 'Reset'
            },
            interaction: {
                click: 'Clicked on {part}',
                drag: 'Dragging {part}',
                hover: 'Hovering over {part}',
                touch: 'Touched {part}'
            },
            expression: {
                happy: 'Happy',
                sad: 'Sad',
                angry: 'Angry',
                surprised: 'Surprised',
                shy: 'Shy',
                love: 'Love',
                neutral: 'Neutral'
            },
            action: {
                idle: 'Idle',
                greeting: 'Greeting',
                thinking: 'Thinking',
                dancing: 'Dancing',
                waving: 'Waving',
                clapping: 'Clapping'
            },
            system: {
                connected: 'Connected to backend',
                disconnected: 'Disconnected from backend',
                connecting: 'Connecting...',
                reconnecting: 'Reconnecting...',
                connection_failed: 'Connection failed',
                level_up: 'Level Up! L{from} → L{to} ({name})'
            }
        });
        
        this.registerTranslations('zh-CN', {
            app: {
                name: 'Angela AI',
                loading: '正在加载 Angela AI...',
                ready: 'Angela AI 已就绪！',
                error: '发生错误'
            },
            ui: {
                settings: '设置',
                minimize: '最小化',
                close: '关闭',
                save: '保存',
                cancel: '取消',
                apply: '应用',
                reset: '重置'
            },
            interaction: {
                click: '点击了 {part}',
                drag: '拖动 {part}',
                hover: '悬停在 {part} 上',
                touch: '触摸了 {part}'
            },
            expression: {
                happy: '开心',
                sad: '难过',
                angry: '生气',
                surprised: '惊讶',
                shy: '害羞',
                love: '爱',
                neutral: '平静'
            },
            action: {
                idle: '待机',
                greeting: '问候',
                thinking: '思考',
                dancing: '跳舞',
                waving: '挥手',
                clapping: '鼓掌'
            },
            system: {
                connected: '已连接到后端',
                disconnected: '已从后端断开',
                connecting: '连接中...',
                reconnecting: '重新连接中...',
                connection_failed: '连接失败',
                level_up: '升级！L{from} → L{to} ({name})'
            }
        });
        
        this.registerTranslations('ja', {
            app: {
                name: 'Angela AI',
                loading: 'Angela AIを読み込み中...',
                ready: 'Angela AIの準備が完了しました！',
                error: 'エラーが発生しました'
            },
            ui: {
                settings: '設定',
                minimize: '最小化',
                close: '閉じる',
                save: '保存',
                cancel: 'キャンセル',
                apply: '適用',
                reset: 'リセット'
            },
            interaction: {
                click: '{part}をクリック',
                drag: '{part}をドラッグ',
                hover: '{part}にホバー',
                touch: '{part}をタッチ'
            },
            expression: {
                happy: 'ハッピー',
                sad: 'サッド',
                angry: 'アングリー',
                surprised: 'サプライズ',
                shy: 'シャイ',
                love: 'ラブ',
                neutral: 'ニュートラル'
            },
            action: {
                idle: 'アイドル',
                greeting: '挨拶',
                thinking: '思考',
                dancing: 'ダンス',
                waving: '手振り',
                clapping: '拍手'
            },
            system: {
                connected: 'バックエンドに接続しました',
                disconnected: 'バックエンドから切断しました',
                connecting: '接続中...',
                reconnecting: '再接続中...',
                connection_failed: '接続に失敗しました',
                level_up: 'レベルアップ！L{from} → L{to} ({name})'
            }
        });
        
        this.registerTranslations('ko', {
            app: {
                name: 'Angela AI',
                loading: 'Angela AI 로드 중...',
                ready: 'Angela AI가 준비되었습니다!',
                error: '오류가 발생했습니다'
            },
            ui: {
                settings: '설정',
                minimize: '최소화',
                close: '닫기',
                save: '저장',
                cancel: '취소',
                apply: '적용',
                reset: '재설정'
            },
            interaction: {
                click: '{part} 클릭',
                drag: '{part} 드래그',
                hover: '{part} 위에 마우스',
                touch: '{part} 터치'
            },
            expression: {
                happy: '행복',
                sad: '슬픔',
                angry: '화남',
                surprised: '놀람',
                shy: '수줍음',
                love: '사랑',
                neutral: '중립'
            },
            action: {
                idle: '대기',
                greeting: '인사',
                thinking: '생각',
                dancing: '춤',
                waving: '손 흔들기',
                clapping: '박수'
            },
            system: {
                connected: '백엔드에 연결됨',
                disconnected: '백엔드에서 연결 끊김',
                connecting: '연결 중...',
                reconnecting: '재연결 중...',
                connection_failed: '연결 실패',
                level_up: '레벨 업! L{from} → L{to} ({name})'
            }
        });

        this.registerTranslations('zh-TW', {
            app: {
                name: 'Angela AI',
                loading: '正在載入 Angela AI...',
                ready: 'Angela AI 已就緒！',
                error: '發生錯誤'
            },
            ui: {
                settings: '設定',
                minimize: '最小化',
                close: '關閉',
                save: '儲存',
                cancel: '取消',
                apply: '套用',
                reset: '重設'
            },
            interaction: {
                click: '點擊了 {part}',
                drag: '拖拽 {part}',
                hover: '懸停在 {part} 上',
                touch: '觸摸了 {part}'
            },
            expression: {
                happy: '開心',
                sad: '難過',
                angry: '生氣',
                surprised: '驚訝',
                shy: '害羞',
                love: '愛',
                neutral: '平靜'
            },
            action: {
                idle: '待機',
                greeting: '問候',
                thinking: '思考',
                dancing: '跳舞',
                waving: '揮手',
                clapping: '鼓掌'
            },
            system: {
                connected: '已連線到後端',
                disconnected: '已從後端斷開',
                connecting: '連線中...',
                reconnecting: '重新連線中...',
                connection_failed: '連線失敗',
                level_up: '升級！L{from} → L{to} ({name})'
            }
        });
    }
    
    registerTranslations(locale, translations) {
        const normalizedLocale = this._normalizeLocale(locale);
        this.translations[normalizedLocale] = {
            ...this.translations[normalizedLocale],
            ...translations
        };
    }
    
    getLocale() {
        return this.currentLocale;
    }
    
    setLocale(locale) {
        const normalizedLocale = this._normalizeLocale(locale);
        
        if (this.config.availableLocales.includes(normalizedLocale)) {
            this.currentLocale = normalizedLocale;
            this._notifyChange();
            return true;
        }
        
        console.warn(`Locale ${locale} is not available`);
        return false;
    }
    
    t(key, params = {}) {
        return this.translate(key, params);
    }
    
    translate(key, params = {}) {
        const value = this._getTranslationValue(key);
        
        if (value === null) {
            console.warn(`Translation key not found: ${key}`);
            return key;
        }
        
        if (typeof value === 'string' && Object.keys(params).length > 0) {
            return this._interpolate(value, params);
        }
        
        return value;
    }
    
    _getTranslationValue(key) {
        const keys = key.split('.');
        let value = this.translations[this.currentLocale];
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                value = null;
                break;
            }
        }
        
        if (value === null && this.currentLocale !== this.config.fallbackLocale) {
            value = this.translations[this.config.fallbackLocale];
            
            for (const k of keys) {
                if (value && typeof value === 'object' && k in value) {
                    value = value[k];
                } else {
                    value = null;
                    break;
                }
            }
        }
        
        return value;
    }
    
    _interpolate(template, params) {
        return template.replace(/\{(\w+)\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }
    
    getAvailableLocales() {
        return [...this.config.availableLocales];
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
    
    _notifyChange() {
        this.changeCallbacks.forEach(callback => {
            try {
                callback(this.currentLocale);
            } catch (e) {
                console.error('I18n change callback error:', e);
            }
        });
    }
    
    formatNumber(number, options = {}) {
        return new Intl.NumberFormat(this.currentLocale, options).format(number);
    }
    
    formatDate(date, options = {}) {
        return new Intl.DateTimeFormat(this.currentLocale, options).format(date);
    }
    
    formatTime(date, options = {}) {
        return new Intl.DateTimeFormat(this.currentLocale, {
            hour: '2-digit',
            minute: '2-digit',
            ...options
        }).format(date);
    }
    
    formatDateTime(date, options = {}) {
        return new Intl.DateTimeFormat(this.currentLocale, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            ...options
        }).format(date);
    }
    
    formatRelativeTime(date, options = {}) {
        const formatter = new Intl.RelativeTimeFormat(this.currentLocale, options);
        const now = new Date();
        const diff = (date.getTime() - now.getTime()) / 1000;
        
        const units = [
            { unit: 'year', seconds: 31536000 },
            { unit: 'month', seconds: 2592000 },
            { unit: 'day', seconds: 86400 },
            { unit: 'hour', seconds: 3600 },
            { unit: 'minute', seconds: 60 },
            { unit: 'second', seconds: 1 }
        ];
        
        for (const { unit, seconds } of units) {
            const value = Math.round(diff / seconds);
            if (Math.abs(value) >= 1 || unit === 'second') {
                return formatter.format(value, unit);
            }
        }
    }
    
    formatCurrency(amount, currency = 'USD', options = {}) {
        return new Intl.NumberFormat(this.currentLocale, {
            style: 'currency',
            currency,
            ...options
        }).format(amount);
    }
    
    exportTranslations(locale = null) {
        if (locale) {
            return this.translations[locale] || {};
        }
        return { ...this.translations };
    }
    
    importTranslations(translations) {
        Object.keys(translations).forEach(locale => {
            this.registerTranslations(locale, translations[locale]);
        });
    }
}

const i18n = new I18nManager();