import { useState } from 'react'
import Head from 'next/head'
import ChatPanel from '../components/ChatPanel'
import PetPanel from '../components/PetPanel'
import SystemMonitor from '../components/SystemMonitor'
import MemoryViewer from '../components/MemoryViewer'
import HealthIndicator from '../components/HealthIndicator'
import ConfigPanel from '../components/ConfigPanel'
import ModelSelector from '../components/ModelSelector'
import ContextViewer from '../components/ContextViewer'

const TABS = [
  { id: 'chat', label: '💬 Chat' },
  { id: 'config', label: '⚙️ Config' },
  { id: 'models', label: '🤖 Models' },
  { id: 'context', label: '🧠 Context' },
  { id: 'memory', label: '💾 Memory' },
  { id: 'system', label: '📊 System' },
  { id: 'pet', label: '🐕 Pet' },
]

export default function Home() {
  const [tab, setTab] = useState('chat')

  return (
    <>
      <Head>
        <title>Angela AI Dashboard</title>
        <meta name="description" content="Angela AI Web Dashboard" />
      </Head>
      <main className="dashboard">
        <header className="dashboard-header">
          <h1>Angela AI</h1>
          <HealthIndicator />
        </header>

        <nav className="tab-nav">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab-btn ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="panel-container">
          {tab === 'chat' && <ChatPanel />}
          {tab === 'config' && <ConfigPanel />}
          {tab === 'models' && <ModelSelector />}
          {tab === 'context' && <ContextViewer />}
          {tab === 'memory' && <MemoryViewer />}
          {tab === 'system' && <SystemMonitor />}
          {tab === 'pet' && <PetPanel />}
        </div>
      </main>
    </>
  )
}
