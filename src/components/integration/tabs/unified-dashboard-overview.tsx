'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useState, useEffect } from 'react'
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
  BarChart3,
  TrendingUp,
  Clock,
  Server
} from 'lucide-react'

interface DashboardOverviewProps {
  systemHealth: any
}

interface ServiceStatus {
  name: string
  icon: any
  status: 'online' | 'degraded' | 'offline'
  description: string
  latency?: number
  uptime?: number
}

interface Activity {
  type: string
  action: string
  description: string
  time: string
  status: 'success' | 'warning' | 'error'
}

interface SystemMetrics {
  requests: number
  requestGrowth: number
  activeUsers: number
  userGrowth: number
  latency: number
  uptime: number
}

export function DashboardOverview({ systemHealth }: DashboardOverviewProps) {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'AI 聊天', icon: MessageSquare, status: 'online', description: '統一AI對話服務', latency: 45, uptime: 99.9 },
    { name: '圖像生成', icon: Image, status: 'online', description: 'AI圖像生成功能', latency: 120, uptime: 99.8 },
    { name: '網路搜索', icon: Zap, status: 'online', description: '智能搜索服務', latency: 85, uptime: 99.7 },
    { name: '代碼分析', icon: Code, status: 'degraded', description: '多語言代碼分析', latency: 200, uptime: 95.2 },
    { name: 'GitHub 連接', icon: Github, status: 'online', description: 'GitHub集成服務', latency: 65, uptime: 99.5 },
    { name: 'AI 代理', icon: Brain, status: 'online', description: '智能代理管理', latency: 35, uptime: 99.9 },
  ])

  const [metrics, setMetrics] = useState<SystemMetrics>({
    requests: 1234,
    requestGrowth: 12,
    activeUsers: 89,
    userGrowth: 5,
    latency: 45,
    uptime: 99.8
  })

  const [recentActivities, setRecentActivities] = useState<Activity[]>([
    { type: 'chat', action: 'AI 對話', description: '用戶與AI助手進行對話', time: '2 分鐘前', status: 'success' },
    { type: 'image', action: '圖像生成', description: '生成了一張AI圖像', time: '5 分鐘前', status: 'success' },
    { type: 'search', action: '網路搜索', description: '執行了網路搜索查詢', time: '8 分鐘前', status: 'success' },
    { type: 'github', action: 'GitHub 同步', description: '同步了GitHub倉庫數據', time: '12 分鐘前', status: 'success' },
    { type: 'code', action: '代碼分析', description: '分析了代碼質量', time: '15 分鐘前', status: 'warning' },
  ])

  // 模擬實時數據更新
  useEffect(() => {
    const interval = setInterval(() => {
      // 更新請求數量
      setMetrics(prev => ({
        ...prev,
        requests: prev.requests + Math.floor(Math.random() * 5),
        activeUsers: prev.activeUsers + Math.floor(Math.random() * 3) - 1,
        latency: Math.max(20, Math.min(100, prev.latency + Math.floor(Math.random() * 10) - 5))
      }))

      // 隨機更新服務狀態
      setServices(prev => prev.map(service => ({
        ...service,
        latency: Math.max(20, Math.min(300, service.latency + Math.floor(Math.random() * 20) - 10))
      })))

      // 添加新的活動記錄
      const activityTypes = ['chat', 'image', 'search', 'github', 'code']
      const activities = ['AI 對話', '圖像生成', '網路搜索', 'GitHub 同步', '代碼分析']
      const descriptions = [
        '用戶與AI助手進行對話',
        '生成了一張AI圖像',
        '執行了網路搜索查詢',
        '同步了GitHub倉庫數據',
        '分析了代碼質量'
      ]
      
      if (Math.random() > 0.7) {
        const randomIndex = Math.floor(Math.random() * activityTypes.length)
        const newActivity: Activity = {
          type: activityTypes[randomIndex],
          action: activities[randomIndex],
          description: descriptions[randomIndex],
          time: '剛剛',
          status: Math.random() > 0.9 ? 'warning' : 'success'
        }
        
        setRecentActivities(prev => [newActivity, ...prev.slice(0, 4)])
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [])

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

  const getLatencyColor = (latency: number) => {
    if (latency < 50) return 'text-green-600'
    if (latency < 100) return 'text-yellow-600'
    return 'text-red-600'
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
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日請求</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.requests.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              +{metrics.requestGrowth}% 較昨日
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍用戶</CardTitle>
            <Users className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.activeUsers}</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              +{metrics.userGrowth}% 較昨日
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">系統延遲</CardTitle>
            <Activity className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getLatencyColor(metrics.latency)}`}>
              {metrics.latency}ms
            </div>
            <p className="text-xs text-muted-foreground">
              平均響應時間
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">系統運行時間</CardTitle>
            <Server className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.uptime}%</div>
            <p className="text-xs text-muted-foreground">
              過去30天
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Services Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => (
          <Card key={service.name} className="hover:shadow-lg transition-shadow">
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
              <div className="space-y-2">
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
                  <span className={`text-xs font-medium ${getLatencyColor(service.latency || 0)}`}>
                    {service.latency}ms
                  </span>
                </div>
                {service.uptime && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">運行時間</span>
                    <span className="text-xs font-medium">{service.uptime}%</span>
                  </div>
                )}
              </div>
              <div className="mt-3 pt-3 border-t">
                <Button variant="outline" size="sm" className="w-full">
                  管理服務
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activities */}
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            實時活動
          </CardTitle>
          <CardDescription>
            系統最近的操作和事件記錄
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {recentActivities.map((activity, index) => (
              <div key={index} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-2">
                  {getActivityIcon(activity.type)}
                  {getStatusBadge(activity.status)}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{activity.action}</div>
                  <div className="text-sm text-muted-foreground">{activity.description}</div>
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
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