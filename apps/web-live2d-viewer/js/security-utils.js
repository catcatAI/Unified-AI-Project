/**
 * =============================================================================
 * ANGELA-MATRIX: L6[执行层] 全层级 [A/B/C] L0+
 * =============================================================================
 *
 * 职责: 提供安全工具，包括 XSS 防护、输入验证和输出编码
 * 维度: 跨所有维度，确保数据和交互的安全性
 * 安全: 使用 A/B/C 密钥机制进行数据验证
 * 成熟度: L0+ 等级即可使用基本安全功能
 *
 * 功能:
 * - XSS 防护（输入验证和输出编码）
 * - HTML 转义和反转义
 * - URL 编码和解码
 * - SQL 注入防护
 * - 命令注入防护
 * - 内容安全策略（CSP）支持
 */

class SecurityUtils {
    constructor() {
        // XSS 攻击模式
        this.xssPatterns = [
            /<script[^>]*>.*?<\/script>/gi,
            /<iframe[^>]*>.*?<\/iframe>/gi,
            /<object[^>]*>.*?<\/object>/gi,
            /<embed[^>]*>.*?<\/embed>/gi,
            /<link[^>]*>.*?<\/link>/gi,
            /<meta[^>]*>.*?<\/meta>/gi,
            /<style[^>]*>.*?<\/style>/gi,
            /on\w+\s*=\s*["'].*?["']/gi,
            /javascript:\s*\w+/gi,
            /vbscript:\s*\w+/gi,
            /data:\s*text\/html/gi,
            /expression\s*\(/gi,
            /eval\s*\(/gi,
            /fromCharCode/gi,
            /&#[\d]+;/g,
            /&#x[0-9a-fA-F]+;/g,
            /<[\s]*!(\-\-)/g,
            /<[\s]*![\s]*CDATA/gi,
            /<[\s]*![\s]*DOCTYPE/gi,
            /<[\s]*![\s]*ENTITY/gi
        ];

        // 允许的 HTML 标签（白名单）
        this.allowedTags = {
            'div': true,
            'span': true,
            'p': true,
            'b': true,
            'strong': true,
            'i': true,
            'em': true,
            'u': true,
            'a': true,
            'br': true,
            'hr': true,
            'ul': true,
            'ol': true,
            'li': true,
            'h1': true,
            'h2': true,
            'h3': true,
            'h4': true,
            'h5': true,
            'h6': true
        };

        // 允许的 HTML 属性（白名单）
        this.allowedAttributes = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'div': ['class', 'id', 'style'],
            'span': ['class', 'id', 'style']
        };

        // SQL 注入模式
        this.sqlInjectionPatterns = [
            /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|UNION)\b)/gi,
            /(\-\-)|(#)|(;)/g,
            /(\bOR\b|\bAND\b)\s*\d+\s*=\s*\d+/gi,
            /(\bOR\b|\bAND\b)\s*['"][\w\s]+['"]\s*=\s*['"][\w\s]+['"]/gi,
            /(\bOR\b|\bAND\b)\s*true\s*=\s*true/gi,
            /(\bOR\b|\bAND\b)\s*1\s*=\s*1/gi
        ];

        // 命令注入模式
        this.commandInjectionPatterns = [
            /[;&|`$(){}]/g,
            /(\bcat\b|\bcp\b|\bmv\b|\bchmod\b|\bchown\b|\brm\b|\bkill\b|\bkillall\b)/gi
        ];

        console.log('[SecurityUtils] Initialized');
    }

    /**
     * 检测 XSS 攻击
     * @param {string} input 输入字符串
     * @returns {boolean} 是否检测到 XSS
     */
    detectXSS(input) {
        if (typeof input !== 'string') {
            return false;
        }

        for (const pattern of this.xssPatterns) {
            if (pattern.test(input)) {
                console.warn('[SecurityUtils] XSS pattern detected:', pattern);
                return true;
            }
        }

        return false;
    }

    /**
     * HTML 转义（防止 XSS）
     * @param {string} str 要转义的字符串
     * @returns {string} 转义后的字符串
     */
    escapeHTML(str) {
        if (typeof str !== 'string') {
            return str;
        }

        const escapeMap = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        };

        return str.replace(/[&<>"'/]/g, char => escapeMap[char]);
    }

    /**
     * HTML 反转义
     * @param {string} str 要反转义的字符串
     * @returns {string} 反转义后的字符串
     */
    unescapeHTML(str) {
        if (typeof str !== 'string') {
            return str;
        }

        const unescapeMap = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#x27;': "'",
            '&#x2F;': '/'
        };

        return str.replace(/&(amp|lt|gt|quot|#x27|#x2F);/g, match => unescapeMap[match]);
    }

    /**
     * 验证并清理 HTML
     * @param {string} html HTML 字符串
     * @param {boolean} stripTags 是否移除所有标签
     * @returns {string} 清理后的 HTML
     */
    sanitizeHTML(html, stripTags = false) {
        if (typeof html !== 'string') {
            return html;
        }

        if (stripTags) {
            // 移除所有 HTML 标签
            return html.replace(/<[^>]*>/g, '');
        }

        // 使用白名单过滤 HTML
        const domParser = new DOMParser();
        const doc = domParser.parseFromString(html, 'text/html');

        function sanitizeNode(node) {
            // 文本节点直接返回
            if (node.nodeType === Node.TEXT_NODE) {
                return;
            }

            // 如果不是元素节点，移除
            if (node.nodeType !== Node.ELEMENT_NODE) {
                node.remove();
                return;
            }

            const tagName = node.tagName.toLowerCase();

            // 如果标签不在白名单中，移除
            if (!this.allowedTags[tagName]) {
                node.remove();
                return;
            }

            // 移除不在白名单中的属性
            const allowedAttrs = this.allowedAttributes[tagName] || [];
            const attrsToRemove = [];

            for (const attr of node.attributes) {
                if (!allowedAttrs.includes(attr.name.toLowerCase())) {
                    attrsToRemove.push(attr.name);
                } else if (attr.name.toLowerCase() === 'href' && attr.value) {
                    // 清理 href 属性中的 javascript: 伪协议
                    if (attr.value.toLowerCase().startsWith('javascript:')) {
                        attrsToRemove.push(attr.name);
                    }
                }
            }

            attrsToRemove.forEach(attrName => node.removeAttribute(attrName));

            // 递归处理子节点
            const children = Array.from(node.childNodes);
            children.forEach(child => sanitizeNode(child));
        }

        // 递归清理所有节点
        Array.from(doc.body.childNodes).forEach(child => sanitizeNode(child));

        return doc.body.innerHTML;
    }

    /**
     * URL 编码
     * @param {string} url URL 字符串
     * @returns {string} 编码后的 URL
     */
    encodeURL(url) {
        if (typeof url !== 'string') {
            return url;
        }
        return encodeURIComponent(url);
    }

    /**
     * URL 解码
     * @param {string} encodedUrl 编码的 URL
     * @returns {string} 解码后的 URL
     */
    decodeURL(encodedUrl) {
        if (typeof encodedUrl !== 'string') {
            return encodedUrl;
        }
        return decodeURIComponent(encodedUrl);
    }

    /**
     * 检测 SQL 注入
     * @param {string} input 输入字符串
     * @returns {boolean} 是否检测到 SQL 注入
     */
    detectSQLInjection(input) {
        if (typeof input !== 'string') {
            return false;
        }

        for (const pattern of this.sqlInjectionPatterns) {
            if (pattern.test(input)) {
                console.warn('[SecurityUtils] SQL injection pattern detected:', pattern);
                return true;
            }
        }

        return false;
    }

    /**
     * 检测命令注入
     * @param {string} input 输入字符串
     * @returns {boolean} 是否检测到命令注入
     */
    detectCommandInjection(input) {
        if (typeof input !== 'string') {
            return false;
        }

        for (const pattern of this.commandInjectionPatterns) {
            if (pattern.test(input)) {
                console.warn('[SecurityUtils] Command injection pattern detected:', pattern);
                return true;
            }
        }

        return false;
    }

    /**
     * 验证输入字符串
     * @param {string} input 输入字符串
     * @param {Object} options 验证选项
     * @returns {Object} 验证结果 { valid: boolean, sanitized: string, errors: Array }
     */
    validateInput(input, options = {}) {
        const result = {
            valid: true,
            sanitized: input,
            errors: []
        };

        if (typeof input !== 'string') {
            result.valid = false;
            result.errors.push('Input is not a string');
            return result;
        }

        const {
            checkXSS = true,
            checkSQLInjection = true,
            checkCommandInjection = true,
            escapeHTML = true,
            maxLength = null,
            minLength = null,
            pattern = null
        } = options;

        // XSS 检测
        if (checkXSS && this.detectXSS(input)) {
            result.valid = false;
            result.errors.push('XSS detected in input');
        }

        // SQL 注入检测
        if (checkSQLInjection && this.detectSQLInjection(input)) {
            result.valid = false;
            result.errors.push('SQL injection detected in input');
        }

        // 命令注入检测
        if (checkCommandInjection && this.detectCommandInjection(input)) {
            result.valid = false;
            result.errors.push('Command injection detected in input');
        }

        // 长度验证
        if (maxLength !== null && input.length > maxLength) {
            result.valid = false;
            result.errors.push(`Input exceeds maximum length of ${maxLength}`);
        }

        if (minLength !== null && input.length < minLength) {
            result.valid = false;
            result.errors.push(`Input is shorter than minimum length of ${minLength}`);
        }

        // 模式验证
        if (pattern !== null && !pattern.test(input)) {
            result.valid = false;
            result.errors.push('Input does not match required pattern');
        }

        // HTML 转义
        if (escapeHTML) {
            result.sanitized = this.escapeHTML(input);
        }

        return result;
    }

    /**
     * 创建安全的 DOM 元素
     * @param {string} tagName 标签名
     * @param {Object} attributes 属性对象
     * @param {string} textContent 文本内容
     * @returns {HTMLElement} DOM 元素
     */
    createSafeElement(tagName, attributes = {}, textContent = '') {
        // 验证标签名
        if (!this.allowedTags[tagName.toLowerCase()]) {
            throw new Error(`Tag "${tagName}" is not allowed`);
        }

        const element = document.createElement(tagName);

        // 设置安全的属性
        const allowedAttrs = this.allowedAttributes[tagName.toLowerCase()] || [];
        for (const [attrName, attrValue] of Object.entries(attributes)) {
            if (allowedAttrs.includes(attrName.toLowerCase())) {
                // 特殊处理 href 属性
                if (attrName.toLowerCase() === 'href' && typeof attrValue === 'string') {
                    if (attrValue.toLowerCase().startsWith('javascript:')) {
                        console.warn('[SecurityUtils] Blocked javascript: in href attribute');
                        continue;
                    }
                }
                element.setAttribute(attrName, attrValue);
            } else {
                console.warn(`[SecurityUtils] Attribute "${attrName}" is not allowed on tag "${tagName}"`);
            }
        }

        // 设置安全的文本内容
        if (textContent) {
            element.textContent = textContent;
        }

        return element;
    }

    /**
     * 生成内容安全策略（CSP）元标签
     * @param {Object} options CSP 选项
     * @returns {string} CSP 策略字符串
     */
    generateCSP(options = {}) {
        const {
            defaultSrc = "'self'",
            scriptSrc = "'self'",
            styleSrc = "'self' 'unsafe-inline'",
            imgSrc = "'self' data:",
            connectSrc = "'self'",
            fontSrc = "'self'",
            objectSrc = "'none'",
            mediaSrc = "'self'",
            frameSrc = "'none'",
            frameAncestors = "'none'",
            formAction = "'self'",
            baseUri = "'self'",
            manifestSrc = "'self'",
            workerSrc = "'self'",
            reportUri = null
        } = options;

        const cspDirectives = [
            `default-src ${defaultSrc}`,
            `script-src ${scriptSrc}`,
            `style-src ${styleSrc}`,
            `img-src ${imgSrc}`,
            `connect-src ${connectSrc}`,
            `font-src ${fontSrc}`,
            `object-src ${objectSrc}`,
            `media-src ${mediaSrc}`,
            `frame-src ${frameSrc}`,
            `frame-ancestors ${frameAncestors}`,
            `form-action ${formAction}`,
            `base-uri ${baseUri}`,
            `manifest-src ${manifestSrc}`,
            `worker-src ${workerSrc}`
        ];

        if (reportUri) {
            cspDirectives.push(`report-uri ${reportUri}`);
        }

        return cspDirectives.join('; ');
    }

    /**
     * 应用 CSP 到文档
     * @param {Object} options CSP 选项
     */
    applyCSP(options = {}) {
        const csp = this.generateCSP(options);

        // 检查是否已存在 CSP meta 标签
        let metaTag = document.querySelector('meta[http-equiv="Content-Security-Policy"]');

        if (!metaTag) {
            // 创建新的 CSP meta 标签
            metaTag = document.createElement('meta');
            metaTag.httpEquiv = 'Content-Security-Policy';
            document.head.appendChild(metaTag);
        }

        metaTag.content = csp;

        console.log('[SecurityUtils] CSP applied:', csp);
    }
}

// 创建全局单例
if (typeof window !== 'undefined') {
    window.securityUtils = new SecurityUtils();
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityUtils;
}