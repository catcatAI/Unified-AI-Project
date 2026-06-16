import Head from 'next/head'
import ChatPanel from '../components/ChatPanel'
import PetPanel from '../components/PetPanel'
import SystemMonitor from '../components/SystemMonitor'

export default function Home() {
  return (
    <>
      <Head>
        <title>Angela AI Dashboard</title>
        <meta name="description" content="Angela AI Web Dashboard" />
      </Head>
      <main className="dashboard">
        <h1>Angela AI Dashboard</h1>
        <div className="panels">
          <ChatPanel />
          <PetPanel />
          <SystemMonitor />
        </div>
      </main>
    </>
  )
}
