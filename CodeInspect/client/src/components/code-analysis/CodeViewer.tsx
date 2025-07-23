import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { ChevronLeft, ChevronRight, FileText, AlertTriangle, Lightbulb, Code } from "lucide-react"
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow, prism } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useTheme } from "@/components/ui/theme-provider"

interface CodeViewerProps {
  project: any
  selectedFile: any
  issues: any[]
  selectedIssue?: any
}

export function CodeViewer({ project, selectedFile, issues, selectedIssue }: CodeViewerProps) {
  const [currentFile, setCurrentFile] = useState(selectedFile || project.files[0])
  const [fileContent, setFileContent] = useState("")
  const { theme } = useTheme()

  console.log("CodeViewer rendered with file:", currentFile?.path)

  useEffect(() => {
    if (selectedFile) {
      setCurrentFile(selectedFile)
    }
  }, [selectedFile])

  useEffect(() => {
    if (currentFile) {
      // Mock file content - in real app this would fetch from API
      setFileContent(currentFile.content || `// ${currentFile.path}
function exampleFunction() {
  const data = fetchData();
  if (data) {
    processData(data);
  }
  return data;
}

class ExampleClass {
  constructor(options) {
    this.options = options;
  }
  
  process() {
    // Some processing logic
    return this.options;
  }
}`)
    }
  }, [currentFile])

  const fileIssues = issues.filter(issue => issue.file === currentFile?.path)
  const getLanguage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'js': case 'jsx': return 'javascript'
      case 'ts': case 'tsx': return 'typescript'
      case 'py': return 'python'
      case 'java': return 'java'
      case 'cpp': case 'cc': case 'cxx': return 'cpp'
      case 'c': return 'c'
      case 'cs': return 'csharp'
      case 'php': return 'php'
      case 'rb': return 'ruby'
      case 'go': return 'go'
      case 'rs': return 'rust'
      default: return 'text'
    }
  }

  const navigateToIssue = (direction: 'prev' | 'next') => {
    const currentIndex = fileIssues.findIndex(issue => issue.line === currentFile?.line)
    let newIndex
    
    if (direction === 'prev') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : fileIssues.length - 1
    } else {
      newIndex = currentIndex < fileIssues.length - 1 ? currentIndex + 1 : 0
    }
    
    if (fileIssues[newIndex]) {
      setCurrentFile({ ...currentFile, line: fileIssues[newIndex].line })
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-12rem)]">
      {/* File Tree */}
      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileText className="w-4 h-4" />
            Project Files
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-20rem)]">
            <div className="p-4 space-y-1">
              {project.files.map((file: any) => (
                <div
                  key={file.path}
                  className={`p-2 rounded cursor-pointer text-sm transition-colors ${
                    currentFile?.path === file.path
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100'
                      : 'hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                  onClick={() => setCurrentFile(file)}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono truncate">{file.path}</span>
                    {issues.some(issue => issue.file === file.path) && (
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Code Editor */}
      <div className="lg:col-span-2 space-y-4">
        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5" />
                <CardTitle className="font-mono text-sm">{currentFile?.path}</CardTitle>
              </div>
              
              {fileIssues.length > 0 && (
                <div className="flex items-center gap-2">
                  <Badge variant="destructive" className="text-xs">
                    {fileIssues.length} issues
                  </Badge>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigateToIssue('prev')}
                      className="h-7 w-7 p-0"
                    >
                      <ChevronLeft className="w-3 h-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigateToIssue('next')}
                      className="h-7 w-7 p-0"
                    >
                      <ChevronRight className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative">
              <SyntaxHighlighter
                language={getLanguage(currentFile?.path || '')}
                style={theme === 'dark' ? tomorrow : prism}
                showLineNumbers
                customStyle={{
                  margin: 0,
                  borderRadius: 0,
                  background: 'transparent',
                  fontSize: '14px',
                }}
                lineNumberStyle={{
                  minWidth: '3em',
                  paddingRight: '1em',
                  color: '#6b7280',
                }}
              >
                {fileContent}
              </SyntaxHighlighter>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Issues Panel */}
      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <AlertTriangle className="w-4 h-4" />
            File Issues ({fileIssues.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-20rem)]">
            <div className="p-4 space-y-4">
              {fileIssues.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Lightbulb className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    No issues found in this file
                  </p>
                </div>
              ) : (
                fileIssues.map((issue) => (
                  <div key={issue._id} className="space-y-3">
                    <div className={`p-3 rounded-lg ${selectedIssue?._id === issue._id ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : 'bg-slate-50 dark:bg-slate-800'}`}>
                      <div className="flex items-start gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{issue.title}</h4>
                          <p className="text-xs text-muted-foreground mt-1">
                            Line {issue.line}
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">
                        {issue.description}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {issue.category}
                      </Badge>
                    </div>
                    
                    {issue.suggestion && (
                      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-4 h-4 text-blue-500 mt-0.5" />
                          <div>
                            <h5 className="font-medium text-sm text-blue-900 dark:text-blue-100">
                              AI Suggestion
                            </h5>
                            <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                              {issue.suggestion}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <Separator />
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}