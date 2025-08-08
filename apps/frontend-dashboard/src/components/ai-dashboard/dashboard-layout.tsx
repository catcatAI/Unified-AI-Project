'use client'

import React, { useState } from 'react'
import { Sidebar } from './sidebar'
import { DashboardOverview } from './tabs/dashboard-overview'
import { AIChat } from './tabs/ai-chat'
import { ImageGeneration } from './tabs/image-generation'
import { WebSearch } from './tabs/web-search'
import { CodeAnalysis } from './tabs/code-analysis'
import { AIAgents } from './tabs/ai-agents'
import { NeuralNetwork } from './tabs/neural-network'
import { GithubConnect } from './tabs/github-connect'
import { SystemMonitor } from './tabs/system-monitor'
import { Settings } from './tabs/settings'
import AtlassianIntegration from './tabs/atlassian-integration'

export function DashboardLayout() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardOverview />
      case 'chat':
        return <AIChat />
      case 'image':
        return <ImageGeneration />
      case 'search':
        return <WebSearch />
      case 'code':
        return <CodeAnalysis />
      case 'agents':
        return <AIAgents />
      case 'neural':
        return <NeuralNetwork />
      case 'github':
        return <GithubConnect />
      case 'monitor':
        return <SystemMonitor />
      case 'settings':
        return <Settings />
      case 'atlassian':
        return <AtlassianIntegration />
      default:
        return <DashboardOverview />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-auto">
        <div className="container mx-auto p-6">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}