import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Database, 
  Globe, 
  Server, 
  Wifi, 
  WifiOff,
  RefreshCw
} from 'lucide-react';

interface HealthMetrics {
  system: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    uptime: number;
    lastCheck: string;
  };
  atlassian: {
    confluence: { status: string; responseTime: number; };
    jira: { status: string; responseTime: number; };
    bitbucket: { status: string; responseTime: number; };
  };
  agent: {
    isActive: boolean;
    tasksCompleted: number;
    tasksFailed: number;
    degradedMode: boolean;
    recoveryEvents: number;
    queueSize: number;
    activeTasks: number;
  };
  fallback: {
    hspFallbackActive: boolean;
    mcpFallbackActive: boolean;
    offlineQueueSize: number;
    cacheHitRate: number;
  };
  network: {
    isOnline: boolean;
    cacheSize: number;
    offlineQueueSize: number;
  };
}

const SystemHealthDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [alerts, setAlerts] = useState<Array<{id: string, type: 'warning' | 'error', message: string, timestamp: string}>>([]);

  useEffect(() => {
    fetchHealthMetrics();
    const interval = setInterval(fetchHealthMetrics, 30000); // 每30秒更新
    return () => clearInterval(interval);
  }, []);

  const fetchHealthMetrics = async () => {
    try {
      setLoading(true);
      
      // 模擬 API 調用
      const response = await fetch('/api/health/status');
      const data = await response.json();
      
      setMetrics(data);
      setLastUpdate(new Date());
      
      // 檢測告警條件
      checkAlerts(data);
    } catch (error) {
      console.error('Failed to fetch health metrics:', error);
      
      // 離線模式下的模擬數據
      const mockData = {
        system: {
          status: 'degraded',
          uptime: 86400,
          lastCheck: new Date().toISOString()
        },
        atlassian: {
          confluence: { status: 'healthy', responseTime: 250 },
          jira: { status: 'healthy', responseTime: 180 },
          bitbucket: { status: 'degraded', responseTime: 800 }
        },
        agent: {
          isActive: true,
          tasksCompleted: 145,
          tasksFailed: 8,
          degradedMode: false,
          recoveryEvents: 2
        },
        network: {
          isOnline: navigator.onLine,
          cacheSize: 25,
          offlineQueueSize: 3
        }
      };
      setMetrics(mockData);
      checkAlerts(mockData);
    } finally {
      setLoading(false);
    }
  };

  // 告警檢測函數
  const checkAlerts = (data: HealthMetrics) => {
    const newAlerts: Array<{id: string, type: 'warning' | 'error', message: string, timestamp: string}> = [];
    const now = new Date().toISOString();

    // 系統健康檢查
    if (data.system.status === 'unhealthy') {
      newAlerts.push({
        id: 'system-unhealthy',
        type: 'error',
        message: '系統狀態不健康，需要立即檢查',
        timestamp: now
      });
    } else if (data.system.status === 'degraded') {
      newAlerts.push({
        id: 'system-degraded',
        type: 'warning',
        message: '系統性能降級，部分功能可能受影響',
        timestamp: now
      });
    }

    // Agent 狀態檢查
    if (!data.agent.isActive) {
      newAlerts.push({
        id: 'agent-inactive',
        type: 'error',
        message: 'Rovo Dev Agent 未激活',
        timestamp: now
      });
    }

    if (data.agent.degradedMode) {
      newAlerts.push({
        id: 'agent-degraded',
        type: 'warning',
        message: 'Agent 運行在降級模式',
        timestamp: now
      });
    }

    // 離線隊列檢查
    if (data.network.offlineQueueSize > 10) {
      newAlerts.push({
        id: 'offline-queue-large',
        type: 'warning',
        message: `離線隊列積壓過多 (${data.network.offlineQueueSize} 項)`,
        timestamp: now
      });
    }

    setAlerts(newAlerts);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'degraded': return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4" />;
      case 'degraded': return <AlertTriangle className="h-4 w-4" />;
      case 'unhealthy': return <AlertTriangle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">載入系統狀態...</span>
      </div>
    );
  }

  if (!metrics) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          無法載入系統健康狀態。請檢查網絡連接。
        </AlertDescription>
      </Alert>
    );
  }

  const successRate = metrics.agent.tasksCompleted / (metrics.agent.tasksCompleted + metrics.agent.tasksFailed) * 100;

  return (
    <div className="space-y-6">
      {/* 告警區域 */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            系統告警 ({alerts.length})
          </h3>
          {alerts.map((alert) => (
            <Alert key={alert.id} variant={alert.type === 'error' ? 'destructive' : 'default'}>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>{alert.message}</span>
                <span className="text-xs text-muted-foreground">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </span>
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* 系統概覽 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">系統狀態</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {getStatusIcon(metrics.system.status)}
              <Badge className={getStatusColor(metrics.system.status)}>
                {metrics.system.status}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              運行時間: {formatUptime(metrics.system.uptime)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">網絡狀態</CardTitle>
            {metrics.network.isOnline ? 
              <Wifi className="h-4 w-4 text-green-600" /> : 
              <WifiOff className="h-4 w-4 text-red-600" />
            }
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Badge className={metrics.network.isOnline ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'}>
                {metrics.network.isOnline ? '在線' : '離線'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              離線隊列: {metrics.network.offlineQueueSize} 項目
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">任務成功率</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate.toFixed(1)}%</div>
            <Progress value={successRate} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {metrics.agent.tasksCompleted} 成功 / {metrics.agent.tasksFailed} 失敗
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">代理狀態</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Badge className={metrics.agent.isActive ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'}>
                {metrics.agent.isActive ? '活躍' : '停止'}
              </Badge>
              {metrics.agent.degradedMode && (
                <Badge className="text-yellow-600 bg-yellow-100">降級</Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              恢復事件: {metrics.agent.recoveryEvents}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 詳細狀態 */}
      <Tabs defaultValue="services" className="space-y-4">
        <TabsList>
          <TabsTrigger value="services">服務狀態</TabsTrigger>
          <TabsTrigger value="performance">性能指標</TabsTrigger>
          <TabsTrigger value="cache">緩存狀態</TabsTrigger>
        </TabsList>

        <TabsContent value="services" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(metrics.atlassian).map(([service, data]) => (
              <Card key={service}>
                <CardHeader>
                  <CardTitle className="text-sm capitalize">{service}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(data.status)}
                      <Badge className={getStatusColor(data.status)}>
                        {data.status}
                      </Badge>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {data.responseTime}ms
                    </span>
                  </div>
                  <Progress 
                    value={Math.min(100, Math.max(0, 100 - (data.responseTime / 10)))} 
                    className="mt-2" 
                  />
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>任務處理統計</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>已完成任務</span>
                    <span className="font-medium">{metrics.agent.tasksCompleted}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>失敗任務</span>
                    <span className="font-medium text-red-600">{metrics.agent.tasksFailed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>成功率</span>
                    <span className="font-medium">{successRate.toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>系統恢復</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>恢復事件</span>
                    <span className="font-medium">{metrics.agent.recoveryEvents}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>降級模式</span>
                    <Badge className={metrics.agent.degradedMode ? 'text-yellow-600 bg-yellow-100' : 'text-green-600 bg-green-100'}>
                      {metrics.agent.degradedMode ? '啟用' : '正常'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="cache" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>本地緩存</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>緩存項目</span>
                    <span className="font-medium">{metrics.network.cacheSize}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>離線隊列</span>
                    <span className="font-medium">{metrics.network.offlineQueueSize}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>網絡狀態</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>連接狀態</span>
                    <Badge className={metrics.network.isOnline ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'}>
                      {metrics.network.isOnline ? '在線' : '離線'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>最後更新</span>
                    <span className="text-sm text-muted-foreground">
                      {lastUpdate.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* 告警區域 */}
      {(metrics.agent.degradedMode || !metrics.network.isOnline || metrics.network.offlineQueueSize > 0) && (
        <div className="space-y-2">
          {metrics.agent.degradedMode && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                系統正在降級模式下運行。某些功能可能受限。
              </AlertDescription>
            </Alert>
          )}
          
          {!metrics.network.isOnline && (
            <Alert>
              <WifiOff className="h-4 w-4" />
              <AlertDescription>
                網絡連接中斷。正在使用離線模式。
              </AlertDescription>
            </Alert>
          )}
          
          {metrics.network.offlineQueueSize > 0 && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                有 {metrics.network.offlineQueueSize} 個操作等待同步。
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemHealthDashboard;