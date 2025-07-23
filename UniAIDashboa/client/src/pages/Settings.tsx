import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  User,
  Key,
  Bell,
  Palette,
  DollarSign,
  BarChart3,
  Shield,
  Save,
  Eye,
  EyeOff
} from 'lucide-react'
import { useToast } from '@/hooks/useToast'
import { useAuth } from '@/contexts/AuthContext'

export function Settings() {
  const { user } = useAuth()
  const { toast } = useToast()

  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
    company: '',
    timezone: 'UTC'
  })

  const [apiKeys, setApiKeys] = useState([
    { service: 'OpenAI', key: 'sk-...', status: 'active', masked: true },
    { service: 'Anthropic', key: 'sk-ant-...', status: 'active', masked: true },
    { service: 'Google Cloud', key: '', status: 'inactive', masked: true },
  ])

  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    usage: true,
    billing: true,
    updates: false
  })

  const [preferences, setPreferences] = useState({
    theme: 'light',
    autoSave: true,
    defaultQuality: 'balanced',
    language: 'en'
  })

  const [budget, setBudget] = useState({
    monthly: 100,
    current: 74.23,
    alerts: true,
    threshold: 80
  })

  const handleSaveProfile = () => {
    console.log('Saving profile:', profile)
    toast({
      title: "Success",
      description: "Profile updated successfully",
    })
  }

  const handleSaveApiKey = (index: number, newKey: string) => {
    const updated = [...apiKeys]
    updated[index].key = newKey
    updated[index].status = newKey ? 'active' : 'inactive'
    setApiKeys(updated)
    console.log('API key updated:', updated[index])
    toast({
      title: "Success",
      description: "API key updated successfully",
    })
  }

  const toggleKeyVisibility = (index: number) => {
    const updated = [...apiKeys]
    updated[index].masked = !updated[index].masked
    setApiKeys(updated)
  }

  const handleSaveNotifications = () => {
    console.log('Saving notifications:', notifications)
    toast({
      title: "Success",
      description: "Notification preferences updated",
    })
  }

  const handleSavePreferences = () => {
    console.log('Saving preferences:', preferences)
    toast({
      title: "Success",
      description: "Preferences updated successfully",
    })
  }

  const handleSaveBudget = () => {
    console.log('Saving budget:', budget)
    toast({
      title: "Success",
      description: "Budget settings updated",
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Settings
        </h1>
        <p className="text-muted-foreground mt-1">Manage your account and application preferences</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Keys
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Preferences
          </TabsTrigger>
          <TabsTrigger value="billing" className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Billing
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Profile Information
              </CardTitle>
              <CardDescription>
                Update your personal information and account details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={profile.name}
                    onChange={(e) => setProfile({...profile, name: e.target.value})}
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({...profile, email: e.target.value})}
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={profile.company}
                    onChange={(e) => setProfile({...profile, company: e.target.value})}
                    placeholder="Optional"
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={profile.timezone} onValueChange={(value) => setProfile({...profile, timezone: value})}>
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="EST">Eastern Time</SelectItem>
                      <SelectItem value="PST">Pacific Time</SelectItem>
                      <SelectItem value="GMT">Greenwich Mean Time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button onClick={handleSaveProfile} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                <Save className="h-4 w-4 mr-2" />
                Save Profile
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                API Keys
              </CardTitle>
              <CardDescription>
                Manage your API keys for different AI services
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {apiKeys.map((apiKey, index) => (
                <div key={apiKey.service} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="font-medium">{apiKey.service}</div>
                      <Badge variant={apiKey.status === 'active' ? 'default' : 'secondary'} className="text-xs">
                        {apiKey.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Input
                      type={apiKey.masked ? 'password' : 'text'}
                      value={apiKey.key}
                      onChange={(e) => handleSaveApiKey(index, e.target.value)}
                      placeholder="Enter API key"
                      className="w-64"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleKeyVisibility(index)}
                    >
                      {apiKey.masked ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Choose how you want to be notified about important events
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                  </div>
                  <Switch
                    checked={notifications.email}
                    onCheckedChange={(checked) => setNotifications({...notifications, email: checked})}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive browser push notifications</p>
                  </div>
                  <Switch
                    checked={notifications.push}
                    onCheckedChange={(checked) => setNotifications({...notifications, push: checked})}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Usage Alerts</Label>
                    <p className="text-sm text-muted-foreground">Get notified about API usage limits</p>
                  </div>
                  <Switch
                    checked={notifications.usage}
                    onCheckedChange={(checked) => setNotifications({...notifications, usage: checked})}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Billing Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive billing and payment updates</p>
                  </div>
                  <Switch
                    checked={notifications.billing}
                    onCheckedChange={(checked) => setNotifications({...notifications, billing: checked})}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Product Updates</Label>
                    <p className="text-sm text-muted-foreground">Get notified about new features</p>
                  </div>
                  <Switch
                    checked={notifications.updates}
                    onCheckedChange={(checked) => setNotifications({...notifications, updates: checked})}
                  />
                </div>
              </div>
              <Button onClick={handleSaveNotifications} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                <Save className="h-4 w-4 mr-2" />
                Save Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Application Preferences
              </CardTitle>
              <CardDescription>
                Customize your application experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Theme</Label>
                  <Select value={preferences.theme} onValueChange={(value) => setPreferences({...preferences, theme: value})}>
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="dark">Dark</SelectItem>
                      <SelectItem value="system">System</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Language</Label>
                  <Select value={preferences.language} onValueChange={(value) => setPreferences({...preferences, language: value})}>
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Default Quality</Label>
                  <Select value={preferences.defaultQuality} onValueChange={(value) => setPreferences({...preferences, defaultQuality: value})}>
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fast">Fast</SelectItem>
                      <SelectItem value="balanced">Balanced</SelectItem>
                      <SelectItem value="quality">High Quality</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-save Work</Label>
                  <p className="text-sm text-muted-foreground">Automatically save your work in progress</p>
                </div>
                <Switch
                  checked={preferences.autoSave}
                  onCheckedChange={(checked) => setPreferences({...preferences, autoSave: checked})}
                />
              </div>
              <Button onClick={handleSavePreferences} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                <Save className="h-4 w-4 mr-2" />
                Save Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="billing" className="space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Billing & Usage
              </CardTitle>
              <CardDescription>
                Monitor your usage and manage billing settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Current Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">${budget.current}</div>
                    <p className="text-xs text-muted-foreground">this month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Monthly Budget</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">${budget.monthly}</div>
                    <p className="text-xs text-muted-foreground">limit set</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Remaining</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">${(budget.monthly - budget.current).toFixed(2)}</div>
                    <p className="text-xs text-muted-foreground">available</p>
                  </CardContent>
                </Card>
              </div>

              <div>
                <Label>Usage Progress</Label>
                <div className="mt-2">
                  <Progress value={(budget.current / budget.monthly) * 100} className="w-full" />
                  <div className="flex justify-between text-sm text-muted-foreground mt-1">
                    <span>${budget.current} used</span>
                    <span>{((budget.current / budget.monthly) * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="monthlyBudget">Monthly Budget ($)</Label>
                  <Input
                    id="monthlyBudget"
                    type="number"
                    value={budget.monthly}
                    onChange={(e) => setBudget({...budget, monthly: parseFloat(e.target.value)})}
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="threshold">Alert Threshold (%)</Label>
                  <Input
                    id="threshold"
                    type="number"
                    value={budget.threshold}
                    onChange={(e) => setBudget({...budget, threshold: parseFloat(e.target.value)})}
                    className="mt-2"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Budget Alerts</Label>
                    <p className="text-sm text-muted-foreground">Get notified when approaching budget limit</p>
                  </div>
                  <Switch
                    checked={budget.alerts}
                    onCheckedChange={(checked) => setBudget({...budget, alerts: checked})}
                  />
                </div>
              </div>

              <Button onClick={handleSaveBudget} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                <Save className="h-4 w-4 mr-2" />
                Save Budget Settings
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}