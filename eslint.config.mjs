import globals from 'globals'

export default [
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/.next/**',
      '**/venv/**',
      '**/.venv/**',
      '**/.pytest_cache/**',
      '**/__pycache__/**',
      '**/*.min.js',
      '**/*.bundle.js',
      '**/extracted-content.js',
      '**/coverage/**',
      '**/.cache/**',
      '**/temp/**',
      '**/temp_miara_extract/**',
      // 第三方 SDK（Live2D 官方 Cubism Core，minified 授權檔）：
      // 內部 read/FS/define 等 emscripten 風格自由變數非本倉程式，不 lint
      '**/live2dcubismcore.js',
      '**/CubismSdkForWeb*/**',
    ],
  },
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        // script-tag 命名空間（2026-10-14 定義稽核：全部在倉內有定義檔，
        // 由各 index.html 以 <script> 順序載入；no-undef 繼續抓真正
        // 未宣告的識別字 — 例如當日修掉的 add-world-content insertBefore）
        ANGELA_CHARACTER_CONFIG: 'readonly',
        AngelaAPIClient: 'readonly',
        AudioHandler: 'readonly',
        AvailabilityManager: 'readonly',
        BackendWebSocketClient: 'readonly',
        CARDS: 'readonly',
        DriverDetector: 'readonly',
        HapticHandler: 'readonly',
        HardwareDetector: 'readonly',
        InputHandler: 'readonly',
        Live2DCubismWrapper: 'readonly',
        Live2DManager: 'readonly',
        Logger: 'readonly',
        MaturityTracker: 'readonly',
        MultimodalAPIClient: 'readonly',
        NPC_SCHEDULES: 'readonly',
        PerformanceManager: 'readonly',
        PluginManager: 'readonly',
        PrecisionManager: 'readonly',
        StateMatrix4D: 'readonly',
        StatePersistence: 'readonly',
        UnifiedDisplayMatrix: 'readonly',
        WORLD_LINES: 'readonly',
        WallpaperHandler: 'readonly',
        i18n: 'readonly',
        performanceMonitor: 'readonly',
        settingsManager: 'readonly',
        systemProfile: 'readonly',
        theme: 'readonly',
        userManager: 'readonly',
      },
    },
    rules: {
      // General JavaScript rules
      'prefer-const': 'warn',
      'no-unused-vars': [
        'warn',
        {
          // 未用參數改名 _ 前綴即消音（呼叫端不綁參名，零行為影響）
          args: 'after-used',
          argsIgnorePattern: '^_',
          // script-tag 跨檔全域 class：定義於本檔、由其他檔案或 index.html
          // inline <script> 使用（2026-10-14 全倉 grep 驗證過），故本檔
          // 內的「定義但未用」為誤報；未列入此清單的名字照樣會被報。
          // ^_：解構棄位（如 for-of 第三元 _area、清理迴圈 _messageId）
          // 屬明示不用約定，非殘留。
          varsIgnorePattern:
            '^_|^(Logger|MaturityTracker|PerformanceManager|PluginManager|PrecisionManager|StateMatrix4D|StatePersistence|TerminalUI)$',
        },
      ],
      // no-console 關閉 —— 非「有意保留裸 console」，而是 console 已被
      // logger.js 的 installConsoleBridge() 接管：載入 logger.js 後所有
      // console.debug/info/log/warn/error 都路由到 Logger（分級 + 持久化 +
      // 監聽），Node CLI 腳本（無 window.angelaAppLogger）降級走原 console
      // 作為 stdout。no-console 規則的前提「原始未管理 console」已被橋接
      // 根治，此處關閉為如實反映架構（console = 受管分級日誌通道），
      // 而非把 2348 個警告當「有意債」留著。
      'no-console': 'off',
      'no-debugger': 'warn',
      'no-empty': 'warn',
      'no-irregular-whitespace': 'warn',
      'no-case-declarations': 'warn',
      'no-fallthrough': 'warn',
      'no-mixed-spaces-and-tabs': 'warn',
      'no-redeclare': 'warn',
      'no-undef': 'warn',
      'no-unreachable': 'warn',
      'no-useless-escape': 'warn',
    },
  },
]
