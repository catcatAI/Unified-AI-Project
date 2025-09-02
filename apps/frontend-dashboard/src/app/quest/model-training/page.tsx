import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Button } from '@acme/ui';
import { Input } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Progress } from '@acme/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  FileText, 
  BarChart3, 
  Settings,
  Upload,
  Download,
  Eye,
  Zap,
  Cpu,
  Database
} from 'lucide-react';

interface Model {
  id: string;
  name: string;
  version: string;
  status: 'training' | 'completed' | 'paused' | 'error';
  progress: number;
  accuracy: number;
  loss: number;
  epochs: number;
  lastUpdated: string;
}

interface TrainingJob {
  id: string;
  modelName: string;
  status: 'running' | 'completed' | 'queued' | 'failed';
  progress: number;
  startTime: string;
  estimatedEndTime: string;
  resources: {
    cpu: number;
    memory: number;
    gpu?: number;
  };
}

export function ModelTraining() {
  const [models, setModels] = useState<Model[]>([
    {
      id: '1',
      name: 'GPT-4 Architecture',
      version: 'v2.1.0',
      status: 'completed',
      progress: 100,
      accuracy: 94.2,
      loss: 0.023,
      epochs: 50,
      lastUpdated: '2023-06-15T14:30:00Z'
    },
    {
      id: '2',
      name: 'Vision Transformer',
      version: 'v1.5.3',
      status: 'training',
      progress: 67,
      accuracy: 87.5,
      loss: 0.156,
      epochs: 35,
      lastUpdated: '2023-06-16T09:15:00Z'
    },
    {
      id: '3',
      name: 'Speech Recognition',
      version: 'v3.0.1',
      status: 'paused',
      progress: 42,
      accuracy: 91.8,
      loss: 0.089,
      epochs: 21,
      lastUpdated: '2023-06-16T08:45:00Z'
    }
  ]);

  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([
    {
      id: 'job_1',
      modelName: 'Vision Transformer',
      status: 'running',
      progress: 67,
      startTime: '2023-06-16T08:00:00Z',
      estimatedEndTime: '2023-06-16T14:30:00Z',
      resources: {
        cpu: 75,
        memory: 62,
        gpu: 85
      }
    },
    {
      id: 'job_2',
      modelName: 'Recommendation Engine',
      status: 'queued',
      progress: 0,
      startTime: '',
      estimatedEndTime: '2023-06-16T15:00:00Z',
      resources: {
        cpu: 0,
        memory: 0
      }
    }
  ]);

  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [isTraining, setIsTraining] = useState(false);

  const handleStartTraining = (modelId: string) => {
    setModels(models.map(model => 
      model.id === modelId ? {...model, status: 'training', progress: 0} : model
    ));
    setIsTraining(true);
  };

  const handlePauseTraining = (modelId: string) => {
    setModels(models.map(model => 
      model.id === modelId ? {...model, status: 'paused'} : model
    ));
    setIsTraining(false);
  };

  const handleStopTraining = (modelId: string) => {
    setModels(models.map(model => 
      model.id === modelId ? {...model, status: 'completed', progress: 100} : model
    ));
    setIsTraining(false);
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'training':
      case 'running':
        return 'default';
      case 'completed':
        return 'outline';
      case 'paused':
        return 'secondary';
      case 'error':
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'training':
        return '訓練中';
      case 'completed':
        return '已完成';
      case 'paused':
        return '已暫停';
      case 'error':
        return '錯誤';
      case 'running':
        return '運行中';
      case 'queued':
        return '排隊中';
      case 'failed':
        return '失敗';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">模型訓練管理</h1>
        <p className="text-muted-foreground">管理AI模型的訓練過程和資源分配</p>
      </div>

      <Tabs defaultValue="models" className="space-y-4">
        <TabsList>
          <TabsTrigger value="models">模型管理</TabsTrigger>
          <TabsTrigger value="training">訓練任務</TabsTrigger>
          <TabsTrigger value="resources">資源監控</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                模型列表
              </CardTitle>
              <CardDescription>
                查看和管理所有AI模型
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {models.map((model) => (
                  <div key={model.id} className="p-4 border border-border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-medium">{model.name}</h3>
                        <p className="text-sm text-muted-foreground">版本: {model.version}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={getStatusVariant(model.status)}>
                          {getStatusText(model.status)}
                        </Badge>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSelectedModel(model.id)}
                        >
                          <Settings className="h-4 w-4 mr-1" />
                          配置
                        </Button>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                      <div>
                        <p className="text-sm text-muted-foreground">準確率</p>
                        <p className="font-medium">{model.accuracy}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">損失值</p>
                        <p className="font-medium">{model.loss}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">訓練週期</p>
                        <p className="font-medium">{model.epochs}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">最後更新</p>
                        <p className="font-medium">{new Date(model.lastUpdated).toLocaleDateString()}</p>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>訓練進度</span>
                        <span>{model.progress}%</span>
                      </div>
                      <Progress value={model.progress} />
                    </div>
                    
                    <div className="flex gap-2 mt-3">
                      {model.status === 'training' ? (
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handlePauseTraining(model.id)}
                        >
                          <Pause className="h-4 w-4 mr-1" />
                          暫停
                        </Button>
                      ) : (
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleStartTraining(model.id)}
                          disabled={model.status === 'completed'}
                        >
                          <Play className="h-4 w-4 mr-1" />
                          開始訓練
                        </Button>
                      )}
                      <Button 
                        variant="outline" 
                        size="sm"
                        disabled={model.status !== 'training' && model.status !== 'paused'}
                      >
                        <Square className="h-4 w-4 mr-1" />
                        停止
                      </Button>
                      <Button variant="outline" size="sm">
                        <RotateCcw className="h-4 w-4 mr-1" />
                        重新訓練
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="training" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                訓練任務
              </CardTitle>
              <CardDescription>
                監控當前和排隊中的訓練任務
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trainingJobs.map((job) => (
                  <div key={job.id} className="p-4 border border-border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-medium">{job.modelName}</h3>
                        <p className="text-sm text-muted-foreground">
                          {job.startTime && `開始時間: ${new Date(job.startTime).toLocaleString()}`}
                        </p>
                      </div>
                      <Badge variant={getStatusVariant(job.status)}>
                        {getStatusText(job.status)}
                      </Badge>
                    </div>
                    
                    {job.status !== 'queued' && (
                      <>
                        <div className="space-y-2 mb-3">
                          <div className="flex justify-between text-sm">
                            <span>任務進度</span>
                            <span>{job.progress}%</span>
                          </div>
                          <Progress value={job.progress} />
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                          <div>
                            <p className="text-sm text-muted-foreground">CPU 使用率</p>
                            <div className="flex items-center gap-2">
                              <Cpu className="h-4 w-4" />
                              <span className="font-medium">{job.resources.cpu}%</span>
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">記憶體使用率</p>
                            <div className="flex items-center gap-2">
                              <Database className="h-4 w-4" />
                              <span className="font-medium">{job.resources.memory}%</span>
                            </div>
                          </div>
                          {job.resources.gpu !== undefined && (
                            <div>
                              <p className="text-sm text-muted-foreground">GPU 使用率</p>
                              <div className="flex items-center gap-2">
                                <Zap className="h-4 w-4" />
                                <span className="font-medium">{job.resources.gpu}%</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                    
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-1" />
                        詳細資訊
                      </Button>
                      {job.status === 'running' && (
                        <Button variant="outline" size="sm">
                          <Pause className="h-4 w-4 mr-1" />
                          暫停
                        </Button>
                      )}
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-1" />
                        下載模型
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  計算資源
                </CardTitle>
                <CardDescription>
                  系統計算資源使用情況
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>CPU 使用率</span>
                    <span>67%</span>
                  </div>
                  <Progress value={67} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>記憶體使用率</span>
                    <span>54%</span>
                  </div>
                  <Progress value={54} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>GPU 使用率</span>
                    <span>78%</span>
                  </div>
                  <Progress value={78} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>儲存空間</span>
                    <span>32%</span>
                  </div>
                  <Progress value={32} />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  訓練統計
                </CardTitle>
                <CardDescription>
                  模型訓練統計資訊
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>總訓練任務數</span>
                    <span className="font-medium">24</span>
                  </div>
                  <div className="flex justify-between">
                    <span>已完成任務</span>
                    <span className="font-medium">18</span>
                  </div>
                  <div className="flex justify-between">
                    <span>平均訓練時間</span>
                    <span className="font-medium">4.2 小時</span>
                  </div>
                  <div className="flex justify-between">
                    <span>最高準確率</span>
                    <span className="font-medium">96.8%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>總訓練週期</span>
                    <span className="font-medium">1,247</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                訓練配置
              </CardTitle>
              <CardDescription>
                配置模型訓練參數
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">批次大小</label>
                  <Input type="number" defaultValue="32" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">學習率</label>
                  <Input type="number" defaultValue="0.001" step="0.0001" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">訓練週期</label>
                  <Input type="number" defaultValue="100" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">驗證分割</label>
                  <Input type="number" defaultValue="0.2" step="0.05" />
                </div>
              </div>
              
              <div className="flex gap-2 mt-4">
                <Button>
                  <Upload className="h-4 w-4 mr-1" />
                  上傳數據集
                </Button>
                <Button variant="outline">
                  保存配置
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}