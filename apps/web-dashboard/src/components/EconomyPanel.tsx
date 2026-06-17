import { useState, useEffect } from 'react'

interface Transaction {
  id: string
  type: 'earn' | 'spend'
  amount: number
  description: string
  timestamp: number
}

interface EconomyState {
  balance: number
  totalEarned: number
  totalSpent: number
  transactions: Transaction[]
}

export default function EconomyPanel() {
  const [economy, setEconomy] = useState<EconomyState>({
    balance: 0,
    totalEarned: 0,
    totalSpent: 0,
    transactions: []
  })

  useEffect(() => {
    const fetchEconomy = async () => {
      try {
        const res = await fetch('/api/economy')
        if (res.ok) {
          const data = await res.json()
          setEconomy(data)
        }
      } catch (err) {
        console.error('Failed to fetch economy:', err)
      }
    }
    
    fetchEconomy()
    const interval = setInterval(fetchEconomy, 5000)
    return () => clearInterval(interval)
  }, [])

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  return (
    <div className="economy-panel">
      <h2>Economy</h2>
      <div className="balance-section">
        <div className="balance">
          <h3>Balance</h3>
          <div className="value">{economy.balance.toFixed(2)}</div>
        </div>
        <div className="stats">
          <div>Earned: {economy.totalEarned.toFixed(2)}</div>
          <div>Spent: {economy.totalSpent.toFixed(2)}</div>
        </div>
      </div>
      <div className="transactions">
        <h3>Recent Transactions</h3>
        <div className="transaction-list">
          {economy.transactions.slice(0, 10).map(tx => (
            <div key={tx.id} className={`transaction ${tx.type}`}>
              <span className="type">{tx.type === 'earn' ? '+' : '-'}</span>
              <span className="amount">{tx.amount.toFixed(2)}</span>
              <span className="description">{tx.description}</span>
              <span className="timestamp">{formatDate(tx.timestamp)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
