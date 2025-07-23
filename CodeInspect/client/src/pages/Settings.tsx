import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Settings as SettingsIcon, Bell, Code, Shield, Zap } from "lucide-react"
import { useToast } from "@/hooks/useToast"

export function Settings() {
  const [settings, setSettings] = useState({
    notifications: {
      analysisComplete: true,
      criticalIssues: true,
      weeklyReports: false,
    },
    analysis: {
      enableSecurity: true,
      enablePerformance: true,
      enableStyle: true,
      enableBugs: true,
      severityThreshold: [60],
    },
    languages: {
      javascript: true,
      typescript: true,
      python: true,
      java: false,
      cpp: false,
    },
  })

  const { toast } = useToast()

  console.log("Settings component rendered")

  const handleSaveSettings = () => {
    console.log("Saving settings:", settings)
    toast({
      title: "Settings Saved",
      description: "Your preferences have been updated successfully.",
    })
  }

  const updateSetting = (category: string, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
          Settings
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Configure your code analysis preferences and notifications
        </p>
      </div>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </CardTitle>
          <CardDescription>
            Choose when you want to receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="analysis-complete">Analysis Complete</Label>
              <p className="text-sm text-muted-foreground">
                Get notified when project analysis is finished
              </p>
            </div>
            <Switch
              id="analysis-complete"
              checked={settings.notifications.analysisComplete}
              onCheckedChange={(checked) => updateSetting('notifications', 'analysisComplete', checked)}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="critical-issues">Critical Issues</Label>
              <p className="text-sm text-muted-foreground">
                Immediate alerts for critical security or bug issues
              </p>
            </div>
            <Switch
              id="critical-issues"
              checked={settings.notifications.criticalIssues}
              onCheckedChange={(checked) => updateSetting('notifications', 'criticalIssues', checked)}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="weekly-reports">Weekly Reports</Label>
              <p className="text-sm text-muted-foreground">
                Receive weekly summaries of your project analyses
              </p>
            </div>
            <Switch
              id="weekly-reports"
              checked={settings.notifications.weeklyReports}
              onCheckedChange={(checked) => updateSetting('notifications', 'weeklyReports', checked)}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="w-5 h-5" />
            Analysis Preferences
          </CardTitle>
          <CardDescription>
            Configure which types of issues to detect and analyze
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="security-analysis">Security Analysis</Label>
                <p className="text-sm text-muted-foreground">
                  Detect security vulnerabilities and risks
                </p>
              </div>
              <Switch
                id="security-analysis"
                checked={settings.analysis.enableSecurity}
                onCheckedChange={(checked) => updateSetting('analysis', 'enableSecurity', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="performance-analysis">Performance Analysis</Label>
                <p className="text-sm text-muted-foreground">
                  Identify performance bottlenecks
                </p>
              </div>
              <Switch
                id="performance-analysis"
                checked={settings.analysis.enablePerformance}
                onCheckedChange={(checked) => updateSetting('analysis', 'enablePerformance', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="style-analysis">Code Style</Label>
                <p className="text-sm text-muted-foreground">
                  Check code formatting and style
                </p>
              </div>
              <Switch
                id="style-analysis"
                checked={settings.analysis.enableStyle}
                onCheckedChange={(checked) => updateSetting('analysis', 'enableStyle', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="bug-analysis">Bug Detection</Label>
                <p className="text-sm text-muted-foreground">
                  Find potential bugs and errors
                </p>
              </div>
              <Switch
                id="bug-analysis"
                checked={settings.analysis.enableBugs}
                onCheckedChange={(checked) => updateSetting('analysis', 'enableBugs', checked)}
              />
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <Label>Severity Threshold</Label>
            <p className="text-sm text-muted-foreground">
              Only show issues above this severity level ({settings.analysis.severityThreshold[0]}%)
            </p>
            <Slider
              value={settings.analysis.severityThreshold}
              onValueChange={(value) => updateSetting('analysis', 'severityThreshold', value)}
              max={100}
              min={0}
              step={10}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>All Issues</span>
              <span>Critical Only</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Language Support
          </CardTitle>
          <CardDescription>
            Enable or disable analysis for specific programming languages
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(settings.languages).map(([language, enabled]) => (
              <div key={language} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <Label htmlFor={language} className="capitalize font-medium">
                  {language === 'cpp' ? 'C++' : language}
                </Label>
                <Switch
                  id={language}
                  checked={enabled}
                  onCheckedChange={(checked) => updateSetting('languages', language, checked)}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button 
          onClick={handleSaveSettings}
          className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
        >
          <SettingsIcon className="w-4 h-4 mr-2" />
          Save Settings
        </Button>
      </div>
    </div>
  )
}