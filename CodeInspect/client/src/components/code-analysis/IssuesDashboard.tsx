import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertTriangle, XCircle, AlertCircle, Info, Search, Filter, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface IssuesDashboardProps {
  issues: any[]
  onFileSelect: (file: any) => void
  onIssueSelect: (issue: any) => void
}

export function IssuesDashboard({ issues, onFileSelect, onIssueSelect }: IssuesDashboardProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [severityFilter, setSeverityFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState("all")

  console.log("IssuesDashboard rendered with", issues.length, "issues")

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "info":
        return <Info className="w-4 h-4 text-blue-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />
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

  const filteredIssues = issues.filter(issue => {
    const matchesSearch = issue.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         issue.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         issue.file.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = severityFilter === "all" || issue.severity === severityFilter
    const matchesCategory = categoryFilter === "all" || issue.category === categoryFilter
    
    return matchesSearch && matchesSeverity && matchesCategory
  })

  const criticalCount = issues.filter(i => i.severity === "critical").length
  const warningCount = issues.filter(i => i.severity === "warning").length
  const infoCount = issues.filter(i => i.severity === "info").length

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800 cursor-pointer hover:shadow-lg transition-all duration-200"
              onClick={() => setSeverityFilter("critical")}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-700 dark:text-red-300">Critical Issues</p>
                <p className="text-3xl font-bold text-red-900 dark:text-red-100">{criticalCount}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200 dark:border-yellow-800 cursor-pointer hover:shadow-lg transition-all duration-200"
              onClick={() => setSeverityFilter("warning")}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-700 dark:text-yellow-300">Warnings</p>
                <p className="text-3xl font-bold text-yellow-900 dark:text-yellow-100">{warningCount}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800 cursor-pointer hover:shadow-lg transition-all duration-200"
              onClick={() => setSeverityFilter("info")}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-700 dark:text-blue-300">Info</p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">{infoCount}</p>
              </div>
              <Info className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filter Issues
          </CardTitle>
          <CardDescription>
            Search and filter issues by severity, category, or keywords
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search issues..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white/50 dark:bg-slate-800/50"
              />
            </div>
            
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-full md:w-40 bg-white/50 dark:bg-slate-800/50">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="info">Info</SelectItem>
              </SelectContent>
            </Select>

            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full md:w-40 bg-white/50 dark:bg-slate-800/50">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="security">Security</SelectItem>
                <SelectItem value="performance">Performance</SelectItem>
                <SelectItem value="style">Code Style</SelectItem>
                <SelectItem value="bug">Potential Bug</SelectItem>
              </SelectContent>
            </Select>

            {(searchTerm || severityFilter !== "all" || categoryFilter !== "all") && (
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm("")
                  setSeverityFilter("all")
                  setCategoryFilter("all")
                }}
                className="bg-white/50 dark:bg-slate-800/50"
              >
                Clear Filters
              </Button>
            )}
          </div>

          <div className="text-sm text-muted-foreground">
            Showing {filteredIssues.length} of {issues.length} issues
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {filteredIssues.map((issue) => (
          <Card
            key={issue._id}
            className={cn(
              "border-l-4 cursor-pointer hover:shadow-md transition-all duration-200 bg-white/70 dark:bg-slate-900/70 backdrop-blur-sm",
              getSeverityColor(issue.severity)
            )}
            onClick={() => handleIssueClick(issue)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    {getSeverityIcon(issue.severity)}
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                      {issue.title}
                    </h3>
                    <Badge variant="outline" className="text-xs">
                      {issue.category}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {issue.description}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {issue.file}
                    </span>
                    <span>Line {issue.line}</span>
                  </div>
                </div>
                
                <ChevronRight className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredIssues.length === 0 && (
        <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
              No Issues Found
            </h3>
            <p className="text-slate-600 dark:text-slate-400">
              {searchTerm || severityFilter !== "all" || categoryFilter !== "all"
                ? "Try adjusting your filters to see more results."
                : "Great job! No issues were detected in your code."}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}