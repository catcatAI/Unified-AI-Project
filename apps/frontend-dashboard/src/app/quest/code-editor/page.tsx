
import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Plus, Edit, Trash2, Play, Save, Download, Upload, 
  FileText, Folder, Search, Settings, Terminal
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';

interface CodeFile {
  id: string;
  name: string;
  path: string;
  language: 'typescript' | 'javascript' | 'python' | 'html' | 'css' | 'json' | 'markdown';
  content: string;
  size: number;
  lastModified: string;
  isActive: boolean;
}

interface CodeProject {
  id: string;
  name: string;
  description: string;
  type: 'frontend' | 'backend' | 'ai-model' | 'utility' | 'config';
  files: CodeFile[];
  dependencies: string[];
  status: 'active' | 'inactive' | 'building' | 'error';
}

const initialProjects: CodeProject[] = [
  {
    id: 'frontend-components',
    name: '前端組件庫',
    description: 'React 前端組件集合',
    type: 'frontend',
    status: 'active',
    dependencies: ['react', 'typescript', 'tailwindcss'],
    files: [
      {
        id: 'chat-component',
        name: 'ChatInterface.tsx',
        path: '/src/components/ChatInterface.tsx',
        language: 'typescript',
        content: `import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

export default function ChatInterface({ 
  messages, 
  onSendMessage, 
  isLoading = false 
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className="flex gap-3">
            <div className={
              message.role === 'user' 
                ? 'bg-primary text-primary-foreground' 
                : 'bg-muted'
            }>
              {message.content}
            </div>
          </div>
        ))}
      </div>
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="輸入消息..."
            disabled={isLoading}
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
            發送
          </Button>
        </div>
      </div>
    </div>
  );
}`,
        size: 1024,
        lastModified: '2024-01-01T10:00:00Z',
        isActive: true
      }
    ]
  },
  {
    id: 'ai-models',
    name: 'AI 模型集合',
    description: 'AI 相關模型和工具',
    type: 'ai-model',
    status: 'active',
    dependencies: ['python', 'torch', 'transformers'],
    files: [
      {
        id: 'text-processor',
        name: 'text_processor.py',
        path: '/src/ai/text_processor.py',
        language: 'python',
        content: "import re\nimport json\nfrom typing import Dict, List, Any\n\nclass TextProcessor:\n    """文本處理核心類"""\n    \n    def __init__(self):\n        self.stopwords = set(['的', '是', '在', '了', '和', '有'])\n    \n    def clean_text(self, text: str) -> str:\n        """清理文本,移除特殊字符"""\n        # 保留中文、英文、數字和基本標點\n        cleaned = re.sub(r'[^\\u4e00-\\u9fff\\w\\s.,!?;:]', ' ', text)\n        return ' '.join(cleaned.split())\n    \n    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:\n        """提取關鍵詞"""\n        words = self.clean_text(text).split()\n        # 簡單的詞頻統計\n        word_freq = {}\n        for word in words:\n            if word.lower() not in self.stopwords and len(word) > 1:\n                word_freq[word] = word_freq.get(word, 0) + 1\n        \n        # 按頻率排序\n        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)\n        return [word for word, freq in sorted_words[:max_keywords]]\n    \n    def analyze_sentiment(self, text: str) -> Dict[str, Any]:\n        """簡單的情感分析"""\n        positive_words = ['好', '棒', '優秀', '喜歡', '滿意']\n        negative_words = ['壞', '差', '討厭', '失望', '糟糕']\n        \n        text_lower = text.lower()\n        positive_count = sum(1 for word in positive_words if word in text_lower)\n        negative_count = sum(1 for word in negative_words if word in text_lower)\n        \n        if positive_count > negative_count:\n            sentiment = 'positive'\n        elif negative_count > positive_count:\n            sentiment = 'negative'\n        else:\n            sentiment = 'neutral'\n        \n        return {\n            'sentiment': sentiment,\n            'positive_score': positive_count,\n            'negative_score': negative_count,\n            'confidence': abs(positive_count - negative_count) / max(len(text.split()), 1)\n        }\n\n# 使用示例\nif __name__ == '__main__':\n    processor = TextProcessor()\n    test_text = '這個產品真的很好用,我很喜歡！'\n    \n    print('清理後文本:', processor.clean_text(test_text))\n    print('關鍵詞:', processor.extract_keywords(test_text))\n    print('情感分析:', processor.analyze_sentiment(test_text))",
        size: 2048,
        lastModified: '2024-01-01T09:30:00Z',
        isActive: false
      }
    ]
  }
];

export default function CodeEditor() {
  const [projects, setProjects] = useState<CodeProject[]>(initialProjects);
  const [selectedProject, setSelectedProject] = useState<CodeProject | null>(projects[0]);
  const [selectedFile, setSelectedFile] = useState<CodeFile | null>(projects[0]?.files[0] || null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
  const [isCreateFileOpen, setIsCreateFileOpen] = useState(false);

  const languageColors = {
    typescript: 'bg-blue-500',
    javascript: 'bg-yellow-500',
    python: 'bg-green-500',
    html: 'bg-red-500',
    css: 'bg-purple-500',
    json: 'bg-gray-500',
    markdown: 'bg-indigo-500'
  };

  const filteredFiles = selectedProject?.files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    file.path.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const saveFile = () => {
    if (!selectedFile || !selectedProject) return;
    
    const updatedProjects = projects.map(project => {
      if (project.id === selectedProject.id) {
        return {
          ...project,
          files: project.files.map(file =>
            file.id === selectedFile.id
              ? { ...file, lastModified: new Date().toISOString() }
              : file
          )
        };
      }
      return project;
    });
    
    setProjects(updatedProjects);
    console.log('文件已保存:', selectedFile.name);
  };

  const createNewFile = () => {
    if (!selectedProject) return;
    
    const newFile: CodeFile = {
      id: `file-${Date.now()}`,
      name: 'new-file.ts',
      path: `/src/new-file.ts`,
      language: 'typescript',
      content: '// 新文件\\n',
      size: 0,
      lastModified: new Date().toISOString(),
      isActive: false
    };
    
    const updatedProject = {
      ...selectedProject,
      files: [...selectedProject.files, newFile]
    };
    
    setProjects(prev => prev.map(p => p.id === selectedProject.id ? updatedProject : p));
    setSelectedProject(updatedProject);
    setSelectedFile(newFile);
    setIsCreateFileOpen(false);
  };

  const deleteFile = (fileId: string) => {
    if (!selectedProject) return;
    
    const updatedProject = {
      ...selectedProject,
      files: selectedProject.files.filter(f => f.id !== fileId)
    };
    
    setProjects(prev => prev.map(p => p.id === selectedProject.id ? updatedProject : p));
    
    if (selectedFile?.id === fileId) {
      setSelectedFile(updatedProject.files[0] || null);
    }
  };

  const updateFileContent = (content: string) => {
    if (!selectedFile) return;
    
    const updatedFile = { ...selectedFile, content, size: content.length };
    setSelectedFile(updatedFile);
    
    if (selectedProject) {
      const updatedProject = {
        ...selectedProject,
        files: selectedProject.files.map(f => f.id === selectedFile.id ? updatedFile : f)
      };
      setSelectedProject(updatedProject);
    }
  };

  return (
    <div className="h-full flex">
      {/* 左側邊欄 - 項目和文件樹 */}
      <div className="w-80 border-r bg-muted/30 flex flex-col">
        {/* 項目選擇 */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">代碼項目</h3>
            <Button size="sm" onClick={() => setIsCreateProjectOpen(true)}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <Select
            value={selectedProject?.id || ''}
            onValueChange={(value) => {
              const project = projects.find(p => p.id === value);
              setSelectedProject(project || null);
              setSelectedFile(project?.files[0] || null);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="選擇項目" />
            </SelectTrigger>
            <SelectContent>
              {projects.map(project => (
                <SelectItem key={project.id} value={project.id}>
                  <div className="flex items-center gap-2">
                    <Badge className={`w-2 h-2 p-0 ${
                      project.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                    }`} />
                    {project.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 文件搜索 */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索文件..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* 文件列表 */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            <div className="flex items-center justify-between mb-2 px-2">
              <span className="text-sm font-medium">文件</span>
              <Button size="sm" variant="ghost" onClick={() => setIsCreateFileOpen(true)}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            
            {filteredFiles.length === 0 ? (
              <p className="text-muted-foreground text-sm p-4 text-center">
                {selectedProject ? '沒有找到文件' : '請選擇項目'}
              </p>
            ) : (
              <div className="space-y-1">
                {filteredFiles.map(file => (
                  <div
                    key={file.id}
                    className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted transition-colors ${
                      selectedFile?.id === file.id ? 'bg-muted' : ''
                    }`}
                    onClick={() => setSelectedFile(file)}
                  >
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{file.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{file.path}</div>
                    </div>
                    <Badge className={`${languageColors[file.language]} text-white text-xs`}>
                      {file.language}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 項目信息 */}
        {selectedProject && (
          <div className="p-4 border-t bg-muted/50">
            <div className="text-sm space-y-1">
              <div className="font-medium">{selectedProject.name}</div>
              <div className="text-muted-foreground">{selectedProject.description}</div>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="outline">{selectedProject.type}</Badge>
                <Badge className={
                  selectedProject.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                }>
                  {selectedProject.status}
                </Badge>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 主編輯區 */}
      <div className="flex-1 flex flex-col">
        {selectedFile ? (
          <>
            {/* 編輯器工具欄 */}
            <div className="border-b p-2 flex items-center justify-between bg-background">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span className="font-medium">{selectedFile.name}</span>
                <Badge className={`${languageColors[selectedFile.language]} text-white`}>
                  {selectedFile.language}
                </Badge>
                {selectedFile.lastModified && (
                  <span className="text-xs text-muted-foreground">
                    最後修改: {new Date(selectedFile.lastModified).toLocaleString()}
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline">
                  <Settings className="w-4 h-4 mr-2" />
                  設置
                </Button>
                <Button size="sm" variant="outline">
                  <Terminal className="w-4 h-4 mr-2" />
                  運行
                </Button>
                <Button size="sm" onClick={saveFile}>
                  <Save className="w-4 h-4 mr-2" />
                  保存
                </Button>
                <Button 
                  size="sm" 
                  variant="destructive"
                  onClick={() => deleteFile(selectedFile.id)}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  刪除
                </Button>
              </div>
            </div>

            {/* 代碼編輯器 */}
            <div className="flex-1 p-4">
              <Textarea
                value={selectedFile.content}
                onChange={(e) => updateFileContent(e.target.value)}
                className="w-full h-full font-mono text-sm resize-none"
                placeholder="開始編寫代碼..."
              />
            </div>

            {/* 底部狀態欄 */}
            <div className="border-t px-4 py-2 bg-muted/30 flex items-center justify-between text-xs">
              <div className="flex items-center gap-4">
                <span>行: 1, 列: 1</span>
                <span>編碼: UTF-8</span>
                <span>文件大小: {selectedFile.size} bytes</span>
              </div>
              <div className="flex items-center gap-2">
                <span>語言: {selectedFile.language}</span>
              </div>
            </div>
          </>
        ) : (
          <Card className="m-4 flex-1 flex items-center justify-center">
            <CardContent className="text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">選擇文件開始編輯</h3>
              <p className="text-muted-foreground mb-4">
                從左側文件樹中選擇一個文件,或創建新文件開始編寫代碼
              </p>
              <Button onClick={() => setIsCreateFileOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                創建新文件
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 創建項目對話框 */}
      <Dialog open={isCreateProjectOpen} onOpenChange={setIsCreateProjectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>創建新項目</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="project-name">項目名稱</Label>
              <Input id="project-name" placeholder="輸入項目名稱" />
            </div>
            <div>
              <Label htmlFor="project-desc">項目描述</Label>
              <Textarea id="project-desc" placeholder="輸入項目描述" />
            </div>
            <div>
              <Label htmlFor="project-type">項目類型</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="選擇項目類型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="frontend">前端</SelectItem>
                  <SelectItem value="backend">後端</SelectItem>
                  <SelectItem value="ai-model">AI 模型</SelectItem>
                  <SelectItem value="utility">工具庫</SelectItem>
                  <SelectItem value="config">配置</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsCreateProjectOpen(false)}>
                取消
              </Button>
              <Button onClick={() => setIsCreateProjectOpen(false)}>
                創建
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 創建文件對話框 */}
      <Dialog open={isCreateFileOpen} onOpenChange={setIsCreateFileOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>創建新文件</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="file-name">文件名稱</Label>
              <Input id="file-name" placeholder="例如: component.tsx" />
            </div>
            <div>
              <Label htmlFor="file-path">文件路徑</Label>
              <Input id="file-path" placeholder="例如: /src/components/" />
            </div>
            <div>
              <Label htmlFor="file-language">文件類型</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="選擇文件類型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="typescript">TypeScript</SelectItem>
                  <SelectItem value="javascript">JavaScript</SelectItem>
                  <SelectItem value="python">Python</SelectItem>
                  <SelectItem value="html">HTML</SelectItem>
                  <SelectItem value="css">CSS</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsCreateFileOpen(false)}>
                取消
              </Button>
              <Button onClick={createNewFile}>
                創建
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
