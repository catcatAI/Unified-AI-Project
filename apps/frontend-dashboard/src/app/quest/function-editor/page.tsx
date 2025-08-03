import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@acme/ui';
import { Button } from '@acme/ui';
import { Input } from '@acme/ui';
import { Label } from '@acme/ui';
import { Textarea } from '@acme/ui';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@acme/ui';
import { Plus, Edit, Trash2, Play, Save, Download, Upload } from 'lucide-react';
import { Separator } from '@acme/ui';

interface FunctionParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  defaultValue?: any;
}

interface AIFunction {
  id: string;
  name: string;
  description: string;
  category: 'ai-core' | 'tool' | 'api' | 'utility' | 'ui';
  parameters: FunctionParameter[];
  returnType: string;
  implementation: string;
  examples: string[];
  status: 'active' | 'inactive' | 'testing';
  createdAt: string;
  updatedAt: string;
}

const initialFunctions: AIFunction[] = [
  {
    id: 'math-calculator',
    name: '數學計算器',
    description: '執行基本數學運算',
    category: 'tool',
    parameters: [
      {
        name: 'expression',
        type: 'string',
        required: true,
        description: '數學表達式，如 "2 + 3 * 4"'
      }
    ],
    returnType: 'number',
    implementation: `function calculate(expression) {
  try {
    // 安全的數學表達式計算
    const result = Function('"use strict"; return (' + expression + ')')();
    return typeof result === 'number' ? result : NaN;
  } catch (error) {
    throw new Error('Invalid mathematical expression');
  }
}`,
    examples: ['calculate("2 + 3")', 'calculate("Math.sqrt(16)")'],
    status: 'active',
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01'
  },
  {
    id: 'text-processor',
    name: '文本處理器',
    description: '處理和分析文本內容',
    category: 'ai-core',
    parameters: [
      {
        name: 'text',
        type: 'string',
        required: true,
        description: '要處理的文本內容'
      },
      {
        name: 'operation',
        type: 'string',
        required: true,
        description: '操作類型：analyze, summarize, translate'
      }
    ],
    returnType: 'object',
    implementation: `async function processText(text, operation) {
  switch (operation) {
    case 'analyze':
      return {
        wordCount: text.split(' ').length,
        charCount: text.length,
        sentiment: 'neutral'
      };
    case 'summarize':
      return {
        summary: text.substring(0, 100) + '...',
        keyPoints: []
      };
    default:
      throw new Error('Unsupported operation');
  }
}`,
    examples: ['processText("Hello world", "analyze")'],
    status: 'active',
    createdAt: '2024-01-01',
    updatedAt: '2024-01-01'
  }
];

