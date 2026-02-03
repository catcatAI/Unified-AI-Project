import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Progress } from '@acme/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui';
import { 
  Activity, 
  Database, 
  Network, 
  Cpu, 
  HardDrive,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';

export function SystemMonitor() {
  const systemMetrics = {
    cpu: 45,
    memory: 67,
    storage: 23,
    network: 89
  };

  const services = [
    { name: 'DialogueManager', status: 'healthy', uptime: '99.9%', lastCheck: '2s ago' },
    { name: 'HAM Memory Manager', status: 'healthy', uptime: '99.7%', lastCheck: '1s ago' },
    { name: 'HSP Connector', status: 'warning', uptime: '97.2%', lastCheck: '5s ago' },
    { name: 'Agent Manager', status: 'healthy', uptime: '99.8%', lastCheck: '1s ago' },
    { name: 'Learning Manager', status: 'healthy', uptime: '99.5%', lastCheck: '3s ago' },
    { name: 'Trust Manager', status: 'healthy', uptime: '100%', lastCheck: '1s ago' },
    { name: 'Emotion System', status: 'error', uptime: '85.1%', lastCheck: '30s ago' },
    { name: 'Crisis System', status: 'healthy', uptime: '99.9%', lastCheck: '2s ago' },
  ];

  const agents = [
    { name: 'Angela Meta-Agent', status: 'active', tasks: 3, memory: '234MB' },
    { name: 'Data Analyst', status: 'idle', tasks: 0, memory: '45MB' },
    { name: 'Creative Writer', status: 'active', tasks: 1, memory: '67MB' },
    { name: 'Translator', status: 'idle', tasks: 0, memory: '23MB' },
    { name: 'Code Analyzer', status: 'active', tasks: 2, memory: '89MB' },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'healthy':
      case 'active':
        return 'default';
      case 'warning':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">系統監控</h1>
        <p className="text-muted-foreground">實時監控統一AI系統運行狀況</p>
      </div>

      {/* System Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU 使用率</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.cpu}%</div>
            <Progress value={systemMetrics.cpu} className="mt-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">記憶體使用率</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.memory}%</div>
            <Progress value={systemMetrics.memory} className="mt-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">儲存使用率</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.storage}%</div>
            <Progress value={systemMetrics.storage} className="mt-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">網路活動</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.network}%</div>
            <Progress value={systemMetrics.network} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="services" className="space-y-4">
        <TabsList>
          <TabsTrigger value="services">核心服務</TabsTrigger>
          <TabsTrigger value="agents">代理狀態</TabsTrigger>
          <TabsTrigger value="memory">記憶系統</TabsTrigger>
        </TabsList>
        
        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                核心服務狀態
              </CardTitle>
              <CardDescription>
                監控AI系統各核心服務的運行狀況
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {services.map((service) => (
                  <div key={service.name} className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-muted-foreground">
                          最後檢查: {service.lastCheck}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusVariant(service.status)}>
                        {service.status}
                      </Badge>
                      <div className="text-sm text-muted-foreground">
                        運行時間: {service.uptime}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>代理狀態監控</CardTitle>
              <CardDescription>
                查看所有活躍代理的狀態和資源使用情況
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {agents.map((agent) => (
                  <div key={agent.name} className="flex items-center justify-between p-3 border border-border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(agent.status)}
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-muted-foreground">
                          記憶體: {agent.memory}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusVariant(agent.status)}>
                        {agent.status}
                      </Badge>
                      <div className="text-sm text-muted-foreground">
                        任務: {agent.tasks}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="memory" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>HAM 記憶系統</CardTitle>
              <CardDescription>
                分層抽象記憶系統的詳細狀態
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-4 border border-border rounded-lg">
                    <div className="text-lg font-bold">2,431</div>
                    <div className="text-sm text-muted-foreground">核心記憶條目</div>
                  </div>
                  <div className="p-4 border border-border rounded-lg">
                    <div className="text-lg font-bold">847</div>
                    <div className="text-sm text-muted-foreground">經驗記錄</div>
                  </div>
                  <div className="p-4 border border-border rounded-lg">
                    <div className="text-lg font-bold">156</div>
                    <div className="text-sm text-muted-foreground">學習紀錄</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>記憶體使用率</span>
                    <span>67%</span>
                  </div>
                  <Progress value={67} />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>檢索效能</span>
                    <span>98.5%</span>
                  </div>
                  <Progress value={98.5} />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
