export interface ArchitectureConfig {
  id: string;
  name: string;
  version: string;
  description: string;
  nodes: any[];
  edges: any[];
  createdAt: string;
  updatedAt: string;
  metadata: {
    author: string;
    tags: string[];
    platform: 'web' | 'desktop' | 'mobile';
  };
}

export interface ComponentGroup {
  id: string;
  name: string;
  description: string;
  components: string[];
  color: string;
}

export const defaultComponentGroups: ComponentGroup[] = [
  {
    id: 'frontend-ui',
    name: '前端 UI 組件',
    description: '用戶界面相關組件',
    components: ['chat-interface', 'dashboard', 'settings-panel', 'file-manager'],
    color: 'hsl(var(--chart-1))'
  },
  {
    id: 'frontend-logic',
    name: '前端邏輯',
    description: '前端業務邏輯組件',
    components: ['state-manager', 'api-client', 'validation', 'routing'],
    color: 'hsl(var(--chart-2))'
  },
  {
    id: 'backend-api',
    name: '後端 API',
    description: 'API 服務層',
    components: ['rest-api', 'graphql-api', 'websocket-api', 'auth-api'],
    color: 'hsl(var(--chart-3))'
  },
  {
    id: 'backend-core',
    name: '後端核心',
    description: '核心業務邏輯',
    components: ['ai-engine', 'data-processor', 'task-scheduler', 'notification-service'],
    color: 'hsl(var(--chart-4))'
  },
  {
    id: 'data-layer',
    name: '數據層',
    description: '數據存儲和管理',
    components: ['database', 'cache', 'file-storage', 'search-engine'],
    color: 'hsl(var(--chart-5))'
  },
  {
    id: 'ai-models',
    name: 'AI 模型',
    description: 'AI 相關模型和工具',
    components: ['llm-interface', 'embedding-model', 'classification-model', 'generation-model'],
    color: 'hsl(var(--primary))'
  }
];

export const defaultArchitectureConfig: ArchitectureConfig = {
  id: 'unified-ai-default',
  name: 'Unified AI Project 預設架構',
  version: '1.0.0',
  description: '統一AI專案的預設系統架構',
  nodes: [],
  edges: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  metadata: {
    author: 'System',
    tags: ['default', 'ai', 'unified'],
    platform: 'web'
  }
};

export class ArchitectureStore {
  private static instance: ArchitectureStore;
  
  public static getInstance(): ArchitectureStore {
    if (!ArchitectureStore.instance) {
      ArchitectureStore.instance = new ArchitectureStore();
    }
    return ArchitectureStore.instance;
  }

  async saveArchitecture(config: ArchitectureConfig): Promise<void> {
    try {
      // 保存到 localStorage (web)
      localStorage.setItem(`architecture_${config.id}`, JSON.stringify(config));
      
      // 保存到 IndexedDB 以支持大文件
      await this.saveToIndexedDB(config);
      
      // 如果是桌面應用，也保存到文件系統
      if (this.isDesktopApp()) {
        await this.saveToFileSystem(config);
      }
      
      console.log('Architecture saved successfully:', config.id);
    } catch (error) {
      console.error('Failed to save architecture:', error);
      throw error;
    }
  }

  async loadArchitecture(id: string): Promise<ArchitectureConfig | null> {
    try {
      // 優先從 IndexedDB 加載
      const config = await this.loadFromIndexedDB(id);
      if (config) return config;
      
      // 備用：從 localStorage 加載
      const stored = localStorage.getItem(`architecture_${id}`);
      if (stored) {
        return JSON.parse(stored);
      }
      
      return null;
    } catch (error) {
      console.error('Failed to load architecture:', error);
      return null;
    }
  }

  async exportArchitecture(id: string): Promise<Blob> {
    const config = await this.loadArchitecture(id);
    if (!config) throw new Error('Architecture not found');
    
    const exportData = {
      ...config,
      exportedAt: new Date().toISOString(),
      exportFormat: 'unified-ai-v1'
    };
    
    return new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
  }

  async importArchitecture(file: File): Promise<ArchitectureConfig> {
    const text = await file.text();
    const data = JSON.parse(text);
    
    // 驗證格式
    if (!data.exportFormat || !data.id) {
      throw new Error('Invalid architecture file format');
    }
    
    const config: ArchitectureConfig = {
      ...data,
      id: `imported_${Date.now()}`,
      updatedAt: new Date().toISOString()
    };
    
    await this.saveArchitecture(config);
    return config;
  }

  private async saveToIndexedDB(config: ArchitectureConfig): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('UnifiedAI', 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['architectures'], 'readwrite');
        const store = transaction.objectStore('architectures');
        
        const putRequest = store.put(config);
        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(putRequest.error);
      };
      
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains('architectures')) {
          db.createObjectStore('architectures', { keyPath: 'id' });
        }
      };
    });
  }

  private async loadFromIndexedDB(id: string): Promise<ArchitectureConfig | null> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('UnifiedAI', 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction(['architectures'], 'readonly');
        const store = transaction.objectStore('architectures');
        
        const getRequest = store.get(id);
        getRequest.onsuccess = () => resolve(getRequest.result || null);
        getRequest.onerror = () => reject(getRequest.error);
      };
    });
  }

  private async saveToFileSystem(config: ArchitectureConfig): Promise<void> {
    // 這裡將來可以接入 Electron 的文件系統 API
    if (window.electronAPI) {
      await window.electronAPI.saveArchitecture(config);
    }
  }

  private isDesktopApp(): boolean {
    return typeof window !== 'undefined' && !!window.electronAPI;
  }
}

declare global {
  interface Window {
    electronAPI?: {
      saveArchitecture: (config: ArchitectureConfig) => Promise<void>;
      loadArchitecture: (id: string) => Promise<ArchitectureConfig | null>;
    };
  }
}