import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Button } from '@acme/ui';
import { Input } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui';
import { 
  Network, 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  Download, 
  Upload,
  Filter,
  Settings,
  Database,
  Link,
  FileText,
  Globe
} from 'lucide-react';

interface Entity {
  id: string;
  name: string;
  type: string;
  description: string;
  relations: number;
  lastUpdated: string;
}

interface Relation {
  id: string;
  source: string;
  target: string;
  type: string;
  strength: number;
  lastUpdated: string;
}

interface GraphData {
  nodes: Entity[];
  edges: Relation[];
}

export function KnowledgeGraph() {
  const [entities, setEntities] = useState<Entity[]>([
    {
      id: '1',
      name: '人工智慧',
      type: '概念',
      description: '模擬人類智能的計算系統',
      relations: 12,
      lastUpdated: '2023-06-15T14:30:00Z'
    },
    {
      id: '2',
      name: '機器學習',
      type: '技術',
      description: 'AI的一個分支，使計算機能夠從數據中學習',
      relations: 8,
      lastUpdated: '2023-06-15T14:30:00Z'
    },
    {
      id: '3',
      name: '深度學習',
      type: '技術',
      description: '機器學習的一個子集，使用神經網絡',
      relations: 6,
      lastUpdated: '2023-06-15T14:30:00Z'
    },
    {
      id: '4',
      name: '神經網絡',
      type: '架構',
      description: '模擬生物神經網絡的計算模型',
      relations: 10,
      lastUpdated: '2023-06-15T14:30:00Z'
    }
  ]);

  const [relations, setRelations] = useState<Relation[]>([
    {
      id: 'r1',
      source: '1',
      target: '2',
      type: '包含',
      strength: 0.9,
      lastUpdated: '2023-06-15T14:30:00Z'
    },
    {
      id: 'r2',
      source: '2',
      target: '3',
      type: '包含',
      strength: 0.8,
      lastUpdated: '2023-06-15T14:30:00Z'
    },
    {
      id: 'r3',
      source: '3',
      target: '4',
      type: '使用',
      strength: 0.95,
      lastUpdated: '2023-06-15T14:30:00Z'
    }
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [graphView, setGraphView] = useState<'network' | 'list'>('network');

  const filteredEntities = entities.filter(entity => 
    entity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entity.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    entity.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getEntityTypeColor = (type: string): string => {
    switch (type.toLowerCase()) {
      case '概念':
        return 'bg-blue-500';
      case '技術':
        return 'bg-green-500';
      case '架構':
        return 'bg-purple-500';
      case '人物':
        return 'bg-yellow-500';
      case '組織':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleAddEntity = () => {
    // 模擬添加實體
    const newEntity: Entity = {
      id: `entity_${Date.now()}`,
      name: '新實體',
      type: '概念',
      description: '新添加的實體',
      relations: 0,
      lastUpdated: new Date().toISOString()
    };
    setEntities([...entities, newEntity]);
  };

  const handleDeleteEntity = (id: string) => {
    setEntities(entities.filter(entity => entity.id !== id));
    setRelations(relations.filter(relation => 
      relation.source !== id && relation.target !== id
    ));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">知識圖譜管理</h1>
        <p className="text-muted-foreground">管理AI系統的知識圖譜和實體關係</p>
      </div>

      <Tabs defaultValue="entities" className="space-y-4">
        <TabsList>
          <TabsTrigger value="entities">實體管理</TabsTrigger>
          <TabsTrigger value="relations">關係管理</TabsTrigger>
          <TabsTrigger value="visualization">圖譜可視化</TabsTrigger>
        </TabsList>

        <TabsContent value="entities" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                實體列表
              </CardTitle>
              <CardDescription>
                管理知識圖譜中的實體
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="搜索實體..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button onClick={handleAddEntity}>
                  <Plus className="h-4 w-4 mr-1" />
                  添加實體
                </Button>
              </div>

              <div className="space-y-3">
                {filteredEntities.map((entity) => (
                  <div key={entity.id} className="p-4 border border-border rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`w-3 h-3 rounded-full mt-1.5 ${getEntityTypeColor(entity.type)}`}></div>
                        <div>
                          <h3 className="font-medium">{entity.name}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary">{entity.type}</Badge>
                            <span className="text-sm text-muted-foreground">
                              {entity.relations} 個關係
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground mt-2">
                            {entity.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleDeleteEntity(entity.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
                      <span>最後更新: {new Date(entity.lastUpdated).toLocaleDateString()}</span>
                      <Button variant="link" size="sm" className="text-xs p-0 h-auto">
                        查看關係
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="relations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link className="h-5 w-5" />
                關係列表
              </CardTitle>
              <CardDescription>
                管理實體之間的關係
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <div className="relative flex-1">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="過濾關係..."
                    className="pl-10"
                  />
                </div>
                <Button>
                  <Plus className="h-4 w-4 mr-1" />
                  添加關係
                </Button>
              </div>

              <div className="space-y-3">
                {relations.map((relation) => {
                  const sourceEntity = entities.find(e => e.id === relation.source);
                  const targetEntity = entities.find(e => e.id === relation.target);
                  
                  return (
                    <div key={relation.id} className="p-4 border border-border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <div className="font-medium">{sourceEntity?.name || relation.source}</div>
                            <Badge variant="secondary" className="mt-1">{sourceEntity?.type || '未知'}</Badge>
                          </div>
                          <div className="text-muted-foreground">
                            <Link className="h-5 w-5" />
                          </div>
                          <div className="text-center">
                            <div className="font-medium">{targetEntity?.name || relation.target}</div>
                            <Badge variant="secondary" className="mt-1">{targetEntity?.type || '未知'}</Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge variant="outline">{relation.type}</Badge>
                          <div className="text-sm">
                            強度: {(relation.strength * 100).toFixed(0)}%
                          </div>
                          <div className="flex gap-1">
                            <Button variant="outline" size="sm">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="sm">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
                        <span>最後更新: {new Date(relation.lastUpdated).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="visualization" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5" />
                圖譜可視化
              </CardTitle>
              <CardDescription>
                可視化知識圖譜結構
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Button 
                  variant={graphView === 'network' ? 'default' : 'outline'}
                  onClick={() => setGraphView('network')}
                >
                  <Network className="h-4 w-4 mr-1" />
                  網絡視圖
                </Button>
                <Button 
                  variant={graphView === 'list' ? 'default' : 'outline'}
                  onClick={() => setGraphView('list')}
                >
                  <List className="h-4 w-4 mr-1" />
                  列表視圖
                </Button>
                <div className="flex-1"></div>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-1" />
                  導出
                </Button>
                <Button variant="outline">
                  <Upload className="h-4 w-4 mr-1" />
                  導入
                </Button>
              </div>

              <div className="border border-border rounded-lg h-96 flex items-center justify-center bg-muted/50">
                {graphView === 'network' ? (
                  <div className="text-center">
                    <Network className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                    <p className="text-muted-foreground">知識圖譜網絡視圖</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      顯示實體之間的關係網絡
                    </p>
                  </div>
                ) : (
                  <div className="text-center">
                    <List className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                    <p className="text-muted-foreground">知識圖譜列表視圖</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      以列表形式顯示實體和關係
                    </p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2">
                      <Database className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="text-sm text-muted-foreground">總實體數</p>
                        <p className="text-xl font-bold">{entities.length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2">
                      <Link className="h-5 w-5 text-green-500" />
                      <div>
                        <p className="text-sm text-muted-foreground">總關係數</p>
                        <p className="text-xl font-bold">{relations.length}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2">
                      <Globe className="h-5 w-5 text-purple-500" />
                      <div>
                        <p className="text-sm text-muted-foreground">知識覆蓋率</p>
                        <p className="text-xl font-bold">87%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}