'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Button } from '@acme/ui'
import { useSystemStatus, useHealthCheck } from '@/hooks/use-api-data'
import { 
  Activity, 
  Zap, 
  Brain, 
  Bot, 
  MessageSquare, 
  Image, 
  Search, 
  Code,
  TrendingUp,
  Users,
  Database,
  Cpu,
  RefreshCw,
  AlertCircle
} from 'lucide-react'

export function DashboardOverview() {
  const { data: systemStatus, loading: statusLoading, error: statusError, refresh } = useSystemStatus()
  const { isHealthy, loading: healthLoading } = useHealthCheck()

  // Use real data when available, fallback to mock data
  const stats = systemStatus && systemStatus.metrics ? [
    {
      title: 'AI Models Active',
      value: systemStatus.metrics.active_models?.toString() || '8',
      change: '+2',
      icon: Brain,
      description: 'Neural networks online'
    },
    {
      title: 'Tasks Completed',
      value: systemStatus.metrics.tasks_completed?.toLocaleString() || '1,247',
      change: '+127',
      icon: Activity,
      description: 'Last 24 hours'
    },
    {
      title: 'Active Agents',
      value: systemStatus.metrics.active_agents?.toString() || '12',
      change: '+3',
      icon: Bot,
      description: 'Specialized AI agents'
    },
    {
      title: 'API Requests',
      value: systemStatus.metrics.api_requests ? (systemStatus.metrics.api_requests / 1000).toFixed(1) + 'K' : '45.2K',
      change: '+5.2K',
      icon: Zap,
      description: 'This month'
    }
  ] : [
    {
      title: 'AI Models Active',
      value: '8',
      change: '+2',
      icon: Brain,
      description: 'Neural networks online'
    },
    {
      title: 'Tasks Completed',
      value: '1,247',
      change: '+127',
      icon: Activity,
      description: 'Last 24 hours'
    },
    {
      title: 'Active Agents',
      value: '12',
      change: '+3',
      icon: Bot,
      description: 'Specialized AI agents'
    },
    {
      title: 'API Requests',
      value: '45.2K',
      change: '+5.2K',
      icon: Zap,
      description: 'This month'
    }
  ]

  const systems = [
    {
      name: 'HAM Memory System',
      status: 'online',
      description: 'Hierarchical Abstract Memory',
      icon: Database
    },
    {
      name: 'HSP Protocol',
      status: 'online',
      description: 'Heterogeneous Service Protocol',
      icon: Activity
    },
    {
      name: 'Neural Network Core',
      status: 'online',
      description: 'Deep learning engine',
      icon: Brain
    },
    {
      name: 'Agent Manager',
      status: 'online',
      description: 'Multi-agent coordination',
      icon: Bot
    },
    {
      name: 'Project Coordinator',
      status: 'online',
      description: 'Task orchestration',
      icon: Cpu
    },
    {
      name: 'Learning Manager',
      status: 'training',
      description: 'Self-improvement system',
      icon: TrendingUp
    }
  ]

  const recentActivity = [
    {
      type: 'chat',
      message: 'AI Chat session completed',
      time: '2 minutes ago',
      icon: MessageSquare
    },
    {
      type: 'image',
      message: 'Image generated: "Abstract landscape"',
      time: '5 minutes ago',
      icon: Image
    },
    {
      type: 'search',
      message: 'Web search: "Latest AI developments"',
      time: '8 minutes ago',
      icon: Search
    },
    {
      type: 'code',
      message: 'Code analysis: React optimization',
      time: '12 minutes ago',
      icon: Code
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Unified Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive AI system overview and management
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Backend Status Indicator */}
          <div className="flex items-center gap-2">
            {healthLoading ? (
              <div className="h-2 w-2 bg-yellow-500 rounded-full animate-pulse" />
            ) : isHealthy ? (
              <div className="h-2 w-2 bg-green-500 rounded-full" />
            ) : (
              <div className="h-2 w-2 bg-red-500 rounded-full" />
            )}
            <span className="text-sm text-muted-foreground">
              {healthLoading ? 'Checking...' : isHealthy ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div>
          
          {/* Data Status Indicator */}
          <div className="flex items-center gap-2">
            {statusLoading ? (
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : statusError ? (
              <AlertCircle className="h-4 w-4 text-red-500" />
            ) : (
              <Activity className="h-4 w-4 text-green-500" />
            )}
            <span className="text-sm text-muted-foreground">
              {statusLoading ? 'Loading...' : statusError ? 'Using Mock Data' : 'Live Data'}
            </span>
          </div>
          
          {/* Refresh Button */}
          <Button variant="outline" size="sm" onClick={refresh} disabled={statusLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${statusLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-600">{stat.change}</span> {stat.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>System Components</CardTitle>
            <CardDescription>
              Core AI systems and their current status
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {systems.map((system) => {
              const Icon = system.icon
              return (
                <div key={system.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Icon className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{system.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {system.description}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant={system.status === 'online' ? 'default' : 'secondary'}
                  >
                    {system.status}
                  </Badge>
                </div>
              )
            })}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Latest AI system interactions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentActivity.map((activity) => {
              const Icon = activity.icon
              return (
                <div key={activity.time} className="flex items-center space-x-3">
                  <Icon className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1">
                    <p className="text-sm">{activity.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {activity.time}
                    </p>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common AI system operations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="justify-start">
              <MessageSquare className="mr-2 h-4 w-4" />
              Start Chat
            </Button>
            <Button variant="outline" className="justify-start">
              {/* eslint-disable-next-line jsx-a11y/alt-text */}
              <Image className="mr-2 h-4 w-4" />
              Generate Image
            </Button>
            <Button variant="outline" className="justify-start">
              <Search className="mr-2 h-4 w-4" />
              Web Search
            </Button>
            <Button variant="outline" className="justify-start">
              <Code className="mr-2 h-4 w-4" />
              Analyze Code
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}