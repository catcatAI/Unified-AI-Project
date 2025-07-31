// Atlassian API 接口定义 - 增強版（支持離線模式和備用機制）

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number;
}

interface OfflineQueueItem {
  id: string;
  method: string;
  url: string;
  data?: any;
  timestamp: number;
  retryCount: number;
}

class OfflineManager {
  private cache = new Map<string, CacheEntry>();
  private offlineQueue: OfflineQueueItem[] = [];
  private isOnline = navigator.onLine;
  private syncInProgress = false;

  constructor() {
    this.loadFromStorage();
    this.setupEventListeners();
  }

  private setupEventListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.syncOfflineQueue();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  private loadFromStorage() {
    try {
      const cachedData = localStorage.getItem('atlassian_cache');
      if (cachedData) {
        const parsed = JSON.parse(cachedData);
        this.cache = new Map(parsed.cache || []);
      }

      const queueData = localStorage.getItem('atlassian_offline_queue');
      if (queueData) {
        this.offlineQueue = JSON.parse(queueData);
      }
    } catch (error) {
      console.warn('Failed to load offline data:', error);
    }
  }

  private saveToStorage() {
    try {
      localStorage.setItem('atlassian_cache', JSON.stringify({
        cache: Array.from(this.cache.entries())
      }));

      localStorage.setItem('atlassian_offline_queue', JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.warn('Failed to save offline data:', error);
    }
  }

  getCached(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  setCache(key: string, data: any, ttl: number = 300000) { // 5分鐘默認TTL
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
    this.saveToStorage();
  }

  addToOfflineQueue(method: string, url: string, data?: any) {
    const item: OfflineQueueItem = {
      id: `${Date.now()}_${Math.random()}`,
      method,
      url,
      data,
      timestamp: Date.now(),
      retryCount: 0
    };

    this.offlineQueue.push(item);
    this.saveToStorage();
  }

  async syncOfflineQueue() {
    if (this.syncInProgress || !this.isOnline) return;

    this.syncInProgress = true;
    const processedItems: string[] = [];

    for (const item of this.offlineQueue) {
      try {
        await this.processOfflineItem(item);
        processedItems.push(item.id);
      } catch (error) {
        item.retryCount++;
        if (item.retryCount >= 3) {
          processedItems.push(item.id);
          console.error('Offline item failed permanently:', error);
        }
      }
    }

    this.offlineQueue = this.offlineQueue.filter(item => !processedItems.includes(item.id));
    this.saveToStorage();
    this.syncInProgress = false;
  }

  private async processOfflineItem(item: OfflineQueueItem) {
    const response = await fetch(item.url, {
      method: item.method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: item.data ? JSON.stringify(item.data) : undefined
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }

  getStatus() {
    return {
      isOnline: this.isOnline,
      cacheSize: this.cache.size,
      queueSize: this.offlineQueue.length,
      syncInProgress: this.syncInProgress
    };
  }
}

const offlineManager = new OfflineManager();
import { useState, useEffect } from 'react';

export interface AtlassianConfig {
  domain: string;
  userEmail: string;
  apiToken: string;
  cloudId: string;
}

export interface AtlassianService {
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync: string;
  health: number;
}

export interface ConfluenceSpace {
  id: string;
  key: string;
  name: string;
  type: string;
  status: string;
}

export interface ConfluencePage {
  id: string;
  title: string;
  type: string;
  status: string;
  space: {
    key: string;
    name: string;
  };
  version: {
    number: number;
  };
  _links: {
    webui: string;
  };
}

export interface JiraProject {
  id: string;
  key: string;
  name: string;
  projectTypeKey: string;
  simplified: boolean;
  style: string;
}

export interface JiraIssue {
  id: string;
  key: string;
  fields: {
    summary: string;
    description?: any;
    status: {
      name: string;
      statusCategory: {
        name: string;
      };
    };
    issuetype: {
      name: string;
      iconUrl: string;
    };
    priority: {
      name: string;
      iconUrl: string;
    };
    assignee?: {
      displayName: string;
      emailAddress: string;
    };
    created: string;
    updated: string;
  };
}

export interface RovoDevTask {
  taskId: string;
  capability: string;
  parameters: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: any;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

export interface RovoDevAgent {
  agentId: string;
  isActive: boolean;
  capabilities: string[];
  queueSize: number;
  activeTasks: number;
  metrics: {
    tasksCompleted: number;
    tasksFailed: number;
    averageResponseTime: number;
    lastActivity: string;
  };
}

// API 客户端类 - 增強版（支持備用機制）
export class AtlassianApiClient {
  private baseUrl: string;
  private backupUrls: string[];
  private config: AtlassianConfig;
  private currentEndpointIndex: number = 0;
  private maxRetries: number = 3;
  private retryDelay: number = 1000;

  constructor(config: AtlassianConfig, baseUrl: string, backupUrls: string[] = []) {
    this.config = config;
    this.baseUrl = baseUrl;
    this.backupUrls = backupUrls;
  }

  // 帶備用機制的請求方法
  private async makeRequestWithFallback(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<Response> {
    const urls = [this.baseUrl, ...this.backupUrls];
    let lastError: Error | null = null;

    for (let i = 0; i < urls.length; i++) {
      const url = `${urls[i]}${endpoint}`;
      const cacheKey = `${options.method || 'GET'}_${url}`;

      try {
        // 檢查緩存（僅限 GET 請求）
        if (!options.method || options.method === 'GET') {
          const cached = offlineManager.getCached(cacheKey);
          if (cached && !navigator.onLine) {
            console.log('返回離線緩存數據:', endpoint);
            return new Response(JSON.stringify(cached), {
              status: 200,
              headers: { 'Content-Type': 'application/json' }
            });
          }
        }

        // 嘗試請求
        const response = await fetch(url, {
          ...options,
          headers: {
            ...this.getAuthHeaders(),
            ...options.headers,
          },
        });

        if (response.ok) {
          // 成功，更新當前端點索引
          this.currentEndpointIndex = i;
          
          // 緩存 GET 請求結果
          if (!options.method || options.method === 'GET') {
            const data = await response.clone().json();
            offlineManager.setCache(cacheKey, data);
          }
          
          return response;
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

      } catch (error) {
        lastError = error as Error;
        console.warn(`端點 ${url} 請求失敗:`, error);
        
        // 如果不是最後一個端點，等待後重試
        if (i < urls.length - 1) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        }
      }
    }

    // 所有端點都失敗，檢查離線模式
    if (!navigator.onLine) {
      const cacheKey = `${options.method || 'GET'}_${this.baseUrl}${endpoint}`;
      const cached = offlineManager.getCached(cacheKey);
      if (cached) {
        console.log('所有端點失敗，返回緩存數據:', endpoint);
        return new Response(JSON.stringify(cached), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      // 如果是寫操作，加入離線隊列
      if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method)) {
        offlineManager.addToOfflineQueue(options.method, `${this.baseUrl}${endpoint}`, 
          options.body ? JSON.parse(options.body as string) : undefined);
        
        return new Response(JSON.stringify({ 
          success: true, 
          message: '操作已加入離線隊列，將在網絡恢復後同步' 
        }), {
          status: 202,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }

    throw lastError || new Error('所有 API 端點都不可用');
  }

  // 配置管理
  async testConnection(): Promise<{ [service: string]: boolean }> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(this.config),
      });
      return response.json();
    } catch (error) {
      console.error('連接測試失敗:', error);
      return { confluence: false, jira: false, bitbucket: false };
    }
  }

  async saveConfig(config: AtlassianConfig): Promise<boolean> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      return response.ok;
    } catch (error) {
      console.error('配置保存失敗:', error);
      return false;
    }
  }

  // Confluence API
  async getConfluenceSpaces(): Promise<ConfluenceSpace[]> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/confluence/spaces');
      return response.json();
    } catch (error) {
      console.error('獲取 Confluence 空間失敗:', error);
      return [];
    }
  }

  async getConfluencePages(spaceKey: string): Promise<ConfluencePage[]> {
    try {
      const response = await this.makeRequestWithFallback(
        `/atlassian/confluence/spaces/${spaceKey}/pages`
      );
      return response.json();
    } catch (error) {
      console.error('獲取 Confluence 頁面失敗:', error);
      return [];
    }
  }

  async createConfluencePage(
    spaceKey: string,
    title: string,
    content: string,
    parentId?: string
  ): Promise<ConfluencePage> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/confluence/pages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spaceKey,
          title,
          content,
          parentId,
        }),
      });
      return response.json();
    } catch (error) {
      console.error('創建 Confluence 頁面失敗:', error);
      throw error;
    }
  }

  // Jira API
  async getJiraProjects(): Promise<JiraProject[]> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/jira/projects');
      return response.json();
    } catch (error) {
      console.error('獲取 Jira 項目失敗:', error);
      return [];
    }
  }

  async getJiraIssues(projectKey: string): Promise<JiraIssue[]> {
    try {
      const response = await this.makeRequestWithFallback(
        `/atlassian/jira/projects/${projectKey}/issues`
      );
      return response.json();
    } catch (error) {
      console.error('獲取 Jira 問題失敗:', error);
      return [];
    }
  }

  async createJiraIssue(
    projectKey: string,
    summary: string,
    description: string,
    issueType: string = 'Task',
    priority: string = 'Medium'
  ): Promise<JiraIssue> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/jira/issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectKey,
          summary,
          description,
          issueType,
          priority,
        }),
      });
      return response.json();
    } catch (error) {
      console.error('創建 Jira 問題失敗:', error);
      throw error;
    }
  }

  async searchJiraIssues(jql: string): Promise<JiraIssue[]> {
    try {
      const response = await this.makeRequestWithFallback('/atlassian/jira/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ jql }),
      });
      const data = await response.json();
      return data.issues || [];
    } catch (error) {
      console.error('搜索 Jira 問題失敗:', error);
      return [];
    }
  }

  // Rovo Dev Agent API
  async getRovoDevAgentStatus(): Promise<RovoDevAgent> {
    try {
      const response = await this.makeRequestWithFallback('/rovo-dev/status');
      return response.json();
    } catch (error) {
      console.error('獲取 Rovo Dev Agent 狀態失敗:', error);
      throw error;
    }
  }

  async submitRovoDevTask(
    capability: string,
    parameters: Record<string, any>
  ): Promise<RovoDevTask> {
    try {
      const response = await this.makeRequestWithFallback('/rovo-dev/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          capability,
          parameters,
        }),
      });
      return response.json();
    } catch (error) {
      console.error('提交 Rovo Dev 任務失敗:', error);
      throw error;
    }
  }

  async getRovoDevTasks(): Promise<RovoDevTask[]> {
    try {
      const response = await this.makeRequestWithFallback('/rovo-dev/tasks');
      return response.json();
    } catch (error) {
      console.error('獲取 Rovo Dev 任務失敗:', error);
      return [];
    }
  }

  async getRovoDevTaskHistory(limit: number = 50): Promise<RovoDevTask[]> {
    try {
      const response = await this.makeRequestWithFallback(
        `/rovo-dev/tasks/history?limit=${limit}`
      );
      return response.json();
    } catch (error) {
      console.error('獲取 Rovo Dev 任務歷史失敗:', error);
      return [];
    }
  }

  // 新增：獲取恢復狀態
  async getRovoDevRecoveryStatus(): Promise<any> {
    try {
      const response = await this.makeRequestWithFallback('/rovo-dev/recovery-status');
      return response.json();
    } catch (error) {
      console.error('獲取恢復狀態失敗:', error);
      return null;
    }
  }

  // 新增：獲取系統健康狀態
  async getSystemHealth(): Promise<any> {
    try {
      const response = await this.makeRequestWithFallback('/system/health');
      return response.json();
    } catch (error) {
      console.error('獲取系統健康狀態失敗:', error);
      return { healthy: false, services: [] };
    }
  }

  // 新增：強制同步離線隊列
  async syncOfflineQueue(): Promise<boolean> {
    try {
      await offlineManager.syncOfflineQueue();
      return true;
    } catch (error) {
      console.error('同步離線隊列失敗:', error);
      return false;
    }
  }

  // 新增：獲取離線狀態
  getOfflineStatus() {
    return offlineManager.getStatus();
  }

  // 辅助方法
  private getAuthHeaders(): Record<string, string> {
    const credentials = `${this.config.userEmail}:${this.config.apiToken}`;
    const encodedCredentials = btoa(credentials);
    return {
      'Authorization': `Basic ${encodedCredentials}`,
      'X-Atlassian-Cloud-ID': this.config.cloudId, // Cloud ID might still be useful for some Atlassian APIs
    };
  }
}

