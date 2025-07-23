import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Loader2, X, Brain, Sparkles } from "lucide-react"

interface AnalysisProgressProps {
  progress: number
  onCancel?: () => void
}

export function AnalysisProgress({ progress, onCancel }: AnalysisProgressProps) {
  const getStatusMessage = () => {
    if (progress < 20) return "Scanning files and structure..."
    if (progress < 40) return "Analyzing dependencies and imports..."
    if (progress < 60) return "Detecting issues and vulnerabilities..."
    if (progress < 80) return "Running AI-powered analysis..."
    if (progress < 100) return "Generating intelligent insights..."
    return "Analysis complete!"
  }

  console.log("Analysis progress:", progress)

  return (
    <div className="max-w-2xl mx-auto mt-20">
      <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50 shadow-2xl">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4 relative">
            <Brain className="w-8 h-8 text-white" />
            <div className="absolute -top-1 -right-1">
              <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
            </div>
            <Loader2 className="w-12 h-12 text-white/30 animate-spin absolute" />
          </div>
          <CardTitle className="text-2xl bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
            CodeInspect AI Analysis
          </CardTitle>
          <CardDescription>
            Please wait while our AI analyzes your code and provides intelligent insights
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600 dark:text-slate-400 flex items-center gap-2">
                <Sparkles className="w-3 h-3" />
                {getStatusMessage()}
              </span>
              <span className="font-medium bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                {progress}%
              </span>
            </div>
            <Progress value={progress} className="h-3" />
          </div>

          <div className="text-center text-sm text-slate-500 dark:text-slate-400 flex items-center justify-center gap-2">
            <Brain className="w-4 h-4" />
            <span>Estimated time remaining: {Math.max(0, Math.ceil((100 - progress) / 20))} minutes</span>
          </div>

          {onCancel && (
            <div className="text-center">
              <Button variant="outline" onClick={onCancel} className="text-red-600 hover:text-red-700 border-red-200 hover:border-red-300">
                <X className="w-4 h-4 mr-2" />
                Cancel Analysis
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}