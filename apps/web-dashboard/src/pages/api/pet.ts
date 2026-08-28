import type { NextApiRequest, NextApiResponse } from 'next'

interface PetState {
  happiness: number
  hunger: number
  energy: number
  health: number
}

// In-memory state shared across API routes (resets on server restart)
const petState: PetState = {
  happiness: 0.5,
  hunger: 0.5,
  energy: 0.5,
  health: 1.0,
}

// Decay rates applied per fetch (passive hunger/energy drain)
let lastDecay = Date.now()

function applyDecay() {
  const now = Date.now()
  const elapsed = (now - lastDecay) / 1000
  if (elapsed > 30) {
    // Hunger increases over time (max 1.0)
    petState.hunger = Math.min(1, petState.hunger + elapsed * 0.001)
    // Energy decreases over time (min 0.0)
    petState.energy = Math.max(0, petState.energy - elapsed * 0.0005)
    lastDecay = now
  }
}

export { petState }

export default function handler(req: NextApiRequest, res: NextApiResponse<PetState>) {
  applyDecay()
  res.status(200).json(petState)
}
