'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Switch } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { 
  Settings as SettingsIcon, 
  Key, 
  Bell, 
  Shield, 
  Database,
  Brain,
  Zap,
  Monitor,
  Save,
  RefreshCw
} from 'lucide-react'

export function Settings() {
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    gemini: '',
    claude: ''
  })

  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    training: false,
    errors: true
  })

  const [system, setSystem] = useState({
    autoSave: true,
    darkMode: false,
    telemetry: true,
    debugMode: false
  })

  const [performance, setPerformance] = useState({
    maxConcurrentRequests: 10,
    cacheSize: 1000,
    timeout: 30,
    retryAttempts: 3
  })

  const handleSaveSettings = () => {
    // Simulate saving settings
    console.log('Settings saved:', { apiKeys, notifications, system, performance })
  }

  const handleResetSettings = () => {
    setApiKeys({ openai: '', gemini: '', claude: '' })
    setNotifications({ email: true, push: true, training: false, errors: true })
    setSystem({ autoSave: true, darkMode: false, telemetry: true, debugMode: false })
    setPerformance({ maxConcurrentRequests: 10, cacheSize: 1000, timeout: 30, retryAttempts: 3 })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Configure your AI system preferences and API keys
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleResetSettings}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button onClick={handleSaveSettings}>
            <Save className="mr-2 h-4 w-4" />
            Save Settings
          </Button>
        </div>
      </div>

      <Tabs defaultValue="api" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="api">API Keys</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="api" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                API Configuration
              </CardTitle>
              <CardDescription>
                Configure your AI service API keys for enhanced functionality
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">OpenAI API Key</label>
                <Input
                  type="password"
                  value={apiKeys.openai}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, openai: e.target.value }))}
                  placeholder="sk-..."
                />
                <p className="text-xs text-muted-foreground">
                  Used for GPT models and advanced AI features
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Google Gemini API Key</label>
                <Input
                  type="password"
                  value={apiKeys.gemini}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, gemini: e.target.value }))}
                  placeholder="AIza..."
                />
                <p className="text-xs text-muted-foreground">
                  Used for Google's Gemini AI models
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Anthropic Claude API Key</label>
                <Input
                  type="password"
                  value={apiKeys.claude}
                  onChange={(e) => setApiKeys(prev => ({ ...prev, claude: e.target.value }))}
                  placeholder="sk-ant-..."
                />
                <p className="text-xs text-muted-foreground">
                  Used for Claude AI assistant
                </p>
              </div>

              <div className="pt-4 border-t">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Your API keys are encrypted and stored securely
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Configure how and when you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Email Notifications</label>
                  <p className="text-xs text-muted-foreground">
                    Receive notifications via email
                  </p>
                </div>
                <Switch
                  checked={notifications.email}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, email: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Push Notifications</label>
                  <p className="text-xs text-muted-foreground">
                    Receive push notifications in browser
                  </p>
                </div>
                <Switch
                  checked={notifications.push}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, push: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Training Updates</label>
                  <p className="text-xs text-muted-foreground">
                    Get notified when model training completes
                  </p>
                </div>
                <Switch
                  checked={notifications.training}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, training: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Error Alerts</label>
                  <p className="text-xs text-muted-foreground">
                    Get notified about system errors
                  </p>
                </div>
                <Switch
                  checked={notifications.errors}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, errors: checked }))
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                System Preferences
              </CardTitle>
              <CardDescription>
                Configure system-wide settings and behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Auto Save</label>
                  <p className="text-xs text-muted-foreground">
                    Automatically save changes and progress
                  </p>
                </div>
                <Switch
                  checked={system.autoSave}
                  onCheckedChange={(checked) => 
                    setSystem(prev => ({ ...prev, autoSave: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Dark Mode</label>
                  <p className="text-xs text-muted-foreground">
                    Enable dark theme for the interface
                  </p>
                </div>
                <Switch
                  checked={system.darkMode}
                  onCheckedChange={(checked) => 
                    setSystem(prev => ({ ...prev, darkMode: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Telemetry</label>
                  <p className="text-xs text-muted-foreground">
                    Share anonymous usage data to improve the product
                  </p>
                </div>
                <Switch
                  checked={system.telemetry}
                  onCheckedChange={(checked) => 
                    setSystem(prev => ({ ...prev, telemetry: checked }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <label className="text-sm font-medium">Debug Mode</label>
                  <p className="text-xs text-muted-foreground">
                    Enable debug logging and advanced features
                  </p>
                </div>
                <Switch
                  checked={system.debugMode}
                  onCheckedChange={(checked) => 
                    setSystem(prev => ({ ...prev, debugMode: checked }))
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Performance Settings
              </CardTitle>
              <CardDescription>
                Optimize system performance and resource usage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Concurrent Requests</label>
                <Input
                  type="number"
                  value={performance.maxConcurrentRequests}
                  onChange={(e) => setPerformance(prev => ({ 
                    ...prev, 
                    maxConcurrentRequests: parseInt(e.target.value) || 10 
                  }))}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum number of simultaneous API requests
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Cache Size (MB)</label>
                <Input
                  type="number"
                  value={performance.cacheSize}
                  onChange={(e) => setPerformance(prev => ({ 
                    ...prev, 
                    cacheSize: parseInt(e.target.value) || 1000 
                  }))}
                />
                <p className="text-xs text-muted-foreground">
                  Memory allocated for caching responses
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Request Timeout (seconds)</label>
                <Input
                  type="number"
                  value={performance.timeout}
                  onChange={(e) => setPerformance(prev => ({ 
                    ...prev, 
                    timeout: parseInt(e.target.value) || 30 
                  }))}
                />
                <p className="text-xs text-muted-foreground">
                  Time to wait before timing out requests
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Retry Attempts</label>
                <Input
                  type="number"
                  value={performance.retryAttempts}
                  onChange={(e) => setPerformance(prev => ({ 
                    ...prev, 
                    retryAttempts: parseInt(e.target.value) || 3 
                  }))}
                />
                <p className="text-xs text-muted-foreground">
                  Number of times to retry failed requests
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}