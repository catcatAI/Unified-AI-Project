import type { NextApiRequest, NextApiResponse } from 'next'

type Data = {
  happiness: number
  hunger: number
  energy: number
  health: number
}

export default function handler(req: NextApiRequest, res: NextApiResponse<Data>) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      happiness: 0,
      hunger: 0,
      energy: 0,
      health: 0
    })
  }

  const { action } = req.body
  
  const newState = {
    happiness: Math.min(1, 0.5 + (action === 'pet' ? 0.1 : 0)),
    hunger: Math.max(0, 0.5 - (action === 'feed' ? 0.2 : 0)),
    energy: Math.min(1, 0.5 + (action === 'rest' ? 0.3 : 0)),
    health: 1.0
  }

  res.status(200).json(newState)
}
