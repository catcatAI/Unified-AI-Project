import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { 
  FileText, 
  AlertTriangle, 
  XCircle, 
  Info, 
  Code, 
  Lightbulb, 
  ChevronRight,
  Package,
  TrendingUp,
  Shield,
  Zap
} from "lucide-react"
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow, prism } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useTheme } from "@/components/ui/theme-provider"
import { cn } from "@/lib/utils"

interface IntegratedAnalysisViewProps {
  project: any
  selectedFile: any
  selectedIssue: any
  onFileSelect: (file: any) => void
  onIssueSelect: (issue: any) => void
}

export function IntegratedAnalysisView({ 
  project, 
  selectedFile, 
  selectedIssue,
  onFileSelect, 
  onIssueSelect 
}: IntegratedAnalysisViewProps) {
  const [currentFile, setCurrentFile] = useState(selectedFile || project.files[0])
  const [fileContent, setFileContent] = useState("")
  const { theme } = useTheme()

  const handleFileSelect = (file: any) => {
    setCurrentFile(file)
    onFileSelect(file)
    // Mock file content
    setFileContent(file.content || `// ${file.path}
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

  const handleIssueSelect = (issue: any) => {
    onIssueSelect(issue)
    const file = project.files.find(f => f.path === issue.file)
    if (file) {
      handleFileSelect({ ...file, line: issue.line })
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "info":
        return <Info className="w-4 h-4 text-blue-500" />
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "border-l-red-500 bg-red-50/50 dark:bg-red-900/10"
      case "warning":
        return "border-l-yellow-500 bg-yellow-50/50 dark:bg-yellow-900/10"
      case "info":
        return "border-l-blue-500 bg-blue-50/50 dark:bg-blue-900/10"
      default:
        return "border-l-gray-500 bg-gray-50/50 dark:bg-gray-900/10"
    }
  }

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

  const fileIssues = project.issues.filter(issue => issue.file === currentFile?.path)
  const criticalCount = project.issues.filter(i => i.severity === "critical").length
  const warningCount = project.issues.filter(i => i.severity === "warning").length
  const infoCount = project.issues.filter(i => i.severity === "info").length

  return (
    <div className="space-y-6">
      {/* Project Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-700 dark:text-blue-300">Total Files</p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">{project.fileCount}</p>
              </div>
              <FileText className="w-6 h-6 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-700 dark:text-red-300">Critical Issues</p>
                <p className="text-2xl font-bold text-red-900 dark:text-red-100">{criticalCount}</p>
              </div>
              <XCircle className="w-6 h-6 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200 dark:border-yellow-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-700 dark:text-yellow-300">Warnings</p>
                <p className="text-2xl font-bold text-yellow-900 dark:text-yellow-100">{warningCount}</p>
              </div>
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border-green-200 dark:border-green-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-700 dark:text-green-300">Complexity</p>
                <p className="text-2xl font-bold text-green-900 dark:text-green-100">{project.complexityScore}/100</p>
              </div>
              <TrendingUp className="w-6 h-6 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Analysis Interface */}
      <ResizablePanelGroup direction="horizontal" className="min-h-[600px] rounded-lg border bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg">
        {/* Left Panel - File Tree & Issues */}
        <ResizablePanel defaultSize={30} minSize={25}>
          <div className="h-full flex flex-col">
            {/* File Tree */}
            <div className="flex-1 border-b">
              <div className="p-4 border-b bg-slate-50/50 dark:bg-slate-800/50">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Project Files
                </h3>
              </div>
              <ScrollArea className="h-48">
                <div className="p-2 space-y-1">
                  {project.files.map((file: any) => (
                    <div
                      key={file.path}
                      className={cn(
                        "p-2 rounded cursor-pointer text-sm transition-all duration-200",
                        currentFile?.path === file.path
                          ? "bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100 shadow-sm"
                          : "hover:bg-slate-100 dark:hover:bg-slate-800"
                      )}
                      onClick={() => handleFileSelect(file)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono truncate">{file.path}</span>
                        {project.issues.some(issue => issue.file === file.path) && (
                          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>

            {/* Issues List */}
            <div className="flex-1">
              <div className="p-4 border-b bg-slate-50/50 dark:bg-slate-800/50">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Issues ({project.issues.length})
                </h3>
              </div>
              <ScrollArea className="h-full">
                <div className="p-2 space-y-2">
                  {project.issues.map((issue) => (
                    <Card
                      key={issue._id}
                      className={cn(
                        "border-l-4 cursor-pointer hover:shadow-md transition-all duration-200 p-3",
                        getSeverityColor(issue.severity),
                        selectedIssue?._id === issue._id && "ring-2 ring-blue-500 ring-opacity-50"
                      )}
                      onClick={() => handleIssueSelect(issue)}
                    >
                      <div className="space-y-2">
                        <div className="flex items-start gap-2">
                          {getSeverityIcon(issue.severity)}
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm truncate">{issue.title}</h4>
                            <p className="text-xs text-muted-foreground truncate">{issue.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <Badge variant="outline" className="text-xs">
                            {issue.category}
                          </Badge>
                          <span className="text-muted-foreground">Line {issue.line}</span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right Panel - Code Viewer */}
        <ResizablePanel defaultSize={70}>
          <div className="h-full flex flex-col">
            {/* Code Header */}
            <div className="p-4 border-b bg-slate-50/50 dark:bg-slate-800/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  <span className="font-mono text-sm">{currentFile?.path}</span>
                </div>
                {fileIssues.length > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {fileIssues.length} issues
                  </Badge>
                )}
              </div>
            </div>

            {/* Code Content */}
            <div className="flex-1 overflow-hidden">
              <SyntaxHighlighter
                language={getLanguage(currentFile?.path || '')}
                style={theme === 'dark' ? tomorrow : prism}
                showLineNumbers
                customStyle={{
                  margin: 0,
                  height: '100%',
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

            {/* Issue Details Panel */}
            {selectedIssue && (
              <div className="border-t bg-white/80 dark:bg-slate-900/80 p-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(selectedIssue.severity)}
                    <div className="flex-1">
                      <h4 className="font-semibold text-sm">{selectedIssue.title}</h4>
                      <p className="text-sm text-muted-foreground mt-1">{selectedIssue.description}</p>
                    </div>
                    <Badge variant="outline">{selectedIssue.category}</Badge>
                  </div>

                  {selectedIssue.suggestion && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <div className="flex items-start gap-2">
                        <Lightbulb className="w-4 h-4 text-blue-500 mt-0.5" />
                        <div>
                          <h5 className="font-medium text-sm text-blue-900 dark:text-blue-100">
                            AI Suggestion
                          </h5>
                          <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                            {selectedIssue.suggestion}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}