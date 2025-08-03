import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui';
import { Badge } from '@acme/ui';
import { Input } from '@acme/ui';
import { ScrollArea } from '@acme/ui';
import { 
  BookOpen, 
  Search, 
  FileText, 
  Code, 
  Database, 
  Network,
  Brain,
  Users
} from 'lucide-react';

export function Documentation() {
  const [searchQuery, setSearchQuery] = useState('');

  const documentCategories = [
    {
      title: '架構設計',
      icon: Brain,
      description: '系統架構和設計文檔',
      docs: [
        { name: 'ARCHITECTURE_OVERVIEW.md', type: 'architecture', status: '完成' },
        { name: 'HAM_design_spec.md', type: 'architecture', status: '完成' },
        { name: 'Fragmenta_design_spec.md', type: 'architecture', status: '進行中' },
        { name: 'AGENT_COLLABORATION_FRAMEWORK.md', type: 'architecture', status: '完成' },
      ]
    },
    {
      title: '技術規範',
      icon: Code,
      description: '技術實現和API規範',
      docs: [
        { name: 'HSP_SPECIFICATION.md', type: 'technical', status: '完成' },
        { name: 'HSP_QUICK_START.md', type: 'technical', status: '完成' },
        { name: 'CORE_SERVICES_OVERVIEW.md', type: 'technical', status: '完成' },
        { name: 'TROUBLESHOOTING.md', type: 'technical', status: '完成' },
      ]
    },
    {
      title: '專案管理',
      icon: Users,
      description: '專案組織和狀態文檔',
      docs: [
        { name: 'PROJECT_ORGANIZATION_STATUS.md', type: 'management', status: '完成' },
        { name: 'PROJECT_STATUS_SUMMARY.md', type: 'management', status: '完成' },
        { name: 'SUCCESS_CRITERIA.md', type: 'management', status: '完成' },
        { name: 'CLEANUP_SUMMARY.md', type: 'management', status: '完成' },
      ]
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case '完成':
        return 'default';
      case '進行中':
        return 'secondary';
      case '計劃中':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'architecture':
        return <Brain className="h-4 w-4" />;
      case 'technical':
        return <Code className="h-4 w-4" />;
      case 'management':
        return <Users className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const filteredCategories = documentCategories.map(category => ({
    ...category,
    docs: category.docs.filter(doc =>
      doc.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.docs.length > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">技術文檔</h1>
        <p className="text-muted-foreground">統一AI專案完整技術文檔庫</p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜尋文檔..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總文檔數</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">70+</div>
            <p className="text-xs text-muted-foreground">Markdown 文件</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">架構文檔</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">設計規範</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">技術規範</CardTitle>
            <Code className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">25</div>
            <p className="text-xs text-muted-foreground">API 和實現</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">完成度</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85%</div>
            <p className="text-xs text-muted-foreground">文檔覆蓋率</p>
          </CardContent>
        </Card>
      </div>

      {/* Document Categories */}
      <div className="space-y-6">
        {filteredCategories.map((category) => (
          <Card key={category.title}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <category.icon className="h-5 w-5" />
                {category.title}
              </CardTitle>
              <CardDescription>{category.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2">
                {category.docs.map((doc) => (
                  <div
                    key={doc.name}
                    className="flex items-center justify-between p-3 border border-border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {getTypeIcon(doc.type)}
                      <div>
                        <div className="font-medium text-sm">{doc.name}</div>
                        <div className="text-xs text-muted-foreground capitalize">
                          {doc.type} 文檔
                        </div>
                      </div>
                    </div>
                    <Badge variant={getStatusColor(doc.status) as any}>
                      {doc.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Access */}
      <Card>
        <CardHeader>
          <CardTitle>快速存取</CardTitle>
          <CardDescription>常用文檔和資源</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="p-4 border border-border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="h-4 w-4" />
                <span className="font-medium">系統架構</span>
              </div>
              <p className="text-sm text-muted-foreground">
                查看統一AI系統的完整架構設計
              </p>
            </div>
            
            <div className="p-4 border border-border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Network className="h-4 w-4" />
                <span className="font-medium">HSP 協議</span>
              </div>
              <p className="text-sm text-muted-foreground">
                異構服務協議的技術規範和使用指南
              </p>
            </div>
            
            <div className="p-4 border border-border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-4 w-4" />
                <span className="font-medium">HAM 記憶</span>
              </div>
              <p className="text-sm text-muted-foreground">
                分層抽象記憶系統的設計與實現
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
