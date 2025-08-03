// Custom hooks for API data management
import { useState, useEffect, useCallback } from 'react';
import { apiService, SystemStatus, ServiceHealth, withFallback } from '@/lib/api';

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