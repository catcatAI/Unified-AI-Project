'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Brain, 
  Activity, 
  Zap, 
  Layers,
  Target,
  TrendingUp,
  Network,
  Cpu,
  BarChart3,
  RefreshCw
} from 'lucide-react'

interface NeuralNetwork {
  id: string
  name: string
  type: string
  status: 'training' | 'idle' | 'processing' | 'error'
  accuracy: number
  loss: number
  epochs: number
  currentEpoch: number
  layers: number
  neurons: number
  lastUpdated: Date
}

export function NeuralNetwork() {
  const networks: NeuralNetwork[] = [
    {
      id: '1',
      name: 'Language Model',
      type: 'Transformer',
      status: 'training',
      accuracy: 94.2,
      loss: 0.058,
      epochs: 100,
      currentEpoch: 67,
      layers: 12,
      neurons: 768,
      lastUpdated: new Date(Date.now() - 300000)
    },
    {
      id: '2',
      name: 'Image Classifier',
      type: 'CNN',
      status: 'idle',
      accuracy: 98.1,
      loss: 0.023,
      epochs: 50,
      currentEpoch: 50,
      layers: 8,
      neurons: 512,
      lastUpdated: new Date(Date.now() - 1800000)
    },
    {
      id: '3',
      name: 'Code Analyzer',
      type: 'LSTM',
      status: 'processing',
      accuracy: 87.5,
      loss: 0.142,
      epochs: 75,
      currentEpoch: 42,
      layers: 6,
      neurons: 256,
      lastUpdated: new Date(Date.now() - 120000)
    },
    {
      id: '4',
      name: 'Sentiment Analysis',
      type: 'BERT',
      status: 'idle',
      accuracy: 91.8,
      loss: 0.089,
      epochs: 30,
      currentEpoch: 30,
      layers: 4,
      neurons: 128,
      lastUpdated: new Date(Date.now() - 3600000)
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'training':
        return 'default'
      case 'processing':
        return 'secondary'
      case 'idle':
        return 'outline'
      case 'error':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'training':
        return <RefreshCw className="h-3 w-3 animate-spin" />
      case 'processing':
        return <Activity className="h-3 w-3" />
      case 'idle':
        return <Brain className="h-3 w-3" />
      case 'error':
        return <Zap className="h-3 w-3" />
      default:
        return <Brain className="h-3 w-3" />
    }
  }

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 95) return 'text-green-600'
    if (accuracy >= 85) return 'text-yellow-600'
    return 'text-red-600'
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

  const averageAccuracy = networks.reduce((sum, net) => sum + net.accuracy, 0) / networks.length
  const trainingNetworks = networks.filter(net => net.status === 'training').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Neural Networks</h1>
          <p className="text-muted-foreground">
            Monitor and manage neural network models
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">
            <Brain className="mr-2 h-4 w-4" />
            {networks.length} models
          </Badge>
          <Badge variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            {trainingNetworks} training
          </Badge>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Models</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{networks.length}</div>
            <p className="text-xs text-muted-foreground">
              Neural networks
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Accuracy</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getAccuracyColor(averageAccuracy)}`}>
              {averageAccuracy.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Across all models
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Training</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{trainingNetworks}</div>
            <p className="text-xs text-muted-foreground">
              Currently training
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Layers</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {networks.reduce((sum, net) => sum + net.layers, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Combined layers
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Networks Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {networks.map((network) => (
          <Card key={network.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{network.name}</CardTitle>
                  <CardDescription>{network.type} Network</CardDescription>
                </div>
                <Badge variant={getStatusColor(network.status)} className="flex items-center gap-1">
                  {getStatusIcon(network.status)}
                  {network.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">Accuracy</span>
                    <span className={`text-sm font-bold ${getAccuracyColor(network.accuracy)}`}>
                      {network.accuracy}%
                    </span>
                  </div>
                  <Progress value={network.accuracy} className="h-2" />
                </div>
                
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">Loss</span>
                    <span className="text-sm font-bold">
                      {network.loss.toFixed(3)}
                    </span>
                  </div>
                  <Progress value={(1 - network.loss) * 100} className="h-2" />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-lg font-bold">{network.layers}</div>
                  <div className="text-xs text-muted-foreground">Layers</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{network.neurons}</div>
                  <div className="text-xs text-muted-foreground">Neurons</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{network.currentEpoch}/{network.epochs}</div>
                  <div className="text-xs text-muted-foreground">Epochs</div>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Last updated: {formatTime(network.lastUpdated)}</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <BarChart3 className="mr-1 h-3 w-3" />
                    Stats
                  </Button>
                  <Button variant="outline" size="sm">
                    <Cpu className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              
              {network.status === 'training' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Training Progress</span>
                    <span>{Math.round((network.currentEpoch / network.epochs) * 100)}%</span>
                  </div>
                  <Progress value={(network.currentEpoch / network.epochs) * 100} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}