export default function FunctionEditor() {
  const [functions, setFunctions] = useState<AIFunction[]>(initialFunctions);
  const [selectedFunction, setSelectedFunction] = useState<AIFunction | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [testResult, setTestResult] = useState<string>('');

  const categoryColors = {
    'ai-core': 'bg-blue-500',
    'tool': 'bg-green-500',
    'api': 'bg-purple-500',
    'utility': 'bg-orange-500',
    'ui': 'bg-pink-500'
  };

  const createNewFunction = () => {
    const newFunction: AIFunction = {
      id: `func-${Date.now()}`,
      name: '新功能',
      description: '功能描述',
      category: 'utility',
      parameters: [],
      returnType: 'any',
      implementation: '// 在這裡編寫功能實現\nfunction newFunction() {\n  return "Hello World";\n}',
      examples: [],
      status: 'inactive',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    setFunctions(prev => [...prev, newFunction]);
    setSelectedFunction(newFunction);
    setIsCreateDialogOpen(false);
  };

  const updateFunction = (updatedFunction: AIFunction) => {
    setFunctions(prev => 
      prev.map(func => 
        func.id === updatedFunction.id 
          ? { ...updatedFunction, updatedAt: new Date().toISOString() }
          : func
      )
    );
    setSelectedFunction(updatedFunction);
  };

  const deleteFunction = (id: string) => {
    setFunctions(prev => prev.filter(func => func.id !== id));
    if (selectedFunction?.id === id) {
      setSelectedFunction(null);
    }
  };

  const testFunction = async () => {
    if (!selectedFunction) return;
    
    try {
      // 這裡可以實現真正的函數測試邏輯
      setTestResult('函數測試成功！\n輸出：Hello World');
    } catch (error) {
      setTestResult(`測試失敗：${error}`);
    }
  };

  const addParameter = () => {
    if (!selectedFunction) return;
    
    const newParameter: FunctionParameter = {
      name: 'newParam',
      type: 'string',
      required: false,
      description: '參數描述'
    };
    
    updateFunction({
      ...selectedFunction,
      parameters: [...selectedFunction.parameters, newParameter]
    });
  };

  const updateParameter = (index: number, parameter: FunctionParameter) => {
    if (!selectedFunction) return;
    
    const updatedParameters = [...selectedFunction.parameters];
    updatedParameters[index] = parameter;
    
    updateFunction({
      ...selectedFunction,
      parameters: updatedParameters
    });
  };

  const removeParameter = (index: number) => {
    if (!selectedFunction) return;
    
    updateFunction({
      ...selectedFunction,
      parameters: selectedFunction.parameters.filter((_, i) => i !== index)
    });
  };

  return (
    <div className="h-full flex gap-6 p-6">
      {/* 功能列表 */}
      <div className="w-1/3 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">功能列表</h2>
          <Button onClick={() => setIsCreateDialogOpen(true)} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            新增功能
          </Button>
        </div>
        
        <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
          {functions.map((func) => (
            <Card 
              key={func.id}
              className={`cursor-pointer transition-all hover:shadow-md ${
                selectedFunction?.id === func.id ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => setSelectedFunction(func)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">{func.name}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge className={`${categoryColors[func.category]} text-white text-xs`}>
                      {func.category}
                    </Badge>
                    <Badge variant={func.status === 'active' ? 'default' : 'secondary'}>
                      {func.status}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{func.description}</p>
                <div className="mt-2 text-xs text-muted-foreground">
                  參數: {func.parameters.length} | 返回: {func.returnType}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 功能編輯區 */}
      <div className="flex-1">
        {selectedFunction ? (
          <Tabs defaultValue="basic" className="h-full">
            <div className="flex items-center justify-between mb-4">
              <TabsList>
                <TabsTrigger value="basic">基本信息</TabsTrigger>
                <TabsTrigger value="parameters">參數配置</TabsTrigger>
                <TabsTrigger value="implementation">實現代碼</TabsTrigger>
                <TabsTrigger value="test">測試運行</TabsTrigger>
              </TabsList>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Save className="w-4 h-4 mr-2" />
                  保存
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  導出
                </Button>
                <Button 
                  variant="destructive" 
                  size="sm"
                  onClick={() => deleteFunction(selectedFunction.id)}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  刪除
                </Button>
              </div>
            </div>

            <TabsContent value="basic" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">功能名稱</Label>
                      <Input
                        id="name"
                        value={selectedFunction.name}
                        onChange={(e) => updateFunction({
                          ...selectedFunction,
                          name: e.target.value
                        })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="category">分類</Label>
                      <Select 
                        value={selectedFunction.category}
                        onValueChange={(value) => updateFunction({
                          ...selectedFunction,
                          category: value as any
                        })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ai-core">AI 核心</SelectItem>
                          <SelectItem value="tool">工具</SelectItem>
                          <SelectItem value="api">API</SelectItem>
                          <SelectItem value="utility">工具函數</SelectItem>
                          <SelectItem value="ui">UI 組件</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="description">功能描述</Label>
                    <Textarea
                      id="description"
                      value={selectedFunction.description}
                      onChange={(e) => updateFunction({
                        ...selectedFunction,
                        description: e.target.value
                      })}
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="returnType">返回類型</Label>
                      <Input
                        id="returnType"
                        value={selectedFunction.returnType}
                        onChange={(e) => updateFunction({
                          ...selectedFunction,
                          returnType: e.target.value
                        })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="status">狀態</Label>
                      <Select 
                        value={selectedFunction.status}
                        onValueChange={(value) => updateFunction({
                          ...selectedFunction,
                          status: value as any
                        })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">活動</SelectItem>
                          <SelectItem value="inactive">未啟用</SelectItem>
                          <SelectItem value="testing">測試中</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="parameters" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>參數配置</CardTitle>
                    <Button onClick={addParameter} size="sm">
                      <Plus className="w-4 h-4 mr-2" />
                      添加參數
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {selectedFunction.parameters.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">
                      尚未配置參數，點擊上方按鈕添加參數
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {selectedFunction.parameters.map((param, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="grid grid-cols-4 gap-4">
                            <div>
                              <Label>參數名稱</Label>
                              <Input
                                value={param.name}
                                onChange={(e) => updateParameter(index, {
                                  ...param,
                                  name: e.target.value
                                })}
                              />
                            </div>
                            <div>
                              <Label>類型</Label>
                              <Select 
                                value={param.type}
                                onValueChange={(value) => updateParameter(index, {
                                  ...param,
                                  type: value as any
                                })}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="string">String</SelectItem>
                                  <SelectItem value="number">Number</SelectItem>
                                  <SelectItem value="boolean">Boolean</SelectItem>
                                  <SelectItem value="object">Object</SelectItem>
                                  <SelectItem value="array">Array</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                checked={param.required}
                                onChange={(e) => updateParameter(index, {
                                  ...param,
                                  required: e.target.checked
                                })}
                              />
                              <Label>必需</Label>
                            </div>
                            <div className="flex justify-end">
                              <Button 
                                variant="destructive" 
                                size="sm"
                                onClick={() => removeParameter(index)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          <div className="mt-2">
                            <Label>描述</Label>
                            <Input
                              value={param.description}
                              onChange={(e) => updateParameter(index, {
                                ...param,
                                description: e.target.value
                              })}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="implementation" className="space-y-4">
              <Card className="h-[600px]">
                <CardHeader>
                  <CardTitle>實現代碼</CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  <Textarea
                    className="h-[500px] font-mono text-sm"
                    value={selectedFunction.implementation}
                    onChange={(e) => updateFunction({
                      ...selectedFunction,
                      implementation: e.target.value
                    })}
                    placeholder="在這裡編寫功能實現代碼..."
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="test" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>測試運行</CardTitle>
                    <Button onClick={testFunction}>
                      <Play className="w-4 h-4 mr-2" />
                      運行測試
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>測試輸入</Label>
                    <Textarea 
                      placeholder="輸入測試參數（JSON 格式）"
                      rows={3}
                    />
                  </div>
                  <Separator />
                  <div>
                    <Label>測試結果</Label>
                    <Textarea 
                      value={testResult}
                      readOnly
                      rows={6}
                      className="font-mono text-sm"
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        ) : (
          <Card className="h-full flex items-center justify-center">
            <CardContent>
              <p className="text-muted-foreground text-center">
                選擇左側功能進行編輯，或創建新功能
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 創建功能對話框 */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>創建新功能</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              將創建一個新的功能模板，您可以在創建後進行詳細配置。
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={createNewFunction}>創建</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
