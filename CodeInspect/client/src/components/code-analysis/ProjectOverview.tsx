import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { FileText, Code, Package, AlertTriangle, CheckCircle, XCircle } from "lucide-react"

interface ProjectOverviewProps {
  project: any
}

export function ProjectOverview({ project }: ProjectOverviewProps) {
  console.log("ProjectOverview rendered with project:", project?.name)

  const getComplexityColor = (score: number) => {
    if (score >= 80) return "text-red-500"
    if (score >= 60) return "text-yellow-500"
    return "text-green-500"
  }

  const getComplexityLabel = (score: number) => {
    if (score >= 80) return "High"
    if (score >= 60) return "Medium"
    return "Low"
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Files</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{project.fileCount}</div>
            <p className="text-xs text-muted-foreground">
              {project.totalSize} total size
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Issues Found</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{project.totalIssues}</div>
            <div className="flex gap-2 mt-2">
              <Badge variant="destructive" className="text-xs">
                {project.criticalIssues} Critical
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {project.warningIssues} Warnings
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Complexity Score</CardTitle>
            <Code className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getComplexityColor(project.complexityScore)}`}>
              {project.complexityScore}/100
            </div>
            <p className="text-xs text-muted-foreground">
              {getComplexityLabel(project.complexityScore)} complexity
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5" />
              Language Breakdown
            </CardTitle>
            <CardDescription>
              Distribution of programming languages in your project
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {project.languages.map((lang: any) => (
              <div key={lang.name} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{lang.name}</span>
                  <span className="text-muted-foreground">{lang.percentage}%</span>
                </div>
                <Progress value={lang.percentage} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="w-5 h-5" />
              Dependencies
            </CardTitle>
            <CardDescription>
              Key dependencies and their versions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {project.dependencies.slice(0, 5).map((dep: any) => (
              <div key={dep.name} className="flex items-center justify-between">
                <span className="text-sm font-medium">{dep.name}</span>
                <Badge variant="outline" className="text-xs">
                  {dep.version}
                </Badge>
              </div>
            ))}
            {project.dependencies.length > 5 && (
              <p className="text-xs text-muted-foreground">
                +{project.dependencies.length - 5} more dependencies
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Entry Points
          </CardTitle>
          <CardDescription>
            Main entry points detected in your project
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {project.entryPoints.map((entry: any) => (
              <div key={entry.path} className="flex items-center gap-2 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-mono truncate">{entry.path}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}