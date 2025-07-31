'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { 
  MessageSquare, 
  Image, 
  Search, 
  Code, 
  Activity, 
  Settings,
  Home,
  Bot,
  Brain,
  Zap,
  Github,
  Monitor,
  Users,
  BarChart3,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

interface SidebarProps {
  className?: string
  activeTab: string
  onTabChange: (tab: string) => void
  systemHealth?: any
}

const sidebarItems = [
  {
    title: '儀表板',
    icon: Home,
    tab: 'dashboard',
    description: '系統概覽與健康狀態'
  },
  {
    title: 'AI 聊天',
    icon: MessageSquare,
    tab: 'chat',
    description: '統一AI對話界面'
  },
  {
    title: '圖像生成',
    icon: Image,
    tab: 'image',
    description: 'AI圖像生成服務'
  },
  {
    title: '網路搜索',
    icon: Search,
    tab: 'search',
    description: 'AI驅動的搜索功能'
  },
  {
    title: '代碼分析',
    icon: Code,
    tab: 'code',
    description: '多語言代碼質量分析'
  },
  {
    title: 'AI 代理',
    icon: Bot,
    tab: 'agents',
    description: '智能代理管理'
  },
  {
    title: '神經網絡',
    icon: Brain,
    tab: 'neural',
    description: '模型訓練與監控'
  },
  {
    title: 'GitHub 連接',
    icon: Github,
    tab: 'github',
    description: 'GitHub集成與自動化'
  },
  {
    title: '系統監控',
    icon: Monitor,
    tab: 'monitor',
    description: '實時系統指標'
  },
  {
    title: '分析儀表板',
    icon: BarChart3,
    tab: 'analytics',
    description: '使用統計與分析'
  },
  {
    title: '團隊協作',
    icon: Users,
    tab: 'team',
    description: '團隊通信與工作空間'
  },
  {
    title: '設置',
    icon: Settings,
    tab: 'settings',
    description: '系統配置'
  }
]

export function UnifiedSidebar({ className, activeTab, onTabChange, systemHealth }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  const getServiceStatusIcon = (serviceName: string) => {
    if (!systemHealth || !systemHealth.services) return null

    const service = systemHealth.services.find((s: any) => 
      s.name.toLowerCase().includes(serviceName.toLowerCase())
    )

    if (!service) return null

    switch (service.status) {
      case 'online':
        return <CheckCircle className="h-3 w-3 text-green-500" />
      case 'error':
        return <AlertTriangle className="h-3 w-3 text-red-500" />
      default:
        return <AlertTriangle className="h-3 w-3 text-yellow-500" />
    }
  }

  const getOverallHealthColor = () => {
    if (!systemHealth) return 'bg-gray-500'
    
    switch (systemHealth.overall) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'unhealthy':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className={cn(
      'border-r bg-gray-50/40 transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-72',
      className
    )}>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-14 items-center border-b px-4">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-primary" />
              <div>
                <span className="font-semibold">AI 統一平台</span>
                {systemHealth && (
                  <div className="flex items-center gap-1">
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      getOverallHealthColor()
                    )} />
                    <span className="text-xs text-muted-foreground">
                      {systemHealth.percentage}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-8 w-8 p-0"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            <span className="sr-only">Toggle sidebar</span>
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </Button>
        </div>
        
        {/* Navigation */}
        <ScrollArea className="flex-1 px-2 py-4">
          <div className="space-y-1">
            {sidebarItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.tab
              
              return (
                <Button
                  key={item.tab}
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    'w-full justify-start',
                    isCollapsed && 'justify-center px-2',
                    isActive && 'bg-secondary'
                  )}
                  onClick={() => onTabChange(item.tab)}
                  title={isCollapsed ? item.title : undefined}
                >
                  <Icon className={cn(
                    'h-4 w-4',
                    !isCollapsed && 'mr-2'
                  )} />
                  
                  {!isCollapsed && (
                    <div className="flex flex-col items-start flex-1">
                      <div className="flex items-center justify-between w-full">
                        <span className="text-sm font-medium">{item.title}</span>
                        {getServiceStatusIcon(item.tab)}
                      </div>
                      <span className="text-xs text-muted-foreground text-left">
                        {item.description}
                      </span>
                    </div>
                  )}
                </Button>
              )
            })}
          </div>
        </ScrollArea>
        
        {/* Footer */}
        {!isCollapsed && systemHealth && (
          <div className="border-t p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">系統狀態</span>
              <Badge variant={
                systemHealth.overall === 'healthy' ? 'default' :
                systemHealth.overall === 'degraded' ? 'secondary' : 'destructive'
              }>
                {systemHealth.overall === 'healthy' ? '正常' :
                 systemHealth.overall === 'degraded' ? '部分正常' : '異常'}
              </Badge>
            </div>
            
            <div className="space-y-2">
              {systemHealth.services.map((service: any) => (
                <div key={service.name} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{service.name}</span>
                  <div className="flex items-center gap-1">
                    {getServiceStatusIcon(service.name)}
                    <span className={
                      service.status === 'online' ? 'text-green-600' :
                      service.status === 'error' ? 'text-red-600' : 'text-yellow-600'
                    }>
                      {service.status === 'online' ? '在線' :
                       service.status === 'error' ? '錯誤' : '離線'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="text-xs text-muted-foreground">
              最後更新: {new Date(systemHealth.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}