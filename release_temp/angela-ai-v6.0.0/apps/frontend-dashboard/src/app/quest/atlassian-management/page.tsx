"use client"
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Button } from '@acme/ui';
import { Input } from '@acme/ui';
import { Label } from '@acme/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui';
import { Alert, AlertDescription } from '@acme/ui';
import { Progress } from '@acme/ui';
import { Textarea } from '@acme/ui';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@acme/ui';
import { 
  Settings, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  ExternalLink,
  FileText,
  Bug,
  GitBranch,
  Users,
  Activity,
  Database,
  Plus,
  Search,
  Clock,
  Zap,
  Wifi,
  WifiOff,
  CloudOff
} from 'lucide-react';
import { 
  AtlassianConfig, 
  AtlassianService, 
  useAtlassianApi,
  ConfluenceSpace,
  JiraProject,
  RovoDevAgent,
  RovoDevTask
} from '@/lib/atlassian-api';

// 移除重复的接口定义，使用从 atlassian-api 导入的接口

export function AtlassianManagement() {
  // 初始化 API 客戶端
  const { client } = useAtlassianApi();
  const [services, setServices] = useState<AtlassianService[]>([
    { name: 'Confluence', status: 'connected', lastSync: '2 分鐘前', health: 95 },
    { name: 'Jira', status: 'connected', lastSync: '1 分鐘前', health: 88 },
    { name: 'Bitbucket', status: 'disconnected', lastSync: '從未', health: 0 },
  ]);

  const [config, setConfig] = useState<AtlassianConfig>({
    domain: '',
    userEmail: '',
    apiToken: '',
    cloudId: ''
  });

  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [offlineStatus, setOfflineStatus] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // 監控網絡狀態和離線功能
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 定期更新離線狀態和系統健康
    const updateStatus = async () => {
      if (client) {
        try {
          const offline = client.getOfflineStatus();
          setOfflineStatus(offline);
          
          const health = await client.getSystemHealth();
          setSystemHealth(health);
        } catch (error) {
          console.warn('無法獲取狀態:', error);
        }
      }
    };

    updateStatus();
    const interval = setInterval(updateStatus, 30000); // 每30秒更新

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [client]);

  const handleConnect = async () => {
    setIsConnecting(true);
    setConnectionStatus('idle');
    
    try {
      // 模擬連接過程
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 更新服務狀態
      setServices(prev => prev.map(service => ({
        ...service,
        status: 'connected' as const,
        lastSync: '剛剛',
        health: Math.floor(Math.random() * 20) + 80
      })));
      
      setConnectionStatus('success');
    } catch (error) {
      setConnectionStatus('error');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleRefresh = async () => {
    setIsConnecting(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setServices(prev => prev.map(service => ({
        ...service,
        lastSync: '剛剛',
        health: Math.floor(Math.random() * 20) + 80
      })));
    } finally {
      setIsConnecting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'default';
      case 'error':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const recentActivities = [
    { type: 'confluence', action: '創建頁面', title: 'API 文檔更新', time: '5 分鐘前' },
    { type: 'jira', action: '創建問題', title: 'Bug: 登錄失敗', time: '10 分鐘前' },
    { type: 'confluence', action: '更新頁面', title: '架構設計文檔', time: '15 分鐘前' },
    { type: 'jira', action: '狀態變更', title: 'UAI-123: 已完成', time: '20 分鐘前' },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'confluence':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'jira':
        return <Bug className="h-4 w-4 text-orange-500" />;
      case 'bitbucket':
        return <GitBranch className="h-4 w-4 text-green-500" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Atlassian 管理</h1>
          <p className="text-muted-foreground">管理 Rovo Dev Agents 和 Atlassian 服務集成</p>
        </div>
        
        {/* 網絡狀態指示器 */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {isOnline ? (
              <Wifi className="h-5 w-5 text-green-500" />
            ) : (
              <WifiOff className="h-5 w-5 text-red-500" />
            )}
            <span className="text-sm text-muted-foreground">
              {isOnline ? '在線' : '離線'}
            </span>
          </div>
          
          {offlineStatus && (
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-500" />
              <span className="text-xs text-muted-foreground">
                緩存: {offlineStatus.cacheSize} | 隊列: {offlineStatus.queueSize}
              </span>
            </div>
          )}
        </div>
      </div>

      {connectionStatus === 'success' && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            成功連接到 Atlassian 服務！所有服務現在都可以使用。
          </AlertDescription>
        </Alert>
      )}

      {connectionStatus === 'error' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            連接失敗。請檢查您的配置信息並重試。
          </AlertDescription>
        </Alert>
      )}

      {!isOnline && (
        <Alert>
          <CloudOff className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>
              目前處於離線模式。部分功能可能受限,但您可以查看緩存數據。
              {offlineStatus?.queueSize > 0 && ` 有 ${offlineStatus.queueSize} 個操作等待同步。`}
            </span>
            {client && offlineStatus?.queueSize > 0 && (
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => client.syncOfflineQueue()}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                同步
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概覽</TabsTrigger>
          <TabsTrigger value="configuration">配置</TabsTrigger>
          <TabsTrigger value="activity">活動記錄</TabsTrigger>
          <TabsTrigger value="rovo-agents">Rovo Agents</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => (
              <Card key={service.name}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {service.name}
                  </CardTitle>
                  {getStatusIcon(service.status)}
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Badge variant={getStatusColor(service.status) as any}>
                      {service.status === 'connected' ? '已連接' : 
                       service.status === 'error' ? '錯誤' : '未連接'}
                    </Badge>
                    <div className="text-xs text-muted-foreground">
                      最後同步: {service.lastSync}
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={service.health} className="h-2 flex-1" />
                      <span className="text-xs text-muted-foreground w-8">
                        {service.health}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex gap-2">
            <Button onClick={handleRefresh} disabled={isConnecting}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isConnecting ? 'animate-spin' : ''}`} />
              刷新狀態
            </Button>
            <Button variant="outline" asChild>
              <a href="https://developer.atlassian.com/" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                Atlassian 開發者文檔
              </a>
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="configuration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Atlassian 配置
              </CardTitle>
              <CardDescription>
                配置您的 Atlassian 實例連接信息
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="domain">域名</Label>
                  <Input
                    id="domain"
                    placeholder="your-domain"
                    value={config.domain}
                    onChange={(e) => setConfig(prev => ({ ...prev, domain: e.target.value }))}
                  />
                  <div className="text-xs text-muted-foreground">
                    例如: your-domain.atlassian.net 中的 "your-domain"
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">用戶郵箱</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="user@example.com"
                    value={config.userEmail}
                    onChange={(e) => setConfig(prev => ({ ...prev, userEmail: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="token">API Token</Label>
                  <Input
                    id="token"
                    type="password"
                    placeholder="您的 API Token"
                    value={config.apiToken}
                    onChange={(e) => setConfig(prev => ({ ...prev, apiToken: e.target.value }))}
                  />
                  <div className="text-xs text-muted-foreground">
                    在 Atlassian 帳戶設置中生成 API Token
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cloudId">Cloud ID</Label>
                  <Input
                    id="cloudId"
                    placeholder="您的 Cloud ID"
                    value={config.cloudId}
                    onChange={(e) => setConfig(prev => ({ ...prev, cloudId: e.target.value }))}
                  />
                </div>
              </div>
              
              <Button 
                onClick={handleConnect} 
                disabled={isConnecting || !config.domain || !config.userEmail || !config.apiToken}
                className="w-full"
              >
                {isConnecting ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    連接中...
                  </>
                ) : (
                  '測試連接'
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                最近活動
              </CardTitle>
              <CardDescription>
                Rovo Dev Agents 的最近操作記錄
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivities.map((activity, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                    {getActivityIcon(activity.type)}
                    <div className="flex-1">
                      <div className="font-medium">{activity.action}</div>
                      <div className="text-sm text-muted-foreground">{activity.title}</div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {activity.time}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rovo-agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Rovo Dev Agents 狀態
              </CardTitle>
              <CardDescription>
                智能開發代理的能力和狀態
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <h4 className="font-medium">可用能力</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 border rounded">
                      <span className="text-sm">代碼分析</span>
                      <Badge variant="default">啟用</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 border rounded">
                      <span className="text-sm">文檔生成</span>
                      <Badge variant="default">啟用</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 border rounded">
                      <span className="text-sm">問題追蹤</span>
                      <Badge variant="default">啟用</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 border rounded">
                      <span className="text-sm">項目管理</span>
                      <Badge variant="secondary">待機</Badge>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <h4 className="font-medium">性能指標</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">任務完成率</span>
                      <span className="text-sm font-medium">94%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">平均響應時間</span>
                      <span className="text-sm font-medium">1.2s</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">今日處理任務</span>
                      <span className="text-sm font-medium">47</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">錯誤率</span>
                      <span className="text-sm font-medium">0.8%</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
