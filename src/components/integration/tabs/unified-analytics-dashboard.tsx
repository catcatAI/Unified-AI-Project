'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  BarChart3, 
  TrendingUp, 
  Users,
  Activity,
  Zap,
  Download,
  Calendar
} from 'lucide-react'

interface AnalyticsData {
  period: string
  totalRequests: number
  uniqueUsers: number
  avgResponseTime: number
  errorRate: number
  topServices: Array<{
    name: string
    requests: number
    growth: number
  }>
}

const mockData: AnalyticsData = {
  period: '過去30天',
  totalRequests: 45678,
  uniqueUsers: 1234,
  avgResponseTime: 45,
  errorRate: 0.05,
  topServices: [
    { name: 'AI 聊天', requests: 15678, growth: 12 },
    { name: '圖像生成', requests: 8934, growth: 8 },
    { name: '代碼分析', requests: 6723, growth: 15 },
    { name: '網路搜索', requests: 5432, growth: -2 },
    { name: 'GitHub 連接', requests: 4321, growth: 23 }
  ]
}

export function UnifiedAnalyticsDashboard() {
  const [data] = useState<AnalyticsData>(mockData)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">分析儀表板</h1>
          <p className="text-muted-foreground">
            使用統計與性能分析
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline">{data.period}</Badge>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" />
            導出報告
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總請求數</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.totalRequests.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +12% 較上期
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍用戶</CardTitle>
            <Users className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.uniqueUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +8% 較上期
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均響應時間</CardTitle>
            <Zap className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.avgResponseTime}ms</div>
            <p className="text-xs text-muted-foreground">
              -5% 較上期
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">錯誤率</CardTitle>
            <TrendingUp className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.errorRate}%</div>
            <p className="text-xs text-muted-foreground">
              -0.02% 較上期
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Top Services */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            熱門服務排行
          </CardTitle>
          <CardDescription>
            按請求量排序的服務使用情況
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.topServices.map((service, index) => (
              <div key={service.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-sm font-medium">{index + 1}</span>
                  </div>
                  <div>
                    <div className="font-medium">{service.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {service.requests.toLocaleString()} 次請求
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className={`text-sm font-medium ${
                      service.growth > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {service.growth > 0 ? '+' : ''}{service.growth}%
                    </div>
                    <div className="text-xs text-muted-foreground">增長率</div>
                  </div>
                  <div className="w-24">
                    <Progress 
                      value={Math.min(Math.abs(service.growth) * 2, 100)} 
                      className="h-2"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Usage Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              每日使用趨勢
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                <p>使用趨勢圖表</p>
                <p className="text-sm">即將推出</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              用戶分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                <p>用戶分布圖表</p>
                <p className="text-sm">即將推出</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}