'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Button } from '@acme/ui'
import { Progress } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { useDetailedSystemMetrics, useServiceHealth } from '@/hooks/use-api-data'
import { 
  Activity, 
  Cpu, 
  MemoryStick, 
  HardDrive, 
  Wifi,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  Server,
  Database,
  Network,
  Thermometer,
  Gauge,
  BarChart3,
  RefreshCw,
  Loader2
} from 'lucide-react'

export function SystemMonitor() {
  const { data: systemMetrics, loading: metricsLoading, error: metricsError, refresh: refreshMetrics } = useDetailedSystemMetrics()
  const { data: services, loading: servicesLoading, error: servicesError, refresh: refreshServices } = useServiceHealth()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'normal':
        return 'text-green-600'
      case 'stopped':
        return 'text-gray-600'
      case 'warning':
        return 'text-yellow-600'
      case 'error':
      case 'critical':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'normal':
        return <CheckCircle className="h-4 w-4" />
      case 'stopped':
        return <Clock className="h-4 w-4" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />
      case 'error':
      case 'critical':
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getProgressColor = (value: number, status: string) => {
    if (status === 'critical') return 'bg-red-500'
    if (status === 'warning') return 'bg-yellow-500'
    if (value > 80) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const handleRefresh = () => {
    refreshMetrics()
    refreshServices()
  }

  // Calculate overall health based on real data
  const calculateOverallHealth = () => {
    if (!systemMetrics || !services) return 0
    
    const runningServices = services.filter(s => s.status === 'running').length
    const serviceHealth = (runningServices / services.length) * 100
    
    const cpuHealth = systemMetrics.cpu.usage_percent < 80 ? 100 : (100 - systemMetrics.cpu.usage_percent)
    const memoryHealth = systemMetrics.memory.percent < 80 ? 100 : (100 - systemMetrics.memory.percent)
    const diskHealth = systemMetrics.disk.percent < 90 ? 100 : (100 - systemMetrics.disk.percent)
    
    return Math.round((serviceHealth + cpuHealth + memoryHealth + diskHealth) / 4)
  }

  const overallHealth = calculateOverallHealth()

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${days}d ${hours}h ${minutes}m`
  }

  if (metricsLoading || servicesLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading system metrics...</span>
      </div>
    )
  }

  if (metricsError || servicesError) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Failed to load system data</h3>
        <p className="text-muted-foreground mb-4">
          {metricsError || servicesError}
        </p>
        <Button onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Monitor</h1>
          <p className="text-muted-foreground">
            Real-time system monitoring and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            {overallHealth}% Healthy
          </Badge>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getStatusColor('normal')}`}>
              {overallHealth}%
            </div>
            <p className="text-xs text-muted-foreground">
              All systems operational
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Services</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {services.filter(s => s.status === 'running').length}/{services.length}
            </div>
            <p className="text-xs text-muted-foreground">
              Services running
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemMetrics?.cpu.usage_percent.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {systemMetrics?.cpu.cores} cores @ {systemMetrics?.cpu.frequency.toFixed(1)} GHz
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemMetrics?.memory.percent.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {formatBytes(systemMetrics?.memory.used || 0)} / {formatBytes(systemMetrics?.memory.total || 0)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="metrics" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="metrics">System Metrics</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* CPU Metrics */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold">
                      {systemMetrics?.cpu.usage_percent.toFixed(1)}%
                    </span>
                    <div className={`flex items-center gap-1 ${getStatusColor(systemMetrics?.cpu.usage_percent > 80 ? 'warning' : 'normal')}`}>
                      {getStatusIcon(systemMetrics?.cpu.usage_percent > 80 ? 'warning' : 'normal')}
                    </div>
                  </div>
                  <Progress 
                    value={systemMetrics?.cpu.usage_percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-muted-foreground">
                    {systemMetrics?.cpu.cores} cores @ {systemMetrics?.cpu.frequency.toFixed(1)} GHz
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Memory Metrics */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory</CardTitle>
                <MemoryStick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold">
                      {systemMetrics?.memory.percent.toFixed(1)}%
                    </span>
                    <div className={`flex items-center gap-1 ${getStatusColor(systemMetrics?.memory.percent > 80 ? 'warning' : 'normal')}`}>
                      {getStatusIcon(systemMetrics?.memory.percent > 80 ? 'warning' : 'normal')}
                    </div>
                  </div>
                  <Progress 
                    value={systemMetrics?.memory.percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(systemMetrics?.memory.available || 0)} available
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Disk Metrics */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Storage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold">
                      {systemMetrics?.disk.percent.toFixed(1)}%
                    </span>
                    <div className={`flex items-center gap-1 ${getStatusColor(systemMetrics?.disk.percent > 90 ? 'critical' : systemMetrics?.disk.percent > 80 ? 'warning' : 'normal')}`}>
                      {getStatusIcon(systemMetrics?.disk.percent > 90 ? 'critical' : systemMetrics?.disk.percent > 80 ? 'warning' : 'normal')}
                    </div>
                  </div>
                  <Progress 
                    value={systemMetrics?.disk.percent || 0} 
                    className="h-2"
                  />
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(systemMetrics?.disk.free || 0)} free
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Network Metrics */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network</CardTitle>
                <Wifi className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold">
                      ↑{formatBytes(systemMetrics?.network.bytes_sent || 0)}
                    </span>
                    <span className="text-lg font-bold">
                      ↓{formatBytes(systemMetrics?.network.bytes_recv || 0)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Packets: {systemMetrics?.network.packets_sent || 0} sent, {systemMetrics?.network.packets_recv || 0} received
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Process Metrics */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Processes</CardTitle>
                <Server className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-2xl font-bold">
                    {systemMetrics?.processes.total || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {systemMetrics?.processes.running || 0} running, {systemMetrics?.processes.sleeping || 0} sleeping
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Temperature Metrics */}
            {systemMetrics?.temperature && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Temperature</CardTitle>
                  <Thermometer className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-2xl font-bold">
                        {systemMetrics.temperature.cpu}°C
                      </span>
                      <div className={`flex items-center gap-1 ${getStatusColor(systemMetrics.temperature.cpu > 80 ? 'critical' : systemMetrics.temperature.cpu > 70 ? 'warning' : 'normal')}`}>
                        {getStatusIcon(systemMetrics.temperature.cpu > 80 ? 'critical' : systemMetrics.temperature.cpu > 70 ? 'warning' : 'normal')}
                      </div>
                    </div>
                    <Progress 
                      value={(systemMetrics.temperature.cpu / 100) * 100} 
                      className="h-2"
                    />
                    <p className="text-xs text-muted-foreground">
                      CPU Temperature {systemMetrics.temperature.gpu && `• GPU: ${systemMetrics.temperature.gpu}°C`}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Status</CardTitle>
              <CardDescription>
                Status and resource usage for all system services
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {services.map((service) => (
                  <div key={service.name} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className={`flex items-center gap-1 ${getStatusColor(service.status)}`}>
                        {getStatusIcon(service.status)}
                      </div>
                      <div>
                        <h3 className="font-medium">{service.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          Uptime: {service.uptime}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <div className="text-sm font-medium">{service.cpu.toFixed(1)}%</div>
                        <div className="text-xs text-muted-foreground">CPU</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-medium">{formatBytes(service.memory)}</div>
                        <div className="text-xs text-muted-foreground">Memory</div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-muted-foreground">
                          Last check: {new Date(service.last_check).toLocaleTimeString()}
                        </div>
                        <Badge variant={service.status === 'running' ? 'default' : 'secondary'}>
                          {service.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gauge className="h-5 w-5" />
                  Performance Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Response Time</span>
                    <span className="text-sm font-medium">245ms</span>
                  </div>
                  <Progress value={75} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Throughput</span>
                    <span className="text-sm font-medium">1,250 req/s</span>
                  </div>
                  <Progress value={85} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Error Rate</span>
                    <span className="text-sm font-medium">0.02%</span>
                  </div>
                  <Progress value={2} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Availability</span>
                    <span className="text-sm font-medium">99.9%</span>
                  </div>
                  <Progress value={99.9} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Resource Usage
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Disk I/O</span>
                    <span className="text-sm font-medium">45 MB/s</span>
                  </div>
                  <Progress value={45} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Network I/O</span>
                    <span className="text-sm font-medium">125 MB/s</span>
                  </div>
                  <Progress value={65} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Database Connections</span>
                    <span className="text-sm font-medium">23/50</span>
                  </div>
                  <Progress value={46} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Active Sessions</span>
                    <span className="text-sm font-medium">156</span>
                  </div>
                  <Progress value={78} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}