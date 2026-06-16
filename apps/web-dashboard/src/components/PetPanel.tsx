import { useState, useEffect } from 'react'

interface PetState {
  happiness: number
  hunger: number
  energy: number
  health: number
}

export default function PetPanel() {
  const [petState, setPetState] = useState<PetState>({
    happiness: 0.5,
    hunger: 0.5,
    energy: 0.5,
    health: 1.0
  })

  useEffect(() => {
    const fetchPetState = async () => {
      try {
        const res = await fetch('/api/pet')
        if (res.ok) {
          const data = await res.json()
          setPetState(data)
        }
      } catch (err) {
        console.error('Failed to fetch pet state:', err)
      }
    }
    
    fetchPetState()
    const interval = setInterval(fetchPetState, 5000)
    return () => clearInterval(interval)
  }, [])

  const interact = async (action: string) => {
    try {
      const res = await fetch('/api/pet/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      })
      if (res.ok) {
        const data = await res.json()
        setPetState(data)
      }
    } catch (err) {
      console.error('Failed to interact:', err)
    }
  }

  return (
    <div className="pet-panel">
      <h2>Pet</h2>
      <div className="pet-status">
        <div>😊 Happiness: {(petState.happiness * 100).toFixed(0)}%</div>
        <div>🍽️ Hunger: {(petState.hunger * 100).toFixed(0)}%</div>
        <div>⚡ Energy: {(petState.energy * 100).toFixed(0)}%</div>
        <div>❤️ Health: {(petState.health * 100).toFixed(0)}%</div>
      </div>
      <div className="pet-actions">
        <button onClick={() => interact('pet')}>Pet</button>
        <button onClick={() => interact('feed')}>Feed</button>
        <button onClick={() => interact('play')}>Play</button>
        <button onClick={() => interact('rest')}>Rest</button>
      </div>
    </div>
  )
}
