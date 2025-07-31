'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Bot, 
  Activity, 
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Users,
  Settings
} from 'lucide-react'

interface AgentStatus {
  id: string
  name: string
  status: 'online' | 'offline' | 'busy' | 'error'
  capabilities: string[]
  performance: {
    tasks_completed: number
    success_rate: number
    avg_response_time: number
  }
  last_activity: string
}

const mockAgents: AgentStatus[] = [
  {
    id: '1',
    name: '代碼分析代理',
    status: 'online',
    capabilities: ['代碼審查', '錯誤檢測', '性能分析'],
    performance: {
      tasks_completed: 156,
      success_rate: 94,
      avg_response_time: 1.2
    },
    last_activity: '2 分鐘前'
  },
  {
    id: '2',
    name: '文檔生成代理',
    status: 'busy',
    capabilities: ['API文檔', '用戶手冊', '技術規範'],
    performance: {
      tasks_completed: 89,
      success_rate: 87,
      avg_response_time: 2.5
    },
    last_activity: '剛剛'
  },
  {
    id: '3',
    name: '測試自動化代理',
    status: 'online',
    capabilities: ['單元測試', '集成測試', 'E2E測試'],
    performance: {
      tasks_completed: 234,
      success_rate: 96,
      avg_response_time: 0.8
    },
    last_activity: '5 分鐘前'
  },
  {
    id: '4',
    name: '部署管理代理',
    status: 'offline',
    capabilities: ['CI/CD', '環境配置', '監控告警'],
    performance: {
      tasks_completed: 67,
      success_rate: 91,
      avg_response_time: 3.1
    },
    last_activity: '1 小時前'
  }
]

export function UnifiedAIAgents() {
  const [agents] = useState<AgentStatus[]>(mockAgents)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'busy': return <Clock className="h-4 w-4 text-yellow-500" />
      case 'error': return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'offline': return <Activity className="h-4 w-4 text-gray-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-50 border-green-200'
      case 'busy': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'error': return 'text-red-600 bg-red-50 border-red-200'
      case 'offline': return 'text-gray-600 bg-gray-50 border-gray-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'online': return '在線'
      case 'busy': return '忙碌'
      case 'error': return '錯誤'
      case 'offline': return '離線'
      default: return '未知'
    }
  }

  const getOverallHealth = () => {
    const onlineAgents = agents.filter(a => a.status === 'online').length
    const totalAgents = agents.length
    return Math.round((onlineAgents / totalAgents) * 100)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI 代理</h1>
          <p className="text-muted-foreground">
            智能代理管理與任務協調
          </p>
        </div>
        
        <Badge variant="outline" className="text-lg px-3 py-1">
          健康度: {getOverallHealth()}%
        </Badge>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">在線代理</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agents.filter(a => a.status === 'online').length}
            </div>
            <p className="text-xs text-muted-foreground">
              總共 {agents.length} 個代理
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總任務數</CardTitle>
            <Zap className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agents.reduce((sum, agent) => sum + agent.performance.tasks_completed, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              已完成任務
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均成功率</CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(agents.reduce((sum, agent) => sum + agent.performance.success_rate, 0) / agents.length)}%
            </div>
            <p className="text-xs text-muted-foreground">
              所有代理平均
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均響應時間</CardTitle>
            <Clock className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(agents.reduce((sum, agent) => sum + agent.performance.avg_response_time, 0) / agents.length).toFixed(1)}s
            </div>
            <p className="text-xs text-muted-foreground">
              響應時間
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Agents Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {agents.map((agent) => (
          <Card key={agent.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  <CardTitle className="text-lg">{agent.name}</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(agent.status)}
                  <Badge variant="outline" className={getStatusColor(agent.status)}>
                    {getStatusText(agent.status)}
                  </Badge>
                </div>
              </div>
              <CardDescription>
                最後活動: {agent.last_activity}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Capabilities */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">能力</h4>
                <div className="flex flex-wrap gap-1">
                  {agent.capabilities.map((capability, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {capability}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium">性能指標</h4>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>任務完成</span>
                    <span className="font-medium">{agent.performance.tasks_completed}</span>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>成功率</span>
                      <span className="font-medium">{agent.performance.success_rate}%</span>
                    </div>
                    <Progress value={agent.performance.success_rate} className="h-2" />
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span>平均響應時間</span>
                    <span className="font-medium">{agent.performance.avg_response_time}s</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Settings className="h-4 w-4 mr-1" />
                  配置
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  <Activity className="h-4 w-4 mr-1" />
                  詳情
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}