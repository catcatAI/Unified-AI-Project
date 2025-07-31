/**
 * 統一整合橋接服務
 * 負責協調三個專案間的通信和數據流
 */

import { EventEmitter } from 'events'

// 整合服務配置
interface IntegrationConfig {
  unifiedAI: {
    baseUrl: string
    apiKey?: string
  }
  githubConnect: {
    baseUrl: string
    apiKey?: string
  }
  aiDashboard: {
    baseUrl: string
  }
}

// 服務狀態
interface ServiceStatus {
  name: string
  status: 'online' | 'offline' | 'error'
  lastCheck: Date
  latency?: number
  error?: string
}

// 整合事件類型
type IntegrationEvent = 
  | { type: 'service_status_changed'; service: string; status: ServiceStatus }
  | { type: 'ai_response'; data: any }
  | { type: 'github_event'; data: any }
  | { type: 'system_error'; error: string }

export class IntegrationBridge extends EventEmitter {
  private config: IntegrationConfig
  private serviceStatuses: Map<string, ServiceStatus> = new Map()
  private healthCheckInterval: NodeJS.Timeout | null = null

  constructor(config: IntegrationConfig) {
    super()
    this.config = config
    this.initializeServices()
  }

  /**
   * 初始化所有服務連接
   */
  private async initializeServices() {
    console.log('🔗 初始化整合橋接服務...')
    
    // 初始化服務狀態
    const services = ['unifiedAI', 'githubConnect', 'aiDashboard']
    for (const service of services) {
      this.serviceStatuses.set(service, {
        name: service,
        status: 'offline',
        lastCheck: new Date()
      })
    }

    // 開始健康檢查
    this.startHealthCheck()
    
    // 設置事件監聽器
    this.setupEventListeners()
  }

  /**
   * 開始服務健康檢查
   */
  private startHealthCheck() {
    this.healthCheckInterval = setInterval(async () => {
      await this.checkAllServices()
    }, 30000) // 每30秒檢查一次

    // 立即執行第一次檢查
    this.checkAllServices()
  }

  /**
   * 檢查所有服務狀態
   */
  private async checkAllServices() {
    const checks = [
      this.checkUnifiedAIService(),
      this.checkGithubConnectService(),
      this.checkAIDashboardService()
    ]

    await Promise.allSettled(checks)
  }

