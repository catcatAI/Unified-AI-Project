"use client"
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button, Input, Textarea, Badge } from '@acme/ui';

interface AtlassianStatus {
  acli_available: boolean;
  version: string;
  path: string;
}

interface JiraProject {
  key: string;
  name: string;
  description?: string;
}

interface JiraIssue {
  key: string;
  summary: string;
  status?: string;
  assignee?: string;
}

const AtlassianIntegration: React.FC = () => {
  const [status, setStatus] = useState<AtlassianStatus | null>(null);
  const [projects, setProjects] = useState<JiraProject[]>([]);
  const [issues, setIssues] = useState<JiraIssue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 表单状态
  const [jql, setJql] = useState('');
  const [newIssue, setNewIssue] = useState({
    project_key: '',
    summary: '',
    description: '',
    issue_type: 'Task',
    priority: '',
    labels: ''
  });

  const apiCall = async (endpoint: string, method: string = 'GET', body?: any) => {
    try {
      const response = await fetch(`/api/v1/atlassian/${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  };

  const checkStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiCall('status');
      setStatus(result);
    } catch (error) {
      setError('Failed to check Atlassian status');
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiCall('jira/projects');
      if (result.success) {
        setProjects(result.projects || []);
      } else {
        setError(result.error || 'Failed to load projects');
      }
    } catch (error) {
      setError('Failed to load Jira projects');
    } finally {
      setLoading(false);
    }
  };

  const loadIssues = async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = jql ? `jira/issues?jql=${encodeURIComponent(jql)}&limit=20` : 'jira/issues?limit=20';
      const result = await apiCall(endpoint);
      if (result.success) {
        setIssues(result.issues || []);
      } else {
        setError(result.error || 'Failed to load issues');
      }
    } catch (error) {
      setError('Failed to load Jira issues');
    } finally {
      setLoading(false);
    }
  };

  const createIssue = async () => {
    if (!newIssue.project_key || !newIssue.summary) {
      setError('Project key and summary are required');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await apiCall('jira/issue', 'POST', newIssue);
      if (result.success) {
        setNewIssue({ project_key: '', summary: '', description: '', issue_type: 'Task', priority: '', labels: '' });
        loadIssues(); // 重新加载问题列表
      } else {
        setError(result.error || 'Failed to create issue');
      }
    } catch (error) {
      setError('Failed to create Jira issue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Atlassian集成</h2>
        <Button onClick={checkStatus} disabled={loading}>
          刷新状态
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Atlassian CLI状态 */}
      <Card>
        <CardHeader>
          <CardTitle>Atlassian CLI状态</CardTitle>
        </CardHeader>
        <CardContent>
          {status ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span>状态:</span>
                <Badge variant={status.acli_available ? "default" : "destructive"}>
                  {status.acli_available ? "可用" : "不可用"}
                </Badge>
              </div>
              <p><strong>版本:</strong> {status.version}</p>
              <p><strong>路径:</strong> {status.path}</p>
              {!status.acli_available && (
                <div className="mt-3 p-3 border rounded text-sm bg-yellow-50">
                  <p className="font-semibold">提示：</p>
                  <ul className="list-disc pl-5">
                    <li>尚未偵測到 Atlassian CLI（acli.exe）。</li>
                    <li>請依官方文件安裝並設定認證。</li>
                    <li>Windows 環境可將 acli.exe 放在專案根目錄或加入 PATH。</li>
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p>正在检查状态...</p>
          )}
        </CardContent>
      </Card>

      {/* Jira项目 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Jira项目
            <Button onClick={loadProjects} disabled={loading} size="sm">
              加载项目
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {projects.length > 0 ? (
            <div className="grid gap-2">
              {projects.slice(0, 10).map((project) => (
                <div key={project.key} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <strong>{project.key}</strong>: {project.name}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>暂无项目数据</p>
          )}
        </CardContent>
      </Card>

      {/* Jira问题查询 */}
      <Card>
        <CardHeader>
          <CardTitle>Jira问题</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="输入JQL查询 (可选)"
              value={jql}
              onChange={(e) => setJql(e.target.value)}
            />
            <Button onClick={loadIssues} disabled={loading}>
              查询问题
            </Button>
          </div>
          <div className="flex gap-2 mt-2">
            <Button variant="outline" onClick={() => { setJql('assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC'); loadIssues(); }}>我的未解決</Button>
            <Button variant="outline" onClick={() => { setJql('resolution = Unresolved ORDER BY priority DESC'); loadIssues(); }}>全部未解決</Button>
            <Button variant="outline" onClick={() => { setJql('ORDER BY created DESC'); loadIssues(); }}>最新建立</Button>
          </div>

          {issues.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-semibold">问题列表:</h4>
              {issues.map((issue) => (
                <div key={issue.key} className="p-2 border rounded">
                  <div className="flex items-center justify-between">
                    <strong>{issue.key}</strong>
                    {issue.status && <Badge variant="outline">{issue.status}</Badge>}
                  </div>
                  <p className="text-sm text-gray-600">{issue.summary}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 创建Jira问题 */}
      <Card>
        <CardHeader>
          <CardTitle>创建Jira问题</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              placeholder="项目键 (如: PROJ)"
              value={newIssue.project_key}
              onChange={(e) => setNewIssue({...newIssue, project_key: e.target.value})}
            />
            <select
              value={newIssue.issue_type}
              onChange={(e) => setNewIssue({...newIssue, issue_type: e.target.value})}
              className="px-3 py-2 border rounded-md"
            >
              <option value="Task">任务</option>
              <option value="Bug">缺陷</option>
              <option value="Story">用户故事</option>
              <option value="Epic">史诗</option>
            </select>
          </div>
          
          <Input
            placeholder="问题摘要"
            value={newIssue.summary}
            onChange={(e) => setNewIssue({...newIssue, summary: e.target.value})}
          />
          
          <Textarea
            placeholder="问题描述 (可选)"
            value={newIssue.description}
            onChange={(e) => setNewIssue({...newIssue, description: e.target.value})}
            rows={3}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              placeholder="优先级 (可选，例如: High/Medium/Low)"
              value={newIssue.priority}
              onChange={(e) => setNewIssue({...newIssue, priority: e.target.value})}
            />
            <Input
              placeholder="标签 (逗号分隔，可选)"
              value={newIssue.labels}
              onChange={(e) => setNewIssue({...newIssue, labels: e.target.value})}
            />
          </div>
          
          <Button 
            onClick={createIssue} 
            disabled={loading || !newIssue.project_key || !newIssue.summary}
          >
            创建问题
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default AtlassianIntegration;