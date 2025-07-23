import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { History, Search, Trash2, Eye, Download, Calendar, FileText } from "lucide-react"
import { getProjectHistory, deleteProject } from "@/api/codeAnalysis"
import { useToast } from "@/hooks/useToast"
import { formatDistanceToNow } from "date-fns"

export function ProjectHistory() {
  const [projects, setProjects] = useState([])
  const [searchTerm, setSearchTerm] = useState("")
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  console.log("ProjectHistory component rendered")

  useEffect(() => {
    loadProjectHistory()
  }, [])

  const loadProjectHistory = async () => {
    try {
      setLoading(true)
      const history = await getProjectHistory()
      setProjects(history.projects)
    } catch (error) {
      console.error("Failed to load project history:", error)
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    try {
      await deleteProject(projectId)
      setProjects(projects.filter(p => p._id !== projectId))
      toast({
        title: "Project Deleted",
        description: "Project has been successfully deleted.",
      })
    } catch (error) {
      console.error("Failed to delete project:", error)
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      })
    }
  }

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high": return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
      case "medium": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"
      case "low": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
            Project History
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            View and manage your previously analyzed projects
          </p>
        </div>
      </div>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Search Projects
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by project name or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white/50 dark:bg-slate-800/50"
            />
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
              <CardContent className="p-6">
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
                  <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
                  <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-slate-500 to-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <History className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
              {searchTerm ? "No Projects Found" : "No Project History"}
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              {searchTerm 
                ? "Try adjusting your search terms to find projects."
                : "Start by analyzing your first project to see it appear here."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <Card key={project._id} className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg transition-all duration-200">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <FileText className="w-5 h-5" />
                      {project.name}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {project.description || "No description available"}
                    </CardDescription>
                  </div>
                  <Badge className={getSeverityColor(project.riskLevel)}>
                    {project.riskLevel}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Issues:</span>
                    <div className="font-medium">{project.totalIssues}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Files:</span>
                    <div className="font-medium">{project.fileCount}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>
                    Analyzed {formatDistanceToNow(new Date(project.analyzedAt), { addSuffix: true })}
                  </span>
                </div>

                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    <Eye className="w-4 h-4 mr-2" />
                    View
                  </Button>
                  <Button size="sm" variant="outline">
                    <Download className="w-4 h-4" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => handleDeleteProject(project._id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}