  /**
   * 檢查Unified-AI-Project服務狀態
   */
  private async checkUnifiedAIService(): Promise<void> {
    try {
      const startTime = Date.now()
      const response = await fetch(`${this.config.unifiedAI.baseUrl}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.unifiedAI.apiKey && { 
            'Authorization': `Bearer ${this.config.unifiedAI.apiKey}` 
          })
        }
      })

      const latency = Date.now() - startTime
      
      if (response.ok) {
        const status: ServiceStatus = {
          name: 'unifiedAI',
          status: 'online',
          lastCheck: new Date(),
          latency
        }
        this.updateServiceStatus('unifiedAI', status)
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      const status: ServiceStatus = {
        name: 'unifiedAI',
        status: 'error',
        lastCheck: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      this.updateServiceStatus('unifiedAI', status)
    }
  }

  /**
   * 檢查GitHub Connect服務狀態
   */
  private async checkGithubConnectService(): Promise<void> {
    try {
      const startTime = Date.now()
      // 由於github-connect-quest是前端應用，我們檢查其靜態資源
      const response = await fetch(`${this.config.githubConnect.baseUrl}`, {
        method: 'HEAD'
      })

      const latency = Date.now() - startTime
      
      if (response.ok) {
        const status: ServiceStatus = {
          name: 'githubConnect',
          status: 'online',
          lastCheck: new Date(),
          latency
        }
        this.updateServiceStatus('githubConnect', status)
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      const status: ServiceStatus = {
        name: 'githubConnect',
        status: 'error',
        lastCheck: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      this.updateServiceStatus('githubConnect', status)
    }
  }

  /**
   * 檢查AI Dashboard服務狀態
   */
  private async checkAIDashboardService(): Promise<void> {
    try {
      const startTime = Date.now()
      const response = await fetch(`${this.config.aiDashboard.baseUrl}/api/health`, {
        method: 'GET'
      })

      const latency = Date.now() - startTime
      
      if (response.ok) {
        const status: ServiceStatus = {
          name: 'aiDashboard',
          status: 'online',
          lastCheck: new Date(),
          latency
        }
        this.updateServiceStatus('aiDashboard', status)
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      const status: ServiceStatus = {
        name: 'aiDashboard',
        status: 'error',
        lastCheck: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      this.updateServiceStatus('aiDashboard', status)
    }
  }

  /**
   * 更新服務狀態
   */
  private updateServiceStatus(serviceName: string, status: ServiceStatus) {
    const previousStatus = this.serviceStatuses.get(serviceName)
    this.serviceStatuses.set(serviceName, status)

    // 如果狀態發生變化，發出事件
    if (!previousStatus || previousStatus.status !== status.status) {
      this.emit('service_status_changed', { service: serviceName, status })
    }
  }

  /**
   * 設置事件監聽器
   */
  private setupEventListeners() {
    // 監聽服務狀態變化
    this.on('service_status_changed', (event) => {
      console.log(`🔄 服務狀態變化: ${event.service} -> ${event.status.status}`)
      
      if (event.status.status === 'error') {
        this.emit('system_error', `服務 ${event.service} 出現錯誤: ${event.status.error}`)
      }
    })
  }

  /**
   * 獲取所有服務狀態
   */
  public getAllServiceStatuses(): ServiceStatus[] {
    return Array.from(this.serviceStatuses.values())
  }

  /**
   * 獲取特定服務狀態
   */
  public getServiceStatus(serviceName: string): ServiceStatus | undefined {
    return this.serviceStatuses.get(serviceName)
  }

  /**
   * 調用Unified-AI-Project API
   */
  public async callUnifiedAI(endpoint: string, options: RequestInit = {}): Promise<any> {
    try {
      const url = `${this.config.unifiedAI.baseUrl}${endpoint}`
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.unifiedAI.apiKey && { 
            'Authorization': `Bearer ${this.config.unifiedAI.apiKey}` 
          }),
          ...options.headers
        }
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Unified-AI-Project API call failed:', error)
      throw error
    }
  }

  /**
   * 調用GitHub Connect API
   */
  public async callGithubConnect(endpoint: string, options: RequestInit = {}): Promise<any> {
    try {
      const url = `${this.config.githubConnect.baseUrl}${endpoint}`
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.githubConnect.apiKey && { 
            'Authorization': `Bearer ${this.config.githubConnect.apiKey}` 
          }),
          ...options.headers
        }
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('GitHub Connect API call failed:', error)
      throw error
    }
  }

  /**
   * 調用AI Dashboard API
   */
  public async callAIDashboard(endpoint: string, options: RequestInit = {}): Promise<any> {
    try {
      const url = `${this.config.aiDashboard.baseUrl}${endpoint}`
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('AI Dashboard API call failed:', error)
      throw error
    }
  }

  /**
   * 發送AI聊天請求
   */
  public async sendAIChat(message: string, model?: string): Promise<any> {
    try {
      // 優先使用Unified-AI-Project
      if (this.getServiceStatus('unifiedAI')?.status === 'online') {
        return await this.callUnifiedAI('/api/v1/chat', {
          method: 'POST',
          body: JSON.stringify({
            user_id: 'dashboard_user',
            session_id: 'dashboard_session',
            text: message
          })
        })
      }

      // 備用：使用AI Dashboard
      if (this.getServiceStatus('aiDashboard')?.status === 'online') {
        return await this.callAIDashboard('/api/chat', {
          method: 'POST',
          body: JSON.stringify({ message, model })
        })
      }

      throw new Error('No AI service available')
    } catch (error) {
      console.error('AI chat failed:', error)
      throw error
    }
  }

  /**
   * 發送圖像生成請求
   */
  public async generateImage(prompt: string, size: string = '1024x1024'): Promise<any> {
    try {
      if (this.getServiceStatus('aiDashboard')?.status === 'online') {
        return await this.callAIDashboard('/api/image', {
          method: 'POST',
          body: JSON.stringify({ prompt, size })
        })
      }

      throw new Error('Image generation service not available')
    } catch (error) {
      console.error('Image generation failed:', error)
      throw error
    }
  }

  /**
   * 發送網路搜索請求
   */
  public async webSearch(query: string, num: number = 10): Promise<any> {
    try {
      if (this.getServiceStatus('aiDashboard')?.status === 'online') {
        return await this.callAIDashboard('/api/search', {
          method: 'POST',
          body: JSON.stringify({ query, num })
        })
      }

      throw new Error('Web search service not available')
    } catch (error) {
      console.error('Web search failed:', error)
      throw error
    }
  }

  /**
   * 獲取GitHub倉庫信息
   */
  public async getGitHubRepos(): Promise<any> {
    try {
      if (this.getServiceStatus('githubConnect')?.status === 'online') {
        return await this.callGithubConnect('/api/github/repos')
      }

      throw new Error('GitHub Connect service not available')
    } catch (error) {
      console.error('GitHub repos fetch failed:', error)
      throw error
    }
  }

  /**
   * 清理資源
   */
  public destroy() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval)
    }
    this.removeAllListeners()
  }
}

// 創建默認配置
export function createDefaultConfig(): IntegrationConfig {
  return {
    unifiedAI: {
      baseUrl: process.env.UNIFIED_AI_URL || 'http://localhost:8000',
      apiKey: process.env.UNIFIED_AI_API_KEY
    },
    githubConnect: {
      baseUrl: process.env.GITHUB_CONNECT_URL || 'http://localhost:5173',
      apiKey: process.env.GITHUB_CONNECT_API_KEY
    },
    aiDashboard: {
      baseUrl: '' // 使用相對路徑，因為我們在同一個應用中
    }
  }
}

// 創建全局實例
let globalBridge: IntegrationBridge | null = null

export function getIntegrationBridge(): IntegrationBridge {
  if (!globalBridge) {
    const config = createDefaultConfig()
    globalBridge = new IntegrationBridge(config)
  }
  return globalBridge
}

export function setIntegrationBridge(bridge: IntegrationBridge): void {
  if (globalBridge) {
    globalBridge.destroy()
  }
  globalBridge = bridge
}