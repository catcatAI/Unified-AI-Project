'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Zap,
  Users,
  Code,
  Image,
  MessageSquare,
  Github,
  Brain,
  BarChart3
} from 'lucide-react'

interface DashboardOverviewProps {
  systemHealth: any
}

export function DashboardOverview({ systemHealth }: DashboardOverviewProps) {
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'unhealthy':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      default:
        return <Activity className="h-5 w-5 text-gray-500" />
    }
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'unhealthy':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const services = [
    { name: 'AI 聊天', icon: MessageSquare, status: 'online', description: '統一AI對話服務' },
    { name: '圖像生成', icon: Image, status: 'online', description: 'AI圖像生成功能' },
    { name: '網路搜索', icon: Zap, status: 'online', description: '智能搜索服務' },
    { name: '代碼分析', icon: Code, status: 'degraded', description: '多語言代碼分析' },
    { name: 'GitHub 連接', icon: Github, status: 'online', description: 'GitHub集成服務' },
    { name: 'AI 代理', icon: Brain, status: 'online', description: '智能代理管理' },
  ]

  const recentActivities = [
    { type: 'chat', action: 'AI 對話', description: '用戶與AI助手進行對話', time: '2 分鐘前', status: 'success' },
    { type: 'image', action: '圖像生成', description: '生成了一張AI圖像', time: '5 分鐘前', status: 'success' },
    { type: 'search', action: '網路搜索', description: '執行了網路搜索查詢', time: '8 分鐘前', status: 'success' },
    { type: 'github', action: 'GitHub 同步', description: '同步了GitHub倉庫數據', time: '12 分鐘前', status: 'success' },
    { type: 'code', action: '代碼分析', description: '分析了代碼質量', time: '15 分鐘前', status: 'warning' },
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="default">成功</Badge>
      case 'warning':
        return <Badge variant="secondary">警告</Badge>
      case 'error':
        return <Badge variant="destructive">錯誤</Badge>
      default:
        return <Badge variant="outline">未知</Badge>
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'chat':
        return <MessageSquare className="h-4 w-4" />
      case 'image':
        return <Image className="h-4 w-4" />
      case 'search':
        return <Zap className="h-4 w-4" />
      case 'github':
        return <Github className="h-4 w-4" />
      case 'code':
        return <Code className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI 統一平台儀表板</h1>
          <p className="text-muted-foreground">
            整合多個AI服務的統一管理界面
          </p>
        </div>
        
        {systemHealth && (
          <div className={`flex items-center gap-3 px-4 py-2 rounded-lg border ${getHealthColor(systemHealth.overall)}`}>
            {getHealthIcon(systemHealth.overall)}
            <div>
              <div className="font-medium">
                系統狀態: {systemHealth.overall === 'healthy' ? '正常' : 
                         systemHealth.overall === 'degraded' ? '部分正常' : '異常'}
              </div>
              <div className="text-sm opacity-75">
                健康度: {systemHealth.percentage}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">在線服務</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemHealth?.services?.filter((s: any) => s.status === 'online').length || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              總共 {systemHealth?.services?.length || 0} 個服務
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日請求</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground">
              +12% 較昨日
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍用戶</CardTitle>
            <Users className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">89</div>
            <p className="text-xs text-muted-foreground">
              +5% 較昨日
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">系統延遲</CardTitle>
            <Activity className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">45ms</div>
            <p className="text-xs text-muted-foreground">
              平均響應時間
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Services Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => (
          <Card key={service.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <service.icon className="h-4 w-4" />
                {service.name}
              </CardTitle>
              <Badge variant={
                service.status === 'online' ? 'default' :
                service.status === 'degraded' ? 'secondary' : 'destructive'
              }>
                {service.status === 'online' ? '在線' :
                 service.status === 'degraded' ? '降級' : '離線'}
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-3">
                {service.description}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    service.status === 'online' ? 'bg-green-500' :
                    service.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                  }`} />
                  <span className="text-xs text-muted-foreground">
                    {service.status === 'online' ? '運行正常' :
                     service.status === 'degraded' ? '部分功能受限' : '服務不可用'}
                  </span>
                </div>
                <Button variant="outline" size="sm">
                  管理
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activities */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            最近活動
          </CardTitle>
          <CardDescription>
            系統最近的操作和事件記錄
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivities.map((activity, index) => (
              <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  {getActivityIcon(activity.type)}
                  {getStatusBadge(activity.status)}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{activity.action}</div>
                  <div className="text-sm text-muted-foreground">{activity.description}</div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {activity.time}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}