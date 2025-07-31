'use client'

import { useState, useEffect } from 'react'
import { UnifiedSidebar } from './unified-sidebar'
import { DashboardOverview } from './tabs/unified-dashboard-overview'
import { UnifiedAIChat } from './tabs/unified-ai-chat'
import { UnifiedImageGeneration } from './tabs/unified-image-generation'
import { UnifiedWebSearch } from './tabs/unified-web-search'
import { UnifiedCodeAnalysis } from './tabs/unified-code-analysis'
import { UnifiedAIAgents } from './tabs/unified-ai-agents'
import { UnifiedNeuralNetwork } from './tabs/unified-neural-network'
import { UnifiedGithubConnect } from './tabs/unified-github-connect'
import { UnifiedSystemMonitor } from './tabs/unified-system-monitor'
import { UnifiedAnalyticsDashboard } from './tabs/unified-analytics-dashboard'
import { UnifiedTeamCollaboration } from './tabs/unified-team-collaboration'
import { UnifiedSettings } from './tabs/unified-settings'
import { getIntegrationBridge } from '@/lib/integration-bridge'

export function UnifiedDashboardLayout() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [systemHealth, setSystemHealth] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  // 初始化整合橋接服務
  useEffect(() => {
    const bridge = getIntegrationBridge()
    
    // 監聽服務狀態變化
    const handleStatusChange = (event: any) => {
      console.log('Service status changed:', event)
      // 可以在這裡更新UI或觸發其他操作
    }

    bridge.on('service_status_changed', handleStatusChange)

    // 獲取初始系統健康狀態
    const fetchSystemHealth = async () => {
      try {
        const response = await fetch('/api/integration/health')
        const healthData = await response.json()
        setSystemHealth(healthData)
      } catch (error) {
        console.error('Failed to fetch system health:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchSystemHealth()

    // 定期更新系統健康狀態
    const healthInterval = setInterval(fetchSystemHealth, 30000)

    return () => {
      bridge.off('service_status_changed', handleStatusChange)
      clearInterval(healthInterval)
    }
  }, [])

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">正在初始化整合服務...</p>
          </div>
        </div>
      )
    }

    switch (activeTab) {
      case 'dashboard':
        return <DashboardOverview systemHealth={systemHealth} />
      case 'chat':
        return <UnifiedAIChat />
      case 'image':
        return <UnifiedImageGeneration />
      case 'search':
        return <UnifiedWebSearch />
      case 'code':
        return <UnifiedCodeAnalysis />
      case 'agents':
        return <UnifiedAIAgents />
      case 'neural':
        return <UnifiedNeuralNetwork />
      case 'github':
        return <UnifiedGithubConnect />
      case 'monitor':
        return <UnifiedSystemMonitor systemHealth={systemHealth} />
      case 'analytics':
        return <UnifiedAnalyticsDashboard />
      case 'team':
        return <UnifiedTeamCollaboration />
      case 'settings':
        return <UnifiedSettings />
      default:
        return <DashboardOverview systemHealth={systemHealth} />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <UnifiedSidebar 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        systemHealth={systemHealth}
      />
      <main className="flex-1 overflow-auto">
        <div className="container mx-auto p-4 sm:p-6 lg:p-8">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}