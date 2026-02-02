'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { ScrollArea } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
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
  AlertCircle,
  Settings,
  Bell,
  User,
  Moon,
  Sun,
  ChevronDown,
  Filter,
  BarChart3,
  Globe,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Archive,
  Play,
  Pause,
  Square,
  Eye
} from 'lucide-react'

export function EnhancedDashboard() {
  const { toast } = useToast()
  const [activeView, setActiveView] = useState('overview')
  const [darkMode, setDarkMode] = useState(false)
  const [notifications, setNotifications] = useState(3)
  const [searchTerm, setSearchTerm] = useState('')

  // Toggle dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  // Mock data for demonstration
  const stats = [
    {
      title: 'AI Models Active',
      value: '12',
      change: '+3',
      icon: Brain,
      description: 'Neural networks online'
    },
    {
      title: 'Tasks Completed',
      value: '2,458',
      change: '+342',
      icon: Activity,
      description: 'Last 24 hours'
    },
    {
      title: 'Active Agents',
      value: '18',
      change: '+5',
      icon: Bot,
      description: 'Specialized AI agents'
    },
    {
      title: 'API Requests',
      value: '89.4K',
      change: '+12.7K',
      icon: Zap,
      description: 'This month'
    }
  ]

  const systems = [
    {
      name: 'HAM Memory System',
      status: 'online',
      description: 'Hierarchical Abstract Memory',
      icon: Database,
      health: 98
    },
    {
      name: 'HSP Protocol',
      status: 'online',
      description: 'Heterogeneous Service Protocol',
      icon: Activity,
      health: 95
    },
    {
      name: 'Neural Network Core',
      status: 'online',
      description: 'Deep learning engine',
      icon: Brain,
      health: 92
    },
    {
      name: 'Agent Manager',
      status: 'online',
      description: 'Multi-agent coordination',
      icon: Bot,
      health: 97
    },
    {
      name: 'Project Coordinator',
      status: 'online',
      description: 'Task orchestration',
      icon: Cpu,
      health: 94
    },
    {
      name: 'Learning Manager',
      status: 'training',
      description: 'Self-improvement system',
      icon: TrendingUp,
      health: 88
    }
  ]

  const recentActivity = [
    {
      type: 'chat',
      message: 'AI Chat session completed',
      time: '2 minutes ago',
      icon: MessageSquare,
      user: 'John Doe'
    },
    {
      type: 'image',
      message: 'Image generated: "Abstract landscape"',
      time: '5 minutes ago',
      icon: Image,
      user: 'Jane Smith'
    },
    {
      type: 'search',
      message: 'Web search: "Latest AI developments"',
      time: '8 minutes ago',
      icon: Search,
      user: 'Alex Johnson'
    },
    {
      type: 'code',
      message: 'Code analysis: React optimization',
      time: '12 minutes ago',
      icon: Code,
      user: 'Sarah Wilson'
    }
  ]

  const quickActions = [
    { name: 'Start Chat', icon: MessageSquare, color: 'bg-blue-500' },
    { name: 'Generate Image', icon: Image, color: 'bg-purple-500' },
    { name: 'Web Search', icon: Search, color: 'bg-green-500' },
    { name: 'Analyze Code', icon: Code, color: 'bg-yellow-500' },
    { name: 'Train Model', icon: Brain, color: 'bg-red-500' },
    { name: 'Manage Agents', icon: Bot, color: 'bg-indigo-500' }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Unified Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive AI system overview and management
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
          
          {/* Notifications */}
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            {notifications > 0 && (
              <Badge className="absolute -top-1 -right-1 h-5 w-5 justify-center rounded-full p-0">
                {notifications}
              </Badge>
            )}
          </Button>
          
          {/* User Profile */}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-primary-foreground" />
              </div>
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index} className="hover:shadow-md transition-shadow">
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
            <CardTitle className="flex items-center justify-between">
              <span>System Components</span>
              <Button variant="ghost" size="sm">
                <Filter className="h-4 w-4 mr-1" />
                Filter
              </Button>
            </CardTitle>
            <CardDescription>
              Core AI systems and their current status
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {systems.map((system, index) => {
              const Icon = system.icon
              return (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-muted">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-medium">{system.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {system.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant={system.status === 'online' ? 'default' : 'secondary'}
                    >
                      {system.status}
                    </Badge>
                    <div className="text-sm text-muted-foreground">
                      {system.health}%
                    </div>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Recent Activity</span>
              <Button variant="ghost" size="sm">
                <BarChart3 className="h-4 w-4 mr-1" />
                View All
              </Button>
            </CardTitle>
            <CardDescription>
              Latest AI system interactions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ScrollArea className="h-80">
              {recentActivity.map((activity, index) => {
                const Icon = activity.icon
                return (
                  <div key={index} className="flex items-start space-x-3 mb-4 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="mt-0.5">
                      <div className="p-2 rounded-lg bg-muted">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.message}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-xs text-muted-foreground">
                          {activity.time}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          by {activity.user}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                )
              })}
            </ScrollArea>
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
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
            {quickActions.map((action, index) => {
              const Icon = action.icon
              return (
                <Button 
                  key={index} 
                  variant="outline" 
                  className="flex flex-col items-center justify-center h-24 hover:shadow-md transition-shadow"
                >
                  <div className={`p-2 rounded-full ${action.color} mb-2`}>
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <span className="text-sm">{action.name}</span>
                </Button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* System Controls */}
      <Card>
        <CardHeader>
          <CardTitle>System Controls</CardTitle>
          <CardDescription>
            Manage system operations and maintenance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button>
              <Play className="h-4 w-4 mr-2" />
              Start All Services
            </Button>
            <Button variant="outline">
              <Pause className="h-4 w-4 mr-2" />
              Pause Services
            </Button>
            <Button variant="outline">
              <Square className="h-4 w-4 mr-2" />
              Stop Services
            </Button>
            <Button variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Restart System
            </Button>
            <Button variant="outline">
              <Archive className="h-4 w-4 mr-2" />
              Backup Data
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}