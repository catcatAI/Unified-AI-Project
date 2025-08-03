'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  MessageSquare, 
  Image, 
  Search, 
  Code, 
  Activity, 
  Settings,
  Home,
  Bot,
  Brain,
  Zap,
  Github,
  Monitor
} from 'lucide-react'

interface SidebarProps {
  className?: string
  activeTab: string
  onTabChange: (tab: string) => void
}

const sidebarItems = [
  {
    title: 'Dashboard',
    icon: Home,
    tab: 'dashboard',
    description: 'AI System Overview'
  },
  {
    title: 'AI Chat',
    icon: MessageSquare,
    tab: 'chat',
    description: 'Conversational AI Interface'
  },
  {
    title: 'Image Generation',
    icon: Image,
    tab: 'image',
    description: 'Create AI-generated images'
  },
  {
    title: 'Web Search',
    icon: Search,
    tab: 'search',
    description: 'AI-powered web search'
  },
  {
    title: 'Code Analysis',
    icon: Code,
    tab: 'code',
    description: 'Analyze and generate code'
  },
  {
    title: 'AI Agents',
    icon: Bot,
    tab: 'agents',
    description: 'Agent management and status'
  },
  {
    title: 'Neural Network',
    icon: Brain,
    tab: 'neural',
    description: 'Neural network operations'
  },
  {
    title: 'GitHub Connect',
    icon: Github,
    tab: 'github',
    description: 'GitHub integration and automation'
  },
  {
    title: 'System Monitor',
    icon: Monitor,
    tab: 'monitor',
    description: 'Real-time system monitoring'
  },
  {
    title: 'Settings',
    icon: Settings,
    tab: 'settings',
    description: 'System configuration'
  }
]

export function Sidebar({ className, activeTab, onTabChange }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div className={cn(
      'border-r bg-gray-50/40 transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64',
      className
    )}>
      <div className="flex h-full flex-col">
        <div className="flex h-14 items-center border-b px-4">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-primary" />
              <span className="font-semibold">AI Unified</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-8 w-8 p-0"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            <span className="sr-only">Toggle sidebar</span>
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </Button>
        </div>
        
        <ScrollArea className="flex-1 px-2 py-4">
          <div className="space-y-1">
            {sidebarItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.tab
              
              return (
                <Button
                  key={item.tab}
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    'w-full justify-start',
                    isCollapsed && 'justify-center px-2',
                    isActive && 'bg-secondary'
                  )}
                  onClick={() => onTabChange(item.tab)}
                  title={isCollapsed ? item.title : undefined}
                >
                  <Icon className={cn(
                    'h-4 w-4',
                    !isCollapsed && 'mr-2'
                  )} />
                  {!isCollapsed && (
                    <div className="flex flex-col items-start">
                      <span className="text-sm font-medium">{item.title}</span>
                      <span className="text-xs text-muted-foreground">
                        {item.description}
                      </span>
                    </div>
                  )}
                </Button>
              )
            })}
          </div>
        </ScrollArea>
        
        {!isCollapsed && (
          <div className="border-t p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4" />
              <span>System Online</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}