"use client"

import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@acme/ui';
import { Button } from '@acme/ui';
import { Input } from '@acme/ui';
import { Badge } from '@acme/ui';
import { ScrollArea } from '@acme/ui';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@acme/ui';
import { Plus, Search, Save, Trash2, FileText, Folder } from 'lucide-react';

interface CodeFile {
  id: string;
  name: string;
  path: string;
  language: string;
  content: string;
  size: number;
  lastModified: string;
  isActive: boolean;
}

interface CodeProject {
  id: string;
  name: string;
  description: string;
  language: string;
  files: CodeFile[];
  status: 'active' | 'inactive';
  createdAt: string;
  lastModified: string;
}

const initialProjects: CodeProject[] = [
  {
    id: 'unified-ai-core',
    name: '統一AI核心',
    description: '統一AI系統的核心實現',
    language: 'typescript',
    status: 'active',
    createdAt: '2024-01-01T00:00:00Z',
    lastModified: '2024-01-15T00:00:00Z',
    files: [
      {
        id: 'main-ts',
        name: 'main.ts',
        path: '/src/main.ts',
        language: 'typescript',
        content: "// 統一AI系統主入口\nimport { UnifiedAISystem } from './core/system';\nimport { config } from './config';\n\nasync function main() {\n  const system = new UnifiedAISystem(config);\n  await system.initialize();\n  await system.start();\n}\n\nmain().catch(console.error);",
        size: 2048,
        lastModified: '2024-01-15T00:00:00Z',
        isActive: true
      },
      {
        id: 'config-ts',
        name: 'config.ts',
        path: '/src/config.ts',
        language: 'typescript',
        content: "// 系統配置\nexport const config = {\n  level5: {\n    enabled: true,\n    components: ['knowledge', 'fusion', 'cognitive', 'evolution', 'creativity', 'metacognition']\n  },\n  training: {\n    auto_train: true,\n    datasets_path: './data/training/'\n  }\n};",
        size: 1024,
        lastModified: '2024-01-14T00:00:00Z',
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
      path: '/src/new-file.ts',
      language: 'typescript',
      content: '// 新文件\n',
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
      {/* 左侧边栏 - 项目和文件树 */}
      <div className="w-80 border-r bg-muted/30 flex flex-col">
        {/* 项目选择 */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">代码项目</h3>
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
              <SelectValue placeholder="选择项目" />
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

        {/* 搜索栏 */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="搜索文件..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>

        {/* 文件树 */}
        <div className="flex-1 overflow-hidden">
          <div className="p-4 border-b flex items-center justify-between">
            <h4 className="font-medium text-sm">文件</h4>
            <Button size="sm" variant="ghost" onClick={() => setIsCreateFileOpen(true)}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          
          <ScrollArea className="flex-1">
            <div className="p-2">
              {filteredFiles.map(file => (
                <div
                  key={file.id}
                  className={`flex items-center justify-between p-2 rounded cursor-pointer hover:bg-muted/50 ${
                    selectedFile?.id === file.id ? 'bg-muted' : ''
                  }`}
                  onClick={() => setSelectedFile(file)}
                >
                  <div className="flex items-center gap-2 flex-1">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{file.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{file.path}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Badge className={`w-2 h-2 p-0 ${languageColors[file.language as keyof typeof languageColors] || 'bg-gray-500'}`} />
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteFile(file.id);
                      }}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="flex-1 flex flex-col">
        {/* 工具栏 */}
        <div className="border-b p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold">{selectedFile?.name || '未选择文件'}</h2>
            {selectedFile && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Badge className={`w-2 h-2 p-0 ${languageColors[selectedFile.language as keyof typeof languageColors] || 'bg-gray-500'}`} />
                <span>{selectedFile.language}</span>
                <span>•</span>
                <span>{selectedFile.size} 字节</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={saveFile}>
              <Save className="w-4 h-4 mr-2" />
              保存
            </Button>
          </div>
        </div>

        {/* 代码编辑器 */}
        <div className="flex-1 p-4">
          {selectedFile ? (
            <div className="h-full border rounded-lg overflow-hidden">
              <textarea
                value={selectedFile.content}
                onChange={(e) => updateFileContent(e.target.value)}
                className="w-full h-full p-4 font-mono text-sm resize-none border-none outline-none"
                placeholder="在此编写代码..."
              />
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>选择一个文件开始编辑</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}