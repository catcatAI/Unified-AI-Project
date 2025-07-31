'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Monitor, 
  Cpu, 
  Database,
  Wifi,
  Activity,
  Zap,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

interface SystemMetric {
  name: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  icon: React.ReactNode
}

interface ServiceHealth {
  name: string
  status: 'healthy' | 'degraded' | 'down'
  uptime: string
  latency: number
}

const mockMetrics: SystemMetric[] = [
  {
    name: 'CPU 使用率',
    value: 45,
    unit: '%',
    status: 'normal',
    icon: <Cpu className="h-4 w-4" />
  },
  {
    name: '內存使用',
    value: 67,
    unit: '%',
    status: 'warning',
    icon: <Database className="h-4 w-4" />
  },
  {
    name: '磁盤使用',
    value: 23,
    unit: '%',
    status: 'normal',
    icon: <Database className="h-4 w-4" />
  },
  {
    name: '網絡延遲',
    value: 12,
    unit: 'ms',
    status: 'normal',
    icon: <Wifi className="h-4 w-4" />
  }
]

const mockServices: ServiceHealth[] = [
  {
    name: 'AI 聊天服務',
    status: 'healthy',
    uptime: '99.9%',
    latency: 45
  },
  {
    name: '圖像生成服務',
    status: 'healthy',
    uptime: '99.8%',
    latency: 120
  },
  {
    name: 'GitHub 連接',
    status: 'degraded',
    uptime: '95.2%',
    latency: 200
  },
  {
    name: '數據庫服務',
    status: 'healthy',
    uptime: '99.9%',
    latency: 8
  }
]

interface UnifiedSystemMonitorProps {
  systemHealth: any
}

export function UnifiedSystemMonitor({ systemHealth }: UnifiedSystemMonitorProps) {
  const [metrics] = useState<SystemMetric[]>(mockMetrics)
  const [services] = useState<ServiceHealth[]>(mockServices)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'text-green-600'
      case 'warning': return 'text-yellow-600'
      case 'critical': return 'text-red-600'
      case 'healthy': return 'text-green-600'
      case 'degraded': return 'text-yellow-600'
      case 'down': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'normal':
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning':
      case 'degraded': return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'critical':
      case 'down': return <AlertTriangle className="h-4 w-4 text-red-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getProgressColor = (value: number, type: string) => {
    if (type === 'latency') {
      return value < 50 ? 'bg-green-500' : value < 100 ? 'bg-yellow-500' : 'bg-red-500'
    }
    return value < 70 ? 'bg-green-500' : value < 90 ? 'bg-yellow-500' : 'bg-red-500'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">系統監控</h1>
          <p className="text-muted-foreground">
            實時系統指標與性能監控
          </p>
        </div>
        
        {systemHealth && (
          <Badge variant={
            systemHealth.overall === 'healthy' ? 'default' :
            systemHealth.overall === 'degraded' ? 'secondary' : 'destructive'
          }>
            系統狀態: {systemHealth.overall === 'healthy' ? '正常' :
                     systemHealth.overall === 'degraded' ? '部分正常' : '異常'}
          </Badge>
        )}
      </div>

      {/* System Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                {metric.icon}
                {metric.name}
              </CardTitle>
              {getStatusIcon(metric.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metric.value}{metric.unit}
              </div>
              <Progress 
                value={metric.unit === '%' ? metric.value : Math.min(metric.value * 2, 100)} 
                className="h-2 mt-2"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {metric.status === 'normal' ? '正常' :
                 metric.status === 'warning' ? '警告' : '嚴重'}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Service Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            服務健康狀態
          </CardTitle>
          <CardDescription>
            各個微服務的運行狀態
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {services.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(service.status)}
                  <div>
                    <div className="font-medium">{service.name}</div>
                    <div className="text-sm text-muted-foreground">
                      運行時間: {service.uptime}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm font-medium">延遲</div>
                    <div className={`text-xs ${getStatusColor(
                      service.latency < 50 ? 'normal' : 
                      service.latency < 100 ? 'warning' : 'critical'
                    )}`}>
                      {service.latency}ms
                    </div>
                  </div>
                  <div className="w-20">
                    <Progress 
                      value={Math.max(0, 100 - service.latency)} 
                      className="h-2"
                    />
                  </div>
                  <Badge variant={
                    service.status === 'healthy' ? 'default' :
                    service.status === 'degraded' ? 'secondary' : 'destructive'
                  }>
                    {service.status === 'healthy' ? '健康' :
                     service.status === 'degraded' ? '降級' : '停機'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Network Status */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-5 w-5" />
              網絡狀態
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">連接狀態</span>
              <Badge variant="default">已連接</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">上傳速度</span>
              <span className="text-sm font-medium">125 Mbps</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">下載速度</span>
              <span className="text-sm font-medium">89 Mbps</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">丟包率</span>
              <span className="text-sm font-medium">0.1%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              系統負載
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">1分鐘平均</span>
              <span className="text-sm font-medium">1.2</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">5分鐘平均</span>
              <span className="text-sm font-medium">0.8</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">15分鐘平均</span>
              <span className="text-sm font-medium">0.5</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">運行進程</span>
              <span className="text-sm font-medium">156</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              活動監控
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">活躍用戶</span>
              <span className="text-sm font-medium">89</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">API請求/分鐘</span>
              <span className="text-sm font-medium">1,234</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">錯誤率</span>
              <span className="text-sm font-medium">0.05%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">響應時間</span>
              <span className="text-sm font-medium">45ms</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}