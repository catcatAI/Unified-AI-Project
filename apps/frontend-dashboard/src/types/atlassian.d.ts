// Atlassian 集成相关的类型定义

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
  description?: string;
  homepageId?: string;
}

export interface JiraProject {
  id: string;
  key: string;
  name: string;
  description?: string;
  lead?: string;
}

export interface RovoDevAgent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'inactive' | 'busy';
}

export interface RovoDevTask {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assignedAgent?: string;
  createdAt: string;
  updatedAt: string;
}