// React Hook for Atlassian API
export function useAtlassianApi(config?: AtlassianConfig) {
  const [client, setClient] = useState<AtlassianApiClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [services, setServices] = useState<AtlassianService[]>([]);

  useEffect(() => {
    if (config) {
      const apiClient = new AtlassianApiClient(config, 'http://localhost:8000/api', [
        'http://localhost:8001/api',
        'http://localhost:8002/api',
      ]);
      setClient(apiClient);
      
      // 测试连接
      apiClient.testConnection().then((results) => {
        setIsConnected(Object.values(results).some(Boolean));
        setServices([
          {
            name: 'Confluence',
            status: results.confluence ? 'connected' : 'disconnected',
            lastSync: new Date().toISOString(),
            health: results.confluence ? 100 : 0,
          },
          {
            name: 'Jira',
            status: results.jira ? 'connected' : 'disconnected',
            lastSync: new Date().toISOString(),
            health: results.jira ? 100 : 0,
          },
        ]);
      }).catch(() => {
        setIsConnected(false);
        setServices([
          {
            name: 'Confluence',
            status: 'error',
            lastSync: new Date().toISOString(),
            health: 0,
          },
          {
            name: 'Jira',
            status: 'error',
            lastSync: new Date().toISOString(),
            health: 0,
          },
        ]);
      });
    }
  }, [config]);

  return {
    client,
    isConnected,
    services,
  };
}