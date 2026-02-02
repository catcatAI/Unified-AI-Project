'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Button } from '@acme/ui'
import { Progress } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
import { useNeuralNetworkModels, useModelMetrics, useModelTrainingStatus } from '@/hooks/use-api-data'
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
  RefreshCw,
  Loader2,
  AlertTriangle,
  Play,
  Pause,
  Settings,
  Clock,
  Database
} from 'lucide-react'

export function NeuralNetwork() {
  const { toast } = useToast()
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  
  // API hooks
  const { data: models, loading: modelsLoading, error: modelsError, refresh: refreshModels } = useNeuralNetworkModels()
  const { data: metrics, loading: metricsLoading, refresh: refreshMetrics } = useModelMetrics(selectedModel || '')
  const { data: trainingStatus, loading: trainingLoading, refresh: refreshTraining } = useModelTrainingStatus(selectedModel || '')
  
  // Mock data for fallback
  const mockNetworks = [
    {
      id: '1',
      name: 'Language Model',
      type: 'Transformer',
      status: 'training',
      accuracy: 94.2,
      loss: 0.058,
      epochs: 100,
      current_epoch: 67,
      layers: 12,
      parameters: 768000000,
      created_at: new Date(Date.now() - 86400000).toISOString(),
      updated_at: new Date(Date.now() - 300000).toISOString()
    },
    {
      id: '2',
      name: 'Image Classifier',
      type: 'CNN',
      status: 'idle',
      accuracy: 98.1,
      loss: 0.023,
      epochs: 50,
      current_epoch: 50,
      layers: 8,
      parameters: 25600000,
      created_at: new Date(Date.now() - 172800000).toISOString(),
      updated_at: new Date(Date.now() - 1800000).toISOString()
    },
    {
      id: '3',
      name: 'Code Analyzer',
      type: 'LSTM',
      status: 'processing',
      accuracy: 87.5,
      loss: 0.142,
      epochs: 75,
      current_epoch: 42,
      layers: 6,
      parameters: 12800000,
      created_at: new Date(Date.now() - 259200000).toISOString(),
      updated_at: new Date(Date.now() - 120000).toISOString()
    },
    {
      id: '4',
      name: 'Sentiment Analysis',
      type: 'BERT',
      status: 'idle',
      accuracy: 91.8,
      loss: 0.089,
      epochs: 30,
      current_epoch: 30,
      layers: 4,
      parameters: 6400000,
      created_at: new Date(Date.now() - 345600000).toISOString(),
      updated_at: new Date(Date.now() - 3600000).toISOString()
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

  const formatTime = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
    return `${Math.floor(minutes / 1440)}d ago`
  }
  
  const formatParameters = (params: number) => {
    if (params >= 1000000000) return `${(params / 1000000000).toFixed(1)}B`
    if (params >= 1000000) return `${(params / 1000000).toFixed(1)}M`
    if (params >= 1000) return `${(params / 1000).toFixed(1)}K`
    return params.toString()
  }
  
  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId)
    refreshMetrics()
    refreshTraining()
  }
  
  const handleRefreshAll = () => {
    refreshModels()
    if (selectedModel) {
      refreshMetrics()
      refreshTraining()
    }
  }
  
  // Use real data when available, fallback to mock data
  const currentNetworks = models || mockNetworks
  const averageAccuracy = currentNetworks.reduce((sum, net) => sum + net.accuracy, 0) / currentNetworks.length
  const trainingNetworks = currentNetworks.filter(net => net.status === 'training').length

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
            {currentNetworks.length} models
          </Badge>
          <Badge variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            {trainingNetworks} training
          </Badge>
          <Button variant="outline" size="sm" onClick={handleRefreshAll} disabled={modelsLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${modelsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>
      
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="training">Training</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">

          {/* Stats Overview */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Models</CardTitle>
                <Network className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentNetworks.length}</div>
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
                <CardTitle className="text-sm font-medium">Total Parameters</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatParameters(currentNetworks.reduce((sum, net) => sum + net.parameters, 0))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Combined parameters
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="models" className="space-y-4">

          {modelsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading models...</span>
            </div>
          ) : modelsError ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Failed to load models</h3>
              <p className="text-muted-foreground mb-4">{modelsError}</p>
              <Button onClick={refreshModels}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {currentNetworks.map((network) => (
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
                        <div className="text-lg font-bold">{formatParameters(network.parameters)}</div>
                        <div className="text-xs text-muted-foreground">Parameters</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold">{network.current_epoch}/{network.epochs}</div>
                        <div className="text-xs text-muted-foreground">Epochs</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Updated: {formatTime(network.updated_at)}</span>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleModelSelect(network.id)}
                        >
                          <BarChart3 className="mr-1 h-3 w-3" />
                          Details
                        </Button>
                        <Button variant="outline" size="sm">
                          <Settings className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    
                    {network.status === 'training' && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Training Progress</span>
                          <span>{Math.round((network.current_epoch / network.epochs) * 100)}%</span>
                        </div>
                        <Progress value={(network.current_epoch / network.epochs) * 100} className="h-2" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="metrics" className="space-y-4">
          {!selectedModel ? (
            <div className="text-center py-12">
              <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Select a Model</h3>
              <p className="text-muted-foreground">
                Choose a model from the Models tab to view detailed metrics
              </p>
            </div>
          ) : metricsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading metrics...</span>
            </div>
          ) : metrics ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                  <CardDescription>Current model performance indicators</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-2xl font-bold text-green-600">{metrics.accuracy}%</div>
                      <div className="text-sm text-muted-foreground">Accuracy</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.loss.toFixed(4)}</div>
                      <div className="text-sm text-muted-foreground">Loss</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.precision}%</div>
                      <div className="text-sm text-muted-foreground">Precision</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.recall}%</div>
                      <div className="text-sm text-muted-foreground">Recall</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Training Statistics</CardTitle>
                  <CardDescription>Training progress and statistics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-2xl font-bold">{metrics.epochs_completed}</div>
                      <div className="text-sm text-muted-foreground">Epochs Completed</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.training_time}h</div>
                      <div className="text-sm text-muted-foreground">Training Time</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.learning_rate}</div>
                      <div className="text-sm text-muted-foreground">Learning Rate</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{metrics.batch_size}</div>
                      <div className="text-sm text-muted-foreground">Batch Size</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No metrics available</h3>
              <p className="text-muted-foreground">
                Metrics data is not available for this model
              </p>
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="training" className="space-y-4">
          {!selectedModel ? (
            <div className="text-center py-12">
              <Activity className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Select a Model</h3>
              <p className="text-muted-foreground">
                Choose a model from the Models tab to view training status
              </p>
            </div>
          ) : trainingLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading training status...</span>
            </div>
          ) : trainingStatus ? (
            <div className="grid gap-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Training Status</CardTitle>
                      <CardDescription>Current training progress and controls</CardDescription>
                    </div>
                    <Badge variant={getStatusColor(trainingStatus.status)} className="flex items-center gap-1">
                      {getStatusIcon(trainingStatus.status)}
                      {trainingStatus.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-2xl font-bold">{trainingStatus.current_epoch}</div>
                      <div className="text-sm text-muted-foreground">Current Epoch</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{trainingStatus.total_epochs}</div>
                      <div className="text-sm text-muted-foreground">Total Epochs</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{trainingStatus.progress}%</div>
                      <div className="text-sm text-muted-foreground">Progress</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{trainingStatus.eta}</div>
                      <div className="text-sm text-muted-foreground">ETA</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Training Progress</span>
                      <span>{trainingStatus.progress}%</span>
                    </div>
                    <Progress value={trainingStatus.progress} className="h-3" />
                  </div>
                  
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Play className="mr-2 h-4 w-4" />
                      Start
                    </Button>
                    <Button variant="outline" size="sm">
                      <Pause className="mr-2 h-4 w-4" />
                      Pause
                    </Button>
                    <Button variant="outline" size="sm">
                      <Settings className="mr-2 h-4 w-4" />
                      Configure
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No training data available</h3>
              <p className="text-muted-foreground">
                Training status is not available for this model
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}