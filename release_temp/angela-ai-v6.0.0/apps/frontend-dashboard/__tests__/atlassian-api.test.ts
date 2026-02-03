/**
 * Atlassian API 客户端测试
 */
import { atlassianApiClient } from '../src/lib/atlassian-api';

// Mock fetch API
global.fetch = jest.fn();

describe('AtlassianApiClient', () => {
  beforeEach(() => {
    // 清除所有模拟调用
    (fetch as jest.Mock).mockClear();
  });

  it('should configure Atlassian integration', async () => {
    // 模拟成功的响应
    (fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce({ success: true })
    });

    const config = {
      domain: 'test.atlassian.net',
      userEmail: 'test@example.com',
      apiToken: 'test_token',
      cloudId: 'test_cloud_id'
    };

    const result = await atlassianApiClient.configure(config);

    expect(result).toBe(true);
    expect(fetch).toHaveBeenCalledWith('/api/py/api/v1/atlassian/configure', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        domain: 'test.atlassian.net',
        user_email: 'test@example.com',
        api_token: 'test_token',
        cloud_id: 'test_cloud_id'
      }),
    });
  });

  it('should get Atlassian status', async () => {
    // 模拟成功的响应
    (fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce({
        connected: true,
        services: [
          { name: 'Confluence', status: 'connected', lastSync: 'Just now', health: 95 }
        ]
      })
    });

    const status = await atlassianApiClient.getStatus();

    expect(status.connected).toBe(true);
    expect(status.services.length).toBe(1);
    expect(status.services[0].name).toBe('Confluence');
  });

  it('should get Jira projects', async () => {
    // 模拟成功的响应
    (fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce({
        projects: [
          { id: '10000', key: 'TEST', name: 'Test Project' }
        ]
      })
    });

    const projects = await atlassianApiClient.getJiraProjects();

    expect(projects.length).toBe(1);
    expect(projects[0].key).toBe('TEST');
  });

  it('should handle network errors gracefully', async () => {
    // 模拟网络错误
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    // 测试离线状态下获取状态
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false
    });

    const status = await atlassianApiClient.getStatus();

    expect(status.connected).toBe(false);
    expect(status.services.length).toBe(3); // 默认的三个服务
  });
});