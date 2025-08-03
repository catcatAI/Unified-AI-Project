import React, { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  addEdge,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Connection,
  Edge,
  Node,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { Button } from '@acme/ui';
import { Card, CardContent, CardHeader, CardTitle } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@acme/ui';
import { Input } from '@acme/ui';
import { Label } from '@acme/ui';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@acme/ui';
import { Textarea } from '@acme/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui';
import { Separator } from '@acme/ui';
import { Plus, Settings, Save, Download, Upload, Layers, Code, Cpu } from 'lucide-react';
import { ArchitectureStore, ArchitectureConfig, defaultComponentGroups, ComponentGroup } from '@/lib/architecture-store';

// 模組類型定義
interface ModuleData extends Record<string, unknown> {
  id: string;
  label: string;
  type: 'model' | 'tool' | 'core-ai' | 'service' | 'data-store' | 'interface';
  status: 'completed' | 'built-in' | 'downloadable' | 'in-progress';
  description: string;
  location?: string;
}

// 自定義節點組件
const ModuleNode: React.FC<{ data: ModuleData }> = ({ data }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'built-in': return 'bg-blue-500';
      case 'downloadable': return 'bg-orange-500';
      case 'in-progress': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'model': return '🤖';
      case 'tool': return '🔧';
      case 'core-ai': return '🧠';
      case 'service': return '⚙️';
      case 'data-store': return '💾';
      case 'interface': return '🖥️';
      default: return '📦';
    }
  };

  return (
    <Card className="min-w-[200px] shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{getTypeIcon(data.type)}</span>
          <CardTitle className="text-sm">{data.label}</CardTitle>
          <Badge className={`${getStatusColor(data.status)} text-white text-xs`}>
            {data.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground">{data.description}</p>
        {data.location && (
          <p className="text-xs text-blue-600 mt-1">{data.location}</p>
        )}
      </CardContent>
    </Card>
  );
};

// 初始節點數據
const initialNodes: Node[] = [
  // Models
  {
    id: 'math-model',
    type: 'module',
    position: { x: 100, y: 100 },
    data: {
      id: 'math-model',
      label: 'Math Model',
      type: 'model',
      status: 'built-in',
      description: 'Lightweight model for basic arithmetic problems',
      location: 'src/tools/math_model/'
    }
  },
  {
    id: 'logic-model',
    type: 'module',
    position: { x: 300, y: 100 },
    data: {
      id: 'logic-model',
      label: 'Logic Model',
      type: 'model',
      status: 'built-in',
      description: 'Lightweight model for basic logic problems',
      location: 'src/tools/logic_model/'
    }
  },
  {
    id: 'image-recognition-model',
    type: 'module',
    position: { x: 500, y: 100 },
    data: {
      id: 'image-recognition-model',
      label: 'Image Recognition Model',
      type: 'model',
      status: 'downloadable',
      description: 'Image recognition using template matching',
      location: 'src/tools/image_recognition_tool.py'
    }
  },
  // Tools
  {
    id: 'math-tool',
    type: 'module',
    position: { x: 100, y: 300 },
    data: {
      id: 'math-tool',
      label: 'Math Tool',
      type: 'tool',
      status: 'completed',
      description: 'Tool for basic arithmetic problems',
      location: 'src/tools/math_tool.py'
    }
  },
  {
    id: 'calculator-tool',
    type: 'module',
    position: { x: 300, y: 300 },
    data: {
      id: 'calculator-tool',
      label: 'Calculator Tool',
      type: 'tool',
      status: 'completed',
      description: 'Calculate mathematical expressions',
      location: 'src/tools/calculator_tool.py'
    }
  },
  // Core AI
  {
    id: 'dialogue-manager',
    type: 'module',
    position: { x: 100, y: 500 },
    data: {
      id: 'dialogue-manager',
      label: 'Dialogue Manager',
      type: 'core-ai',
      status: 'completed',
      description: 'Manages AI conversations and responses'
    }
  },
  {
    id: 'learning-manager',
    type: 'module',
    position: { x: 300, y: 500 },
    data: {
      id: 'learning-manager',
      label: 'Learning Manager',
      type: 'core-ai',
      status: 'completed',
      description: 'Handles learning and adaptation'
    }
  },
  {
    id: 'ham-memory',
    type: 'module',
    position: { x: 500, y: 500 },
    data: {
      id: 'ham-memory',
      label: 'HAM Memory Manager',
      type: 'core-ai',
      status: 'completed',
      description: 'Hierarchical memory management system'
    }
  },
  {
    id: 'tool-dispatcher',
    type: 'module',
    position: { x: 700, y: 500 },
    data: {
      id: 'tool-dispatcher',
      label: 'Tool Dispatcher',
      type: 'core-ai',
      status: 'completed',
      description: 'Routes and executes tool requests'
    }
  },
  // Services
  {
    id: 'main-api-server',
    type: 'module',
    position: { x: 100, y: 700 },
    data: {
      id: 'main-api-server',
      label: 'Main API Server',
      type: 'service',
      status: 'completed',
      description: 'FastAPI backend server'
    }
  },
  {
    id: 'llm-interface',
    type: 'module',
    position: { x: 300, y: 700 },
    data: {
      id: 'llm-interface',
      label: 'LLM Interface',
      type: 'service',
      status: 'completed',
      description: 'Interface to language models'
    }
  },
  // Interfaces
  {
    id: 'cli-interface',
    type: 'module',
    position: { x: 100, y: 900 },
    data: {
      id: 'cli-interface',
      label: 'CLI Interface',
      type: 'interface',
      status: 'completed',
      description: 'Command line interface'
    }
  },
  {
    id: 'electron-app',
    type: 'module',
    position: { x: 300, y: 900 },
    data: {
      id: 'electron-app',
      label: 'Electron App',
      type: 'interface',
      status: 'completed',
      description: 'Desktop application interface'
    }
  }
];

