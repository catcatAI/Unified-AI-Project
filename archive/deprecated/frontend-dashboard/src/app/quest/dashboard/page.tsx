import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Progress } from '@acme/ui';
import { 
  Brain, 
  Database, 
  MessageSquare, 
  Users, 
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';

export function Dashboard() {
  const systemModules = [
    { name: 'DialogueManager', status: '運行中', health: 95 },
    { name: 'HAM Memory', status: '運行中', health: 88 },
    { name: 'HSP Connector', status: '待機', health: 75 },
    { name: 'Agent Manager', status: '運行中', health: 92 },
    { name: 'Learning Manager', status: '運行中', health: 85 },
  ];

  const stats = [
    {
      title: '活躍代理',
      value: '12',
      icon: Users,
      trend: '+2 from last hour'
    },
    {
      title: '對話會話',
      value: '847',
      icon: MessageSquare,
      trend: '+15% this week'
    },
    {
      title: '記憶條目',
      value: '2,431',
      icon: Database,
      trend: '+127 today'
    },
    {
      title: '系統健康度',
      value: '89%',
      icon: Activity,
      trend: 'All systems operational'
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">儀表板</h1>
        <p className="text-muted-foreground">統一AI專案系統概覽</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.trend}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* System Modules */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              核心模組狀態
            </CardTitle>
            <CardDescription>
              AI系統各模組運行狀況
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {systemModules.map((module) => (
              <div key={module.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {module.status === '運行中' ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : module.status === '待機' ? (
                      <Clock className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="font-medium">{module.name}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={module.status === '運行中' ? 'default' : 'secondary'}
                  >
                    {module.status}
                  </Badge>
                  <div className="w-16">
                    <Progress value={module.health} className="h-2" />
                  </div>
                  <span className="text-sm text-muted-foreground w-8">
                    {module.health}%
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Project Architecture */}
        <Card>
          <CardHeader>
            <CardTitle>專案架構</CardTitle>
            <CardDescription>
              統一AI專案技術棧概覽
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">AI核心系統</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">DialogueManager</Badge>
                  <Badge variant="outline">HAM Memory</Badge>
                  <Badge variant="outline">LIS System</Badge>
                  <Badge variant="outline">Meta-Formula</Badge>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">代理協作框架</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">Meta-Agent Angela</Badge>
                  <Badge variant="outline">Specialized Agents</Badge>
                  <Badge variant="outline">Agent Manager</Badge>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-2">通信協議</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">HSP Protocol</Badge>
                  <Badge variant="outline">MQTT Connector</Badge>
                  <Badge variant="outline">Service Discovery</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
