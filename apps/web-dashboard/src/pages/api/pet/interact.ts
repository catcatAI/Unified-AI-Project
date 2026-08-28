import type { NextApiRequest, NextApiResponse } from 'next'
import { petState } from '../pet'

type Data = {
  happiness: number
  hunger: number
  energy: number
  health: number
}

const ACTION_EFFECTS: Record<string, { happiness?: number; hunger?: number; energy?: number; health?: number }> = {
  pet:  { happiness:  0.1, energy: -0.05 },
  feed: { hunger: -0.2, happiness: 0.05 },
  play: { happiness: 0.15, energy: -0.15, hunger: 0.05 },
  rest: { energy: 0.3, happiness: -0.05 },
}

function clamp(v: number): number {
  return Math.max(0, Math.min(1, v))
}

export default function handler(req: NextApiRequest, res: NextApiResponse<Data>) {
  if (req.method !== 'POST') {
    return res.status(405).json({ happiness: 0, hunger: 0, energy: 0, health: 0 })
  }

  const { action } = req.body || {}
  const effects = ACTION_EFFECTS[action]

  if (effects) {
    if (effects.happiness !== undefined) petState.happiness = clamp(petState.happiness + effects.happiness)
    if (effects.hunger !== undefined) petState.hunger = clamp(petState.hunger + effects.hunger)
    if (effects.energy !== undefined) petState.energy = clamp(petState.energy + effects.energy)
    if (effects.health !== undefined) petState.health = clamp(petState.health + effects.health)
  }

  res.status(200).json(petState)
}
