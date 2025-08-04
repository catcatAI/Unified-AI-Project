'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Button } from '@acme/ui'
import { 
  Bot, 
  Activity, 
  Clock, 
  CheckCircle,
  AlertTriangle,
  Pause,
  Play,
  Settings,
  Brain,
  MessageSquare,
  Image,
  Search,
  Code,
  Database
} from 'lucide-react'

interface Agent {
  id: string
  name: string
  type: string
  status: 'online' | 'offline' | 'busy' | 'error'
  description: string
  capabilities: string[]
  lastActive: Date
  tasksCompleted: number
  icon: any
}

export function AIAgents() {
  const agents: Agent[] = [
    {
      id: '1',
      name: 'Chat Agent',
      type: 'Conversational AI',
      status: 'online',
      description: 'Handles natural language conversations and user interactions',
      capabilities: ['Natural Language Processing', 'Context Management', 'Multi-turn Dialog'],
      lastActive: new Date(Date.now() - 300000),
      tasksCompleted: 1247,
      icon: MessageSquare
    },
    {
      id: '2',
      name: 'Image Generator',
      type: 'Creative AI',
      status: 'busy',
      description: 'Generates images from text descriptions using diffusion models',
      capabilities: ['Image Generation', 'Style Transfer', 'Image Editing'],
      lastActive: new Date(Date.now() - 120000),
      tasksCompleted: 856,
      icon: Image
    },
    {
      id: '3',
      name: 'Web Search Agent',
      type: 'Information Retrieval',
      status: 'online',
      description: 'Performs web searches and information extraction',
      capabilities: ['Web Search', 'Information Extraction', 'Content Analysis'],
      lastActive: new Date(Date.now() - 180000),
      tasksCompleted: 623,
      icon: Search
    },
    {
      id: '4',
      name: 'Code Analyzer',
      type: 'Development AI',
      status: 'online',
      description: 'Analyzes code quality and provides optimization suggestions',
      capabilities: ['Code Analysis', 'Bug Detection', 'Performance Optimization'],
      lastActive: new Date(Date.now() - 240000),
      tasksCompleted: 445,
      icon: Code
    },
    {
      id: '5',
      name: 'Data Processor',
      type: 'Analytics AI',
      status: 'offline',
      description: 'Processes and analyzes large datasets',
      capabilities: ['Data Processing', 'Statistical Analysis', 'Visualization'],
      lastActive: new Date(Date.now() - 3600000),
      tasksCompleted: 234,
      icon: Database
    },
    {
      id: '6',
      name: 'Neural Network Core',
      type: 'Core AI',
      status: 'online',
      description: 'Central neural network processing unit',
      capabilities: ['Deep Learning', 'Pattern Recognition', 'Model Training'],
      lastActive: new Date(Date.now() - 60000),
      tasksCompleted: 3421,
      icon: Brain
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'default'
      case 'busy':
        return 'secondary'
      case 'offline':
        return 'outline'
      case 'error':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-3 w-3" />
      case 'busy':
        return <Clock className="h-3 w-3" />
      case 'offline':
        return <Pause className="h-3 w-3" />
      case 'error':
        return <AlertTriangle className="h-3 w-3" />
      default:
        return <Activity className="h-3 w-3" />
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
    return `${Math.floor(minutes / 1440)}d ago`
  }

  const totalTasks = agents.reduce((sum, agent) => sum + agent.tasksCompleted, 0)
  const onlineAgents = agents.filter(agent => agent.status === 'online' || agent.status === 'busy').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Agents</h1>
          <p className="text-muted-foreground">
            Manage and monitor specialized AI agents
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">
            <Bot className="mr-2 h-4 w-4" />
            {agents.length} agents
          </Badge>
          <Badge variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            {onlineAgents} online
          </Badge>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
            <p className="text-xs text-muted-foreground">
              {onlineAgents} currently active
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTasks.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Across all agents
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">98%</div>
            <p className="text-xs text-muted-foreground">
              Overall system uptime
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Agents Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => {
          const Icon = agent.icon
          return (
            <Card key={agent.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                  </div>
                  <Badge variant={getStatusColor(agent.status)} className="flex items-center gap-1">
                    {getStatusIcon(agent.status)}
                    {agent.status}
                  </Badge>
                </div>
                <CardDescription>{agent.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">Capabilities</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.map((capability, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {capability}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-muted-foreground">Tasks: </span>
                    <span className="font-medium">{agent.tasksCompleted}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last: </span>
                    <span className="font-medium">{formatTime(agent.lastActive)}</span>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Settings className="mr-1 h-3 w-3" />
                    Configure
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={agent.status === 'online' || agent.status === 'busy'}
                  >
                    <Play className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}