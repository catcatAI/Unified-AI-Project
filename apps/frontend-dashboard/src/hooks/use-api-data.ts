// Custom hooks for API data management
import { useState, useEffect, useCallback } from 'react';
import { apiService, SystemStatus, ServiceHealth, DetailedSystemMetrics, AIAgent, NeuralNetworkModel, ModelMetrics, TrainingStatus, GeneratedImage, ImageStatistics, withFallback } from '@/lib/api';
import { dataArchiveService } from '@/lib/data-archive';

// Hook for system status
export function useSystemStatus() {
  const [data, setData] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const status = await apiService.getSystemStatus();
      setData(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system status');
      // Set fallback data
      setData({
        status: 'online',
        services: {
          ham_memory: true,
          hsp_protocol: true,
          neural_network: true,
          agent_manager: true,
          project_coordinator: true,
        },
        metrics: {
          active_models: 8,
          tasks_completed: 1247,
          active_agents: 12,
          api_requests: 45200,
        },
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for service health
export function useServiceHealth() {
  const [data, setData] = useState<ServiceHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const services = await apiService.getServiceHealth();
      setData(services);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch service health');
      // Set fallback data
      setData([
        {
          name: 'HAM Memory Manager',
          status: 'running',
          cpu: 15.2,
          memory: 234.5,
          uptime: '2d 14h 32m',
          last_check: new Date().toISOString(),
        },
        {
          name: 'HSP Connector',
          status: 'running',
          cpu: 8.7,
          memory: 156.3,
          uptime: '2d 14h 32m',
          last_check: new Date().toISOString(),
        },
        {
          name: 'Multi-LLM Service',
          status: 'running',
          cpu: 45.1,
          memory: 1024.8,
          uptime: '2d 14h 32m',
          last_check: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for system metrics
export function useSystemMetrics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const metrics = await apiService.getSystemMetrics();
      setData(metrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system metrics');
      // Set fallback data
      setData({
        cpu: { value: 45, max: 100, status: 'normal' },
        memory: { value: 6.2, max: 16, status: 'normal' },
        disk: { value: 128, max: 512, status: 'normal' },
        network: { value: 2.4, max: 10, status: 'normal' },
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for health check
export function useHealthCheck() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const checkHealth = useCallback(async () => {
    try {
      setLoading(true);
      await apiService.healthCheck();
      setIsHealthy(true);
    } catch (error) {
      setIsHealthy(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // Check every minute
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return { isHealthy, loading, checkHealth };
}

// Hook for chat functionality
export function useChat() {
  const [messages, setMessages] = useState<any[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your AI assistant. I can help you with various tasks including answering questions, generating content, analyzing data, and more. How can I assist you today?',
      timestamp: new Date(Date.now() - 300000),
      model: 'Backend AI'
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      setLoading(true);
      setError(null);
      
      // Send to backend
      const response = await apiService.sendChatMessage(content);
      setMessages(prev => [...prev, response]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      // Add error message
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I\'m having trouble connecting to the AI service right now. Please try again later.',
        timestamp: new Date(),
        model: 'System'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { messages, loading, error, sendMessage };
}

// Hook for detailed system metrics
export function useDetailedSystemMetrics() {
  const [data, setData] = useState<DetailedSystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const metrics = await apiService.getDetailedSystemMetrics();
      setData(metrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch detailed system metrics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for AI agents
export function useAIAgents() {
  const [data, setData] = useState<AIAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const agents = await apiService.getAIAgents();
      setData(agents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch AI agents');
    } finally {
      setLoading(false);
    }
  }, []);

  const performAction = useCallback(async (agentId: string, action: string, config?: any) => {
    try {
      const result = await apiService.performAgentAction(agentId, action, config);
      // Refresh data after action
      await fetchData();
      return result;
    } catch (err) {
      throw err;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
    // Refresh every 15 seconds
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData, performAction };
}

// Hook for specific AI agent
export function useAIAgent(agentId: string) {
  const [data, setData] = useState<AIAgent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!agentId) return;
    try {
      setLoading(true);
      setError(null);
      const agent = await apiService.getAIAgent(agentId);
      setData(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch AI agent');
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchData();
    // Refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for neural network models
export function useNeuralNetworkModels() {
  const [data, setData] = useState<NeuralNetworkModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const models = await apiService.getNeuralNetworkModels();
      setData(models);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch neural network models');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 20 seconds
    const interval = setInterval(fetchData, 20000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for model metrics
export function useModelMetrics(modelId: string) {
  const [data, setData] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!modelId) return;
    try {
      setLoading(true);
      setError(null);
      const metrics = await apiService.getModelMetrics(modelId);
      setData(metrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch model metrics');
    } finally {
      setLoading(false);
    }
  }, [modelId]);

  useEffect(() => {
    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for model training status
export function useModelTrainingStatus(modelId: string) {
  const [data, setData] = useState<TrainingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!modelId) return;
    try {
      setLoading(true);
      setError(null);
      const status = await apiService.getModelTrainingStatus(modelId);
      setData(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch training status');
    } finally {
      setLoading(false);
    }
  }, [modelId]);

  useEffect(() => {
    fetchData();
    // Refresh every 3 seconds for training status
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for image generation history
export function useImageHistory(page: number = 1, limit: number = 20) {
  const [data, setData] = useState<{ images: GeneratedImage[]; total: number; page: number; limit: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const history = await apiService.getImageHistory(page, limit);
      setData(history);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch image history');
    } finally {
      setLoading(false);
    }
  }, [page, limit]);

  const deleteImage = useCallback(async (imageId: string) => {
    try {
      const result = await apiService.deleteImage(imageId);
      // Refresh data after deletion
      await fetchData();
      return result;
    } catch (err) {
      throw err;
    }
  }, [fetchData]);

  const batchDeleteImages = useCallback(async (imageIds: string[]) => {
    try {
      const result = await apiService.batchDeleteImages(imageIds);
      // Refresh data after deletion
      await fetchData();
      return result;
    } catch (err) {
      throw err;
    }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData, deleteImage, batchDeleteImages };
}

// Hook for image statistics
export function useImageStatistics() {
  const [data, setData] = useState<ImageStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await apiService.getImageStatistics();
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch image statistics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

// Hook for saving chat messages to archive
export function useChatArchive() {
  const saveChatToArchive = useCallback(async (input: string, output: string) => {
    try {
      await dataArchiveService.saveEntry({
        type: 'chat',
        input,
        output,
      });
    } catch (error) {
      console.error('Failed to save chat to archive:', error);
    }
  }, []);

  return { saveChatToArchive };
}

// Hook for saving image generation to archive
export function useImageArchive() {
  const saveImageToArchive = useCallback(async (input: string, output: string, metadata?: Record<string, any>) => {
    try {
      await dataArchiveService.saveEntry({
        type: 'image',
        input,
        output,
        metadata,
      });
    } catch (error) {
      console.error('Failed to save image to archive:', error);
    }
  }, []);

  return { saveImageToArchive };
}

// Hook for saving web search to archive
export function useSearchArchive() {
  const saveSearchToArchive = useCallback(async (input: string, output: string, metadata?: Record<string, any>) => {
    try {
      await dataArchiveService.saveEntry({
        type: 'search',
        input,
        output,
        metadata,
      });
    } catch (error) {
      console.error('Failed to save search to archive:', error);
    }
  }, []);

  return { saveSearchToArchive };
}

// Hook for saving code analysis to archive
export function useCodeArchive() {
  const saveCodeToArchive = useCallback(async (input: string, output: string, metadata?: Record<string, any>) => {
    try {
      await dataArchiveService.saveEntry({
        type: 'code',
        input,
        output,
        metadata,
      });
    } catch (error) {
      console.error('Failed to save code to archive:', error);
    }
  }, []);

  return { saveCodeToArchive };
}
