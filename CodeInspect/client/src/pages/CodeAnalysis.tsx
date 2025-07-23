import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Github, FileText, AlertTriangle, CheckCircle, XCircle, Play, Pause, Eye, Code2, Brain, Sparkles } from "lucide-react"
import { ProjectUpload } from "@/components/code-analysis/ProjectUpload"
import { ProjectOverview } from "@/components/code-analysis/ProjectOverview"
import { IssuesDashboard } from "@/components/code-analysis/IssuesDashboard"
import { CodeViewer } from "@/components/code-analysis/CodeViewer"
import { AnalysisProgress } from "@/components/code-analysis/AnalysisProgress"
import { IntegratedAnalysisView } from "@/components/code-analysis/IntegratedAnalysisView"
import { getProjectAnalysis, uploadProject } from "@/api/codeAnalysis"
import { useToast } from "@/hooks/useToast"

export function CodeAnalysis() {
  const [currentProject, setCurrentProject] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [viewMode, setViewMode] = useState("integrated") // "integrated" or "tabbed"
  const { toast } = useToast()

  console.log("CodeAnalysis component rendered")

  const handleProjectUpload = async (files: FileList | null, githubUrl?: string) => {
    console.log("Starting project upload", { files: files?.length, githubUrl })
    
    try {
      setIsAnalyzing(true)
      setAnalysisProgress(0)
      
      const result = await uploadProject({ files, githubUrl })
      
      // Simulate analysis progress
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval)
            setIsAnalyzing(false)
            return 100
          }
          return prev + 10
        })
      }, 500)
      
      setTimeout(async () => {
        const analysis = await getProjectAnalysis(result.projectId)
        setCurrentProject(analysis)
        toast({
          title: "Analysis Complete",
          description: "Your project has been successfully analyzed with AI insights.",
        })
      }, 5000)
      
    } catch (error) {
      console.error("Project upload failed:", error)
      setIsAnalyzing(false)
      toast({
        title: "Upload Failed",
        description: error.message,
        variant: "destructive",
      })
    }
  }

  const handleIssueSelect = (issue: any) => {
    setSelectedIssue(issue)
    setSelectedFile({ path: issue.file, line: issue.line })
  }

  const handleFileSelect = (file: any) => {
    setSelectedFile(file)
  }

  if (isAnalyzing) {
    return <AnalysisProgress progress={analysisProgress} />
  }

  if (!currentProject) {
    return <ProjectUpload onUpload={handleProjectUpload} />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-blue-600 to-purple-600 dark:from-slate-100 dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
                CodeInspect Analysis
              </h1>
              <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <Sparkles className="w-4 h-4" />
                <span>AI-powered code inspection and debugging</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm rounded-lg p-1 border border-slate-200/50 dark:border-slate-700/50">
            <Button
              variant={viewMode === "integrated" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("integrated")}
              className={viewMode === "integrated" ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white" : "text-xs"}
            >
              <Eye className="w-3 h-3 mr-1" />
              Integrated
            </Button>
            <Button
              variant={viewMode === "tabbed" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("tabbed")}
              className={viewMode === "tabbed" ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white" : "text-xs"}
            >
              <Code2 className="w-3 h-3 mr-1" />
              Tabbed
            </Button>
          </div>

          <Button 
            onClick={() => setCurrentProject(null)}
            variant="outline"
            className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 dark:hover:from-blue-900/20 dark:hover:to-purple-900/20"
          >
            <Upload className="w-4 h-4 mr-2" />
            New Analysis
          </Button>
        </div>
      </div>

      {viewMode === "integrated" ? (
        <IntegratedAnalysisView
          project={currentProject}
          selectedFile={selectedFile}
          selectedIssue={selectedIssue}
          onFileSelect={handleFileSelect}
          onIssueSelect={handleIssueSelect}
        />
      ) : (
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50">
            <TabsTrigger value="overview" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 data-[state=active]:text-white">Overview</TabsTrigger>
            <TabsTrigger value="issues" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 data-[state=active]:text-white">Issues</TabsTrigger>
            <TabsTrigger value="code" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 data-[state=active]:text-white">Code Viewer</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <ProjectOverview project={currentProject} />
          </TabsContent>

          <TabsContent value="issues">
            <IssuesDashboard 
              issues={currentProject.issues} 
              onFileSelect={handleFileSelect}
              onIssueSelect={handleIssueSelect}
            />
          </TabsContent>

          <TabsContent value="code">
            <CodeViewer 
              project={currentProject} 
              selectedFile={selectedFile}
              issues={currentProject.issues}
              selectedIssue={selectedIssue}
            />
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}