// 初始連接線
const initialEdges: Edge[] = [
  // Tools connect to models
  { id: 'e1', source: 'math-tool', target: 'math-model', type: 'smoothstep' },
  { id: 'e2', source: 'calculator-tool', target: 'math-model', type: 'smoothstep' },
  
  // Core AI connections
  { id: 'e3', source: 'dialogue-manager', target: 'learning-manager', type: 'smoothstep' },
  { id: 'e4', source: 'dialogue-manager', target: 'ham-memory', type: 'smoothstep' },
  { id: 'e5', source: 'dialogue-manager', target: 'tool-dispatcher', type: 'smoothstep' },
  { id: 'e6', source: 'tool-dispatcher', target: 'math-tool', type: 'smoothstep' },
  { id: 'e7', source: 'tool-dispatcher', target: 'calculator-tool', type: 'smoothstep' },
  
  // Services connect to core AI
  { id: 'e8', source: 'main-api-server', target: 'dialogue-manager', type: 'smoothstep' },
  { id: 'e9', source: 'llm-interface', target: 'dialogue-manager', type: 'smoothstep' },
  
  // Interfaces connect to services
  { id: 'e10', source: 'cli-interface', target: 'main-api-server', type: 'smoothstep' },
  { id: 'e11', source: 'electron-app', target: 'main-api-server', type: 'smoothstep' }
];

const nodeTypes: NodeTypes = {
  module: ModuleNode,
};

export default function ArchitectureEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [editingNode, setEditingNode] = useState<ModuleData | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [componentGroups, setComponentGroups] = useState<ComponentGroup[]>(defaultComponentGroups);
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [currentConfig, setCurrentConfig] = useState<ArchitectureConfig | null>(null);
  const [architectureStore] = useState(() => ArchitectureStore.getInstance());

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const addNewModule = () => {
    const newNode: Node = {
      id: `module-${Date.now()}`,
      type: 'module',
      position: { x: Math.random() * 500, y: Math.random() * 500 },
      data: {
        id: `module-${Date.now()}`,
        label: 'New Module',
        type: 'tool',
        status: 'in-progress',
        description: 'New module description'
      }
    };
    setNodes((nds) => [...nds, newNode]);
    setIsAddDialogOpen(false);
  };

  const editModule = (moduleData: ModuleData) => {
    setEditingNode(moduleData);
  };

  const saveModule = (updatedData: ModuleData) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === updatedData.id
          ? { ...node, data: updatedData }
          : node
      )
    );
    setEditingNode(null);
  };

  const saveArchitecture = async () => {
    try {
      const config: ArchitectureConfig = {
        id: currentConfig?.id || `arch-${Date.now()}`,
        name: currentConfig?.name || '新架構設計',
        version: '1.0.0',
        description: currentConfig?.description || '系統架構設計',
        nodes,
        edges,
        createdAt: currentConfig?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        metadata: {
          author: 'User',
          tags: ['unified-ai'],
          platform: 'web'
        }
      };
      
      await architectureStore.saveArchitecture(config);
      setCurrentConfig(config);
      console.log('架構已保存');
    } catch (error) {
      console.error('保存失敗:', error);
    }
  };

  const exportArchitecture = async () => {
    if (!currentConfig) {
      await saveArchitecture();
      return;
    }
    
    try {
      const blob = await architectureStore.exportArchitecture(currentConfig.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentConfig.name}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('導出失敗:', error);
    }
  };

  const importArchitecture = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    architectureStore.importArchitecture(file)
      .then(config => {
        setNodes(config.nodes);
        setEdges(config.edges);
        setCurrentConfig(config);
        console.log('架構已導入');
      })
      .catch(error => {
        console.error('導入失敗:', error);
      });
  };

  const filteredNodes = selectedGroup === 'all' 
    ? nodes 
    : nodes.filter(node => {
        const group = componentGroups.find(g => 
          g.components.includes(node.data.type as string) || 
          g.id === (node.data as any).category
        );
        return group?.id === selectedGroup;
      });

  return (
    <div className="h-full w-full flex">
      {/* 左側面板 - 組件分組 */}
      <div className="w-80 border-r bg-muted/30 flex flex-col">
        <div className="p-4 border-b">
          <h3 className="font-semibold mb-4">組件分組</h3>
          <div className="space-y-2">
            <Button
              variant={selectedGroup === 'all' ? 'default' : 'ghost'}
              className="w-full justify-start"
              onClick={() => setSelectedGroup('all')}
            >
              <Layers className="w-4 h-4 mr-2" />
              全部組件
            </Button>
            {componentGroups.map(group => (
              <Button
                key={group.id}
                variant={selectedGroup === group.id ? 'default' : 'ghost'}
                className="w-full justify-start"
                onClick={() => setSelectedGroup(group.id)}
              >
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: group.color }}
                />
                {group.name}
              </Button>
            ))}
          </div>
        </div>
        
        <div className="flex-1 p-4">
          <h4 className="font-medium mb-2">組件詳情</h4>
          {selectedGroup !== 'all' && (
            <div className="text-sm text-muted-foreground">
              {componentGroups.find(g => g.id === selectedGroup)?.description}
            </div>
          )}
        </div>

        <div className="p-4 border-t">
          <div className="text-xs text-muted-foreground space-y-1">
            <div>總節點: {nodes.length}</div>
            <div>連接線: {edges.length}</div>
            <div>當前分組: {filteredNodes.length}</div>
          </div>
        </div>
      </div>

      {/* 主要內容區 */}
      <div className="flex-1 flex flex-col">
        {/* 工具欄 */}
        <div className="flex items-center justify-between p-4 border-b bg-background">
          <div className="flex items-center gap-2">
            <Button onClick={() => setIsAddDialogOpen(true)} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              添加模組
            </Button>
            <Separator orientation="vertical" className="h-6" />
            <Button variant="outline" size="sm" onClick={saveArchitecture}>
              <Save className="w-4 h-4 mr-2" />
              保存架構
            </Button>
            <Button variant="outline" size="sm" onClick={exportArchitecture}>
              <Download className="w-4 h-4 mr-2" />
              導出架構
            </Button>
            <Button variant="outline" size="sm" asChild>
              <label htmlFor="import-file">
                <Upload className="w-4 h-4 mr-2" />
                導入架構
              </label>
            </Button>
            <input
              id="import-file"
              type="file"
              accept=".json"
              className="hidden"
              onChange={importArchitecture}
            />
          </div>
          
          <div className="text-sm text-muted-foreground">
            {currentConfig ? `已加載: ${currentConfig.name}` : '未保存的架構'}
          </div>
        </div>

        {/* React Flow 編輯器 */}
        <div className="flex-1">
          <ReactFlow
            nodes={filteredNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            onNodeDoubleClick={(_, node) => editModule(node.data as ModuleData)}
          >
            <Controls />
            <MiniMap />
            <Background />
          </ReactFlow>
        </div>
      </div>

      {/* 添加模組對話框 */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加新模組</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">名稱</Label>
              <Input id="name" placeholder="模組名稱" className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="type" className="text-right">類型</Label>
              <Select>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="選擇模組類型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="model">模型</SelectItem>
                  <SelectItem value="tool">工具</SelectItem>
                  <SelectItem value="core-ai">核心AI</SelectItem>
                  <SelectItem value="service">服務</SelectItem>
                  <SelectItem value="data-store">數據存儲</SelectItem>
                  <SelectItem value="interface">介面</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="description" className="text-right">描述</Label>
              <Textarea id="description" placeholder="模組描述" className="col-span-3" />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={addNewModule}>添加</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* 編輯模組對話框 */}
      {editingNode && (
        <Dialog open={!!editingNode} onOpenChange={() => setEditingNode(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>編輯模組: {editingNode.label}</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-name" className="text-right">名稱</Label>
                <Input 
                  id="edit-name" 
                  value={editingNode.label} 
                  onChange={(e) => setEditingNode({...editingNode, label: e.target.value})}
                  className="col-span-3" 
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-type" className="text-right">類型</Label>
                <Select value={editingNode.type} onValueChange={(value) => setEditingNode({...editingNode, type: value as any})}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="model">模型</SelectItem>
                    <SelectItem value="tool">工具</SelectItem>
                    <SelectItem value="core-ai">核心AI</SelectItem>
                    <SelectItem value="service">服務</SelectItem>
                    <SelectItem value="data-store">數據存儲</SelectItem>
                    <SelectItem value="interface">介面</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-status" className="text-right">狀態</Label>
                <Select value={editingNode.status} onValueChange={(value) => setEditingNode({...editingNode, status: value as any})}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="completed">已完成</SelectItem>
                    <SelectItem value="built-in">內建</SelectItem>
                    <SelectItem value="downloadable">可下載</SelectItem>
                    <SelectItem value="in-progress">進行中</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-description" className="text-right">描述</Label>
                <Textarea 
                  id="edit-description" 
                  value={editingNode.description} 
                  onChange={(e) => setEditingNode({...editingNode, description: e.target.value})}
                  className="col-span-3" 
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-location" className="text-right">位置</Label>
                <Input 
                  id="edit-location" 
                  value={editingNode.location || ''} 
                  onChange={(e) => setEditingNode({...editingNode, location: e.target.value})}
                  className="col-span-3" 
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingNode(null)}>
                取消
              </Button>
              <Button onClick={() => saveModule(editingNode)}>保存</Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
