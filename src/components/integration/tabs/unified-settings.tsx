'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Settings, 
  User, 
  Bell,
  Shield,
  Database,
  Palette,
  Globe,
  Save,
  RefreshCw
} from 'lucide-react'

interface ServiceConfig {
  name: string
  url: string
  status: 'connected' | 'disconnected' | 'error'
  lastChecked: string
}

const mockServices: ServiceConfig[] = [
  {
    name: 'Unified-AI-Project',
    url: 'http://localhost:8000',
    status: 'connected',
    lastChecked: '2 分鐘前'
  },
  {
    name: 'GitHub Connect',
    url: 'http://localhost:5173',
    status: 'connected',
    lastChecked: '1 分鐘前'
  },
  {
    name: 'AI Dashboard',
    url: 'http://localhost:3000',
    status: 'connected',
    lastChecked: '剛剛'
  }
]

export function UnifiedSettings() {
  const [services] = useState<ServiceConfig[]>(mockServices)
  const [userSettings, setUserSettings] = useState({
    name: '用戶名',
    email: 'user@example.com',
    language: 'zh-TW',
    theme: 'system',
    notifications: true
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50'
      case 'disconnected': return 'text-gray-600 bg-gray-50'
      case 'error': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected': return '已連接'
      case 'disconnected': return '未連接'
      case 'error': return '連接錯誤'
      default: return '未知'
    }
  }

  const handleSaveSettings = () => {
    // 實現保存設置邏輯
    console.log('保存設置:', userSettings)
  }

  const handleTestConnection = (serviceName: string) => {
    // 實現測試連接邏輯
    console.log('測試連接:', serviceName)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">設置</h1>
          <p className="text-muted-foreground">
            系統配置與偏好設置
          </p>
        </div>
        
        <Button onClick={handleSaveSettings}>
          <Save className="h-4 w-4 mr-2" />
          保存設置
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* User Settings */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                用戶設置
              </CardTitle>
              <CardDescription>
                個人信息和偏好設置
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">用戶名</label>
                <Input
                  value={userSettings.name}
                  onChange={(e) => setUserSettings(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="輸入用戶名"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">郵箱</label>
                <Input
                  value={userSettings.email}
                  onChange={(e) => setUserSettings(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="輸入郵箱地址"
                  type="email"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">語言</label>
                <Select value={userSettings.language} onValueChange={(value) => setUserSettings(prev => ({ ...prev, language: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="zh-TW">繁體中文</SelectItem>
                    <SelectItem value="zh-CN">简体中文</SelectItem>
                    <SelectItem value="en-US">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">主題</label>
                <Select value={userSettings.theme} onValueChange={(value) => setUserSettings(prev => ({ ...prev, theme: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="system">系統默認</SelectItem>
                    <SelectItem value="light">淺色主題</SelectItem>
                    <SelectItem value="dark">深色主題</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                通知設置
              </CardTitle>
              <CardDescription>
                管理通知和提醒
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">啟用通知</div>
                  <div className="text-sm text-muted-foreground">接收系統通知</div>
                </div>
                <Button
                  variant={userSettings.notifications ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setUserSettings(prev => ({ ...prev, notifications: !prev.notifications }))}
                >
                  {userSettings.notifications ? '已啟用' : '已禁用'}
                </Button>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">通知方式</label>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" defaultChecked />
                    <span className="text-sm">瀏覽器通知</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" defaultChecked />
                    <span className="text-sm">郵件通知</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input type="checkbox" />
                    <span className="text-sm">短信通知</span>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System Settings */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                服務配置
              </CardTitle>
              <CardDescription>
                管理外部服務連接
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {services.map((service) => (
                <div key={service.name} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="font-medium">{service.name}</div>
                      <div className="text-sm text-muted-foreground">{service.url}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={getStatusColor(service.status)}>
                        {getStatusText(service.status)}
                      </Badge>
                      <Button variant="outline" size="sm" onClick={() => handleTestConnection(service.name)}>
                        <RefreshCw className="h-3 w-3 mr-1" />
                        測試
                      </Button>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    最後檢查: {service.lastChecked}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                安全設置
              </CardTitle>
              <CardDescription>
                管理安全選項和權限
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">API 密鑰</label>
                <Input
                  type="password"
                  placeholder="輸入API密鑰"
                  defaultValue="••••••••••••••••"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">會話超時</label>
                <Select defaultValue="30">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="15">15 分鐘</SelectItem>
                    <SelectItem value="30">30 分鐘</SelectItem>
                    <SelectItem value="60">1 小時</SelectItem>
                    <SelectItem value="120">2 小時</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">權限級別</label>
                <Select defaultValue="user">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">管理員</SelectItem>
                    <SelectItem value="user">用戶</SelectItem>
                    <SelectItem value="guest">訪客</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                界面設置
              </CardTitle>
              <CardDescription>
                自定義界面外觀
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">主題顏色</label>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="w-8 h-8 p-0 bg-blue-500"></Button>
                  <Button variant="outline" size="sm" className="w-8 h-8 p-0 bg-green-500"></Button>
                  <Button variant="outline" size="sm" className="w-8 h-8 p-0 bg-purple-500"></Button>
                  <Button variant="outline" size="sm" className="w-8 h-8 p-0 bg-orange-500"></Button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">字體大小</label>
                <Select defaultValue="medium">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">小</SelectItem>
                    <SelectItem value="medium">中</SelectItem>
                    <SelectItem value="large">大</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}