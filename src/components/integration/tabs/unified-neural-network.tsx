'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Brain, 
  Activity, 
  Zap,
  TrendingUp,
  Cpu,
  Database,
  BarChart3
} from 'lucide-react'

interface ModelStatus {
  id: string
  name: string
  status: 'training' | 'ready' | 'error' | 'paused'
  progress: number
  accuracy: number
  loss: number
  epochs: number
  total_epochs: number
  last_updated: string
}

const mockModels: ModelStatus[] = [
  {
    id: '1',
    name: 'GPT-4 微調模型',
    status: 'training',
    progress: 75,
    accuracy: 92.3,
    loss: 0.18,
    epochs: 15,
    total_epochs: 20,
    last_updated: '2 分鐘前'
  },
  {
    id: '2',
    name: '代碼理解模型',
    status: 'ready',
    progress: 100,
    accuracy: 88.7,
    loss: 0.23,
    epochs: 30,
    total_epochs: 30,
    last_updated: '1 小時前'
  },
  {
    id: '3',
    name: '圖像分類模型',
    status: 'paused',
    progress: 45,
    accuracy: 85.1,
    loss: 0.31,
    epochs: 9,
    total_epochs: 20,
    last_updated: '30 分鐘前'
  }
]

export function UnifiedNeuralNetwork() {
  const [models] = useState<ModelStatus[]>(mockModels)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'training': return <Zap className="h-4 w-4 text-blue-500 animate-pulse" />
      case 'ready': return <Activity className="h-4 w-4 text-green-500" />
      case 'error': return <Activity className="h-4 w-4 text-red-500" />
      case 'paused': return <Activity className="h-4 w-4 text-yellow-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'training': return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'ready': return 'text-green-600 bg-green-50 border-green-200'
      case 'error': return 'text-red-600 bg-red-50 border-red-200'
      case 'paused': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'training': return '訓練中'
      case 'ready': return '就緒'
      case 'error': return '錯誤'
      case 'paused': return '暫停'
      default: return '未知'
    }
  }

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 90) return 'text-green-600'
    if (accuracy >= 80) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getOverallStats = () => {
    const totalModels = models.length
    const readyModels = models.filter(m => m.status === 'ready').length
    const trainingModels = models.filter(m => m.status === 'training').length
    const avgAccuracy = models.reduce((sum, m) => sum + m.accuracy, 0) / models.length

    return {
      totalModels,
      readyModels,
      trainingModels,
      avgAccuracy: Math.round(avgAccuracy * 10) / 10
    }
  }

  const stats = getOverallStats()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">神經網絡</h1>
          <p className="text-muted-foreground">
            模型訓練與性能監控
          </p>
        </div>
        
        <Badge variant="outline" className="text-lg px-3 py-1">
          模型: {stats.totalModels}
        </Badge>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總模型數</CardTitle>
            <Brain className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalModels}</div>
            <p className="text-xs text-muted-foreground">
              已部署模型
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">就緒模型</CardTitle>
            <Activity className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.readyModels}</div>
            <p className="text-xs text-muted-foreground">
              可用於推理
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">訓練中</CardTitle>
            <Zap className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.trainingModels}</div>
            <p className="text-xs text-muted-foreground">
              正在訓練
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均準確率</CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getAccuracyColor(stats.avgAccuracy)}`}>
              {stats.avgAccuracy}%
            </div>
            <p className="text-xs text-muted-foreground">
              所有模型平均
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Models Grid */}
      <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
        {models.map((model) => (
          <Card key={model.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  <CardTitle className="text-lg">{model.name}</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(model.status)}
                  <Badge variant="outline" className={getStatusColor(model.status)}>
                    {getStatusText(model.status)}
                  </Badge>
                </div>
              </div>
              <CardDescription>
                最後更新: {model.last_updated}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Training Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>訓練進度</span>
                  <span className="font-medium">{model.progress}%</span>
                </div>
                <Progress value={model.progress} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Epoch {model.epochs}/{model.total_epochs}</span>
                  <span>{model.status === 'training' ? '訓練中...' : '已完成'}</span>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>準確率</span>
                    <span className={`font-medium ${getAccuracyColor(model.accuracy)}`}>
                      {model.accuracy}%
                    </span>
                  </div>
                  <Progress value={model.accuracy} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>損失值</span>
                    <span className="font-medium">{model.loss}</span>
                  </div>
                  <Progress value={Math.max(0, 100 - model.loss * 100)} className="h-2" />
                </div>
              </div>

              {/* Resource Usage */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 bg-muted rounded">
                  <Cpu className="h-4 w-4 mx-auto mb-1" />
                  <div className="text-xs font-medium">CPU</div>
                  <div className="text-xs text-muted-foreground">45%</div>
                </div>
                <div className="p-2 bg-muted rounded">
                  <Database className="h-4 w-4 mx-auto mb-1" />
                  <div className="text-xs font-medium">內存</div>
                  <div className="text-xs text-muted-foreground">2.3GB</div>
                </div>
                <div className="p-2 bg-muted rounded">
                  <BarChart3 className="h-4 w-4 mx-auto mb-1" />
                  <div className="text-xs font-medium">GPU</div>
                  <div className="text-xs text-muted-foreground">78%</div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Activity className="h-4 w-4 mr-1" />
                  監控
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  <BarChart3 className="h-4 w-4 mr-1" />
                  詳情
                </Button>
                {model.status === 'paused' && (
                  <Button variant="outline" size="sm">
                    <Zap className="h-4 w-4 mr-1" />
                    繼